from django.db import models
from django.contrib.auth.models import User
from geopy.geocoders import Nominatim
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _
from pgvector.django import VectorField

class Item(models.Model):
    CATEGORY_CHOICES = [
        ('electronics', _('Electronics & Gadgets')),
        ('documents', _('IDs & Documents')),
        ('keys', _('Keys')),
        ('bags', _('Bags & Wallets')),
        ('clothing', _('Clothing & Accessories')),
        ('pets', _('Pets & Animals')),
        ('transport', _('Sport & Leisure')),
        ('kids', _('Kids & Baby')),
        ('other', _('Miscellaneous')),
    ]


    TYPE_CHOICES = [
        ('lost', _('Lost')),
        ('found', _('Found')),
    ]

    STATUS_CHOICES = [
        ('active', _('Active')),
        ('reunited', _('Reunited'))
    ]

    title = models.CharField(max_length=60)
    description = models.TextField(max_length=1000, blank=True)

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='items')

    image = models.ImageField(upload_to='items/', blank=True, null=True)

    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='other')
    type = models.CharField(max_length=10, choices=TYPE_CHOICES, default='lost')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')

    is_approved = models.BooleanField(
        default=False, 
        verbose_name="Approved by administrator",
        help_text="The listing will appear on the website only after approval."
    )

    is_priority = models.BooleanField(default=False)

    city = models.CharField(max_length=100)
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)

    reward_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    is_reward_paid = models.BooleanField(default=False)
    
    finder = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='found_items')

    embedding = VectorField(dimensions=1024, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if self.status == 'reunited':
            self.chats.update(is_closed=True)

        if self.city:
            is_new = self.pk is None
            old_city = None if is_new else Item.objects.get(pk=self.pk).city
            
            if is_new or old_city != self.city:
                try:
                    geolocator = Nominatim(user_agent="reunite_lost_and_found", timeout=10)
                    location = geolocator.geocode(self.city)
                    if location:
                        self.latitude = location.latitude
                        self.longitude = location.longitude
                except Exception as e:
                    print(f"Geocoding error: {e}")
            
        super().save(*args, **kwargs)

    def __str__(self):
        return f"[{self.get_type_display()}] {self.title} ({self.city})"
    

class Wallet(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='wallet')
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def __str__(self):
        return f"Wallet: {self.user.username} - Balance: €{self.balance}"

@receiver(post_save, sender=User)
def create_user_wallet(sender, instance, created, **kwargs):
    if created:
        Wallet.objects.create(user=instance)


class PayoutTransaction(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending (Waiting for Admin)'),
        ('completed', 'Completed (Paid)'),
        ('rejected', 'Rejected/Cancelled'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payouts')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Payout #{self.id} - {self.user.username} - {self.amount} EUR [{self.get_status_display()}]"