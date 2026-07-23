from django.shortcuts import render, redirect, reverse, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext_lazy as _
from allauth.account.models import EmailAddress
from django.contrib import messages
import datetime
from django.utils.timezone import make_aware
from .models import *
from django.conf import settings
from dateutil.relativedelta import relativedelta
import stripe

stripe.api_key = settings.STRIPE_SECRET_KEY

def subscription_view(request):
    price_id = 'price_1To2juHHl6ggmM31iCOSFRPO'
    
    try:
        stripe_price = stripe.Price.retrieve(price_id, expand=['product'])
        product = stripe_price.product
        
        subscription_data = {
            'price_id': stripe_price.id,
            'name': product.name,
            'description': product.description,
            'images': product.images,
            'price_formatted': f"€{stripe_price.unit_amount / 100.0:.2f}",
        }
    except Exception as e:
        print(f"Error retrieving data from Stripe: {e}")
        subscription_data = {
            'price_id': price_id,
            'name': "Reunite Hope",
            'description': "Bring your missing items home faster.",
            'images': [],
            'price_formatted': "€3.99",
        }

    if request.method == 'POST':
        if not request.user.is_authenticated:
            return redirect(f'{settings.BASE_URL}{reverse("account_login")}?next={request.get_full_path()}')

        is_verified = EmailAddress.objects.filter(
            user=request.user, 
            email=request.user.email, 
            verified=True
        ).exists()

        if not is_verified:
            messages.error(
                request, 
                _("To subscribe, you must confirm your email address.")
            )
            return redirect('subscription')
        
        selected_price_id = request.POST.get('price_id')

        checkout_session = stripe.checkout.Session.create(
            line_items=[
                {
                    'price': selected_price_id,
                    'quantity': 1,
                }
            ],
            payment_method_types=['card'],
            mode='subscription',
            success_url=request.build_absolute_uri(reverse("create_subscription")) + f'?session_id={{CHECKOUT_SESSION_ID}}',
            cancel_url=request.build_absolute_uri(reverse("subscription")),
            customer_email=request.user.email,
            metadata={
                'user_id': request.user.id,
            }
        )
        return redirect(checkout_session.url, code=303)

    return render(request, 'subscription/subscription.html', {'subscription': subscription_data})


def create_subscription(request):
    if request.user.has_premium:
        messages.info(request, "You already have an active subscription.")
        return redirect('my_sub')
        
    checkout_session_id = request.GET.get("session_id", None)

    if checkout_session_id:
        try:
            session = stripe.checkout.Session.retrieve(checkout_session_id)

            user_id = session.metadata.user_id
            user = User.objects.get(id=user_id)

            stripe_sub = stripe.Subscription.retrieve(session.subscription)

            first_item = stripe_sub.items.data[0]
            price = first_item.price

            product = stripe.Product.retrieve(price.product)

            Subscription.objects.create(
                user=user,
                customer_id=session.customer,
                subscription_id=session.subscription,
                product_name=product.name,
                price=price.unit_amount / 100,
                interval=price.recurring.interval,
            )

        except Exception as e:
            print(f"Error creating subscription in database: {e}")

    return redirect("my_sub")


import datetime
from django.utils.timezone import make_aware

@login_required
def my_sub_view(request):
    local_sub = Subscription.objects.filter(user=request.user).order_by('-id').first()
    stripe_data = None

    if local_sub:
        try:
            stripe_sub = stripe.Subscription.retrieve(
                local_sub.subscription_id, expand=["plan.product"]
            )

            plan = stripe_sub.plan
            product = plan.product

            status = getattr(stripe_sub, 'status', 'inactive')
            cancel_at_period_end = getattr(stripe_sub, 'cancel_at_period_end', False)
            start_date_timestamp = getattr(stripe_sub, 'start_date', None)

            is_active = status in ["active", "trialing"]
            
            is_cancelled = cancel_at_period_end

            if is_active and not is_cancelled:
                if local_sub.canceled_at or local_sub.end_date:
                    local_sub.canceled_at = None
                    local_sub.end_date = None
                    local_sub.save()

            next_charge_date = None
            if start_date_timestamp:
                period_start = datetime.datetime.fromtimestamp(start_date_timestamp)
                interval = getattr(plan, 'interval', 'month')
                interval_count = getattr(plan, 'interval_count', 1)
                
                if interval == 'month':
                    next_charge_date = make_aware(period_start + relativedelta(months=interval_count))
                elif interval == 'year':
                    next_charge_date = make_aware(period_start + relativedelta(years=interval_count))
                elif interval == 'week':
                    next_charge_date = make_aware(period_start + datetime.timedelta(weeks=interval_count))
                else:
                    next_charge_date = make_aware(period_start + datetime.timedelta(days=interval_count))

            image_url = None
            images_list = getattr(product, 'images', None)
            if images_list and isinstance(images_list, list) and len(images_list) > 0:
                image_url = images_list[0]

            description = getattr(product, 'description', "Premium plan active.")
            if not description:
                description = "Premium plan active."

            stripe_data = {
                "subscription_id": local_sub.subscription_id,
                "product_name": getattr(product, 'name', 'Premium Plan'),
                "description": description,
                "image": image_url,
                "price_formatted": f"€{plan.amount / 100.0:.2f}",
                "interval": getattr(plan, 'interval', 'month'),
                "start_date": local_sub.start_date,
                "next_charge_date": next_charge_date,
                "is_active": is_active,
                "is_cancelled": is_cancelled,
            }
            
        except Exception as e:
            print(f"!!! CRITICAL STRIPE ERROR: {e}")
            
            is_local_cancelled = local_sub.canceled_at is not None or local_sub.end_date is not None
            try:
                local_price = float(local_sub.price)
                price_formatted = f"€{local_price:.2f}"
            except (ValueError, TypeError):
                price_formatted = f"€{local_sub.price}"

            stripe_data = {
                "subscription_id": local_sub.subscription_id,
                "product_name": getattr(local_sub, 'product_name', 'Premium Plan'),
                "description": "Premium features activated (Offline mode).",
                "image": None,
                "price_formatted": price_formatted,
                "interval": getattr(local_sub, 'interval', 'month'),
                "start_date": local_sub.start_date,
                "next_charge_date": local_sub.end_date,
                "is_active": not is_local_cancelled,
                "is_cancelled": is_local_cancelled,
            }

    return render(
        request, "subscription/my-sub.html", {"subscription": stripe_data}
    )


def cancel_subscription(request, subscription_id):
    subscription = get_object_or_404(Subscription, user=request.user, subscription_id=subscription_id)

    stripe.Subscription.modify(
        subscription_id,
        cancel_at_period_end=True
    )

    subscription.canceled_at = now()
    
    stripe_subscription = stripe.Subscription.retrieve(subscription_id)
    
    canceled_on_timestamp = getattr(stripe_subscription, 'canceled_on', None)
    
    if canceled_on_timestamp:
        subscription.end_date = make_aware(
            datetime.datetime.fromtimestamp(canceled_on_timestamp)
        )
    else:
        start_date_timestamp = getattr(stripe_subscription, 'start_date', None)
        if start_date_timestamp:
            period_start = datetime.datetime.fromtimestamp(start_date_timestamp)
            subscription.end_date = make_aware(period_start + datetime.timedelta(days=30))

    subscription.save()

    return redirect('my_sub')