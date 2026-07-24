from django.shortcuts import render, redirect, reverse
import decimal
import stripe
from django.conf import settings
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from .models import *
from posts.models import Wallet, Item

stripe.api_key = settings.STRIPE_SECRET_KEY

def product_view(request):
    product_id = 'prod_UnwObr8mAXRhmn'
    product = stripe.Product.retrieve(product_id)
    prices = stripe.Price.list(product=product_id)
    price = prices.data[0]
    product_price = price.unit_amount / 100.0

    if request.method == 'POST':
        if not request.user.is_authenticated:
            return redirect(f'{settings.BASE_URL}{reverse("account_login")}?next={request.get_full_path()}')
        
        price_id = request.POST.get('price_id')
        quantity = int(request.POST.get('quantity'))
        
        checkout_session = stripe.checkout.Session.create(
            line_items = [
                {
                    'price': price_id,
                    'quantity': quantity,
                }
            ],
            payment_method_types = ['card'],
            mode = 'payment',
            customer_creation = 'always',
            success_url = f'{settings.BASE_URL}{reverse("payment_successful")}?session_id={{CHECKOUT_SESSION_ID}}',
            cancel_url = f'{settings.BASE_URL}{reverse("payment_cancelled")}',
        )

        line_item = stripe.checkout.Session.list_line_items(checkout_session.id).data[0]

        UserPayment.objects.create(
            user = request.user,
            stripe_checkout_id = checkout_session.id,
            stripe_product_id = line_item.price.product,
            product_name = line_item.description,
            quantity = line_item.quantity,
            price = line_item.price.unit_amount / 100.0,
            currency = line_item.price.currency,
            has_paid = False
        )

        return redirect(checkout_session.url, code=303)

    return render(request, 'payments/product.html', {'product': product, 'product_price': product_price})


def payment_successful(request):
    checkout_session_id = request.GET.get('session_id', None)
    customer = None

    if checkout_session_id:
        try:
            session = stripe.checkout.Session.retrieve(checkout_session_id)
            customer_id = session.customer
            if customer_id:
                customer = stripe.Customer.retrieve(customer_id)
        except Exception as e:
            print(f"Error: {e}")

    return render(request, 'payments/payment_successful.html', {'customer': customer})


def payment_cancelled(request):
    return render(request, 'payments/payment_cancelled.html')


@require_POST
@csrf_exempt
def stripe_webhook(request):
    endpoint_secret = settings.STRIPE_WEBHOOK_SECRET
    payload = request.body
    
    signature_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    if not signature_header:
        return HttpResponse(status=400)

    try:
        event = stripe.Webhook.construct_event(
            payload, signature_header, endpoint_secret
        )
    except (ValueError, stripe.error.SignatureVerificationError):
        return HttpResponse(status=400)
    
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        checkout_session_id = session.id
        
        metadata = getattr(session, 'metadata', None)
        
        metadata_type = getattr(metadata, 'type', None) if metadata else None

        if metadata_type == 'reward_payment_with_wallet':
            item_id = getattr(metadata, 'item_id', None)
            total_reward_raw = getattr(metadata, 'total_reward', None)
            wallet_deduction_raw = getattr(metadata, 'wallet_deduction', None)
            
            try:
                item = Item.objects.get(id=item_id)
                
                total_reward = decimal.Decimal(str(float(total_reward_raw)))
                wallet_deduction = decimal.Decimal(str(float(wallet_deduction_raw)))
                
                owner_wallet, created = Wallet.objects.get_or_create(user=item.user)
                owner_wallet.balance -= wallet_deduction
                owner_wallet.save()
                
                item.reward_amount = total_reward
                item.is_reward_paid = True
                item.save()
                
                return HttpResponse(status=200)
                
            except Item.DoesNotExist:
                print(f"Webhook Error: Item with ID {item_id} not found.")
                return HttpResponse(status=200)
            except Exception as e:
                print(f"!!! CRITICAL WEBHOOK REWARD ERROR: {e}")
                return HttpResponse(status=500)

        else:
            try:
                user_payment = UserPayment.objects.get(stripe_checkout_id=checkout_session_id)
                user_payment.stripe_customer_id = session.customer
                user_payment.has_paid = True
                user_payment.save()
            except UserPayment.DoesNotExist:
                return HttpResponse(status=200)
            except Exception as e:
                print(f"!!! CRITICAL WEBHOOK USERPAYMENT ERROR: {e}")
                return HttpResponse(status=500)

    return HttpResponse(status=200)