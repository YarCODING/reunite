import decimal
import stripe
from django.conf import settings
from django.urls import reverse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.core.mail import send_mail
from posts.models import Item
from ..models import Wallet, PayoutTransaction
from chats.models import ChatGroup
from django.conf import Settings

stripe.api_key = settings.STRIPE_SECRET_KEY

@login_required
def create_reward_payment_session(request, item_id):
    item = get_object_or_404(Item, id=item_id, user=request.user)
    
    if request.method == "POST":
        reward_amount_raw = request.POST.get('amount')
        try:
            total_reward = decimal.Decimal(str(reward_amount_raw))
            
            if total_reward < decimal.Decimal('1.00'):
                messages.error(request, "Minimum reward is €1.00.")
                return redirect('item-detail', item_id=item.id)
        except (ValueError, TypeError, decimal.InvalidOperation):
            messages.error(request, "Invalid amount entered.")
            return redirect('item-detail', item_id=item.id)

        wallet, _ = Wallet.objects.get_or_create(user=request.user)
        user_balance = wallet.balance

        if user_balance >= total_reward:
            wallet_deduction = total_reward
            stripe_charge = decimal.Decimal('0.00')
        else:
            wallet_deduction = user_balance
            stripe_charge = total_reward - user_balance

        if stripe_charge == decimal.Decimal('0.00'):
            wallet.balance -= wallet_deduction
            wallet.save()

            item.reward_amount = total_reward
            item.is_reward_paid = True
            item.save()

            messages.success(request, f"Successfully paid! €{wallet_deduction} was deducted from your wallet balance.")
            return redirect('/dashboard/?payment=success')

        amount_in_cents = int(stripe_charge * 100)

        success_path = reverse('dashboard') + '?payment=success'
        cancel_path = reverse('dashboard') + '?payment=cancel'

        checkout_session = stripe.checkout.Session.create(
            customer_email=request.user.email,
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'eur',
                    'product_data': {
                        'name': f'Reward Sub-payment for Item: {item.title}',
                        'description': f'Total reward: €{total_reward} (Paid via Wallet: €{wallet_deduction})',
                    },
                    'unit_amount': amount_in_cents,
                },
                'quantity': 1,
            }],
            mode='payment',
            metadata={
                'item_id': item.id,
                'total_reward': float(total_reward),
                'wallet_deduction': float(wallet_deduction),
                'type': 'reward_payment_with_wallet'
            },
            success_url = request.build_absolute_uri(success_path),
            cancel_url = request.build_absolute_uri(cancel_path),
        )
        return redirect(checkout_session.url, status=303)


@login_required
@require_http_methods(["POST"])
def confirm_reunite_view(request, chatroom_name):
    chat_group = get_object_or_404(ChatGroup, group_name=chatroom_name)
    item = chat_group.item
    
    if not item or item.user != request.user or item.status == 'reunited':
        return redirect('chats')
        
    finder_user = None
    for member in chat_group.members.all():
        if member != request.user:
            finder_user = member
            break
            
    if not finder_user:
        return redirect('chatroom', chatroom_name=chatroom_name)

    item.finder = finder_user
    item.status = 'reunited'
    item.save()
    
    chat_group.is_closed = True
    chat_group.save()
    
    if item.is_reward_paid and item.reward_amount > 0:
        commission_rate = 0.02 if finder_user.has_premium else 0.10
        
        reward_decimal = decimal.Decimal(str(item.reward_amount))
        service_fee = reward_decimal * decimal.Decimal(str(commission_rate))
        payout_amount = reward_decimal - service_fee
        
        finder_wallet, _ = Wallet.objects.get_or_create(user=finder_user)
        finder_wallet.balance += payout_amount
        finder_wallet.save()
        
        messages.success(request, f"Success! Item marked as reunited. €{payout_amount} has been added to {finder_user.username}'s wallet.")
    else:
        messages.success(request, "Success! Item marked as reunited.")
        
    return redirect('chatroom', chatroom_name=chatroom_name)


@login_required
def request_withdrawal_view(request):
    wallet, _ = Wallet.objects.get_or_create(user=request.user)

    if request.method == "POST":
        current_balance = wallet.balance
        if current_balance <= 0:
            messages.error(request, "Your balance is empty.")
            return redirect('wallet-page')

        transaction = PayoutTransaction.objects.create(
            user=request.user,
            amount=current_balance,
            status='pending'
        )

        wallet.balance = 0.00
        wallet.save()

        subject = f"NEW Payout Request #{transaction.id} from @{request.user.username}"
        message_body = f"User @{request.user.username} ({request.user.email}) requested a payout.\n\n" \
                       f"Total amount to pay out: {current_balance} EUR\n\n" \
                       f"Action needed:\n" \
                       f"1. Send money manually to the user via Card/PayPal.\n" \
                       f"2. Go to Django Admin and mark Payout #{transaction.id} as COMPLETED.\n\n" \
                       f"Link to admin panel: {settings.BASE_URL}/admin/"

        send_mail(
            subject=subject,
            message=message_body,
            from_email=None,
            recipient_list=[settings.ADMIN_RECIPIENT_EMAIL],
        )

        messages.success(request, f"Your request for {current_balance} EUR has been submitted! Admin will contact you soon.")
        return redirect('wallet-page')

    payout_history = request.user.payouts.all().order_by('-created_at')

    return render(request, 'posts/wallet.html', {'wallet': wallet, 'payout_history': payout_history})
