from django.db import models
from django.contrib.auth.models import User
from django.utils.timezone import now

class Subscription(models.Model):
    user = models. ForeignKey(User, on_delete=models.CASCADE)
    customer_id = models.CharField(max_length=255)
    subscription_id = models.CharField(max_length=255, unique=True)
    product_name = models.CharField(max_length=255)
    price = models.IntegerField()
    interval = models.CharField(max_length=50, default="month")
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField(null=True, blank=True)
    canceled_at = models.DateTimeField(null=True, blank=True)

    @property
    def is_active(self):
        if self.end_date:
            if now() < self.end_date:
                return True
            else:
                return False 
        else:
            return True
        
    @property
    def tier(self):
        tier_mapping = {
            'Reunite Hope': 1,
        }
        tier = tier_mapping.get(self.product_name, None)
        return tier
    
    def __str__(self):
        return f"{self.user.username} - {self.product_name} - Active: {self.is_active}"
    

def user_has_premium(self):
    sub = Subscription.objects.filter(user=self).order_by('-id').first()
    return sub.is_active if sub else False

User.add_to_class('has_premium', property(user_has_premium))
