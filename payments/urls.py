from django.urls import path
from .views import *

urlpatterns = [
    # path('', product_view, name="product"),
    # path('payment_successful/', payment_successful, name='payment_successful'),
    # path('payment_cancelled', payment_cancelled, name='payment_cancelled'),
    path('stripe_webhook/', stripe_webhook, name='stripe_webhook'),
]