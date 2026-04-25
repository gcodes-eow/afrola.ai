from django.db import models

class PricingPlan(models.Model):
    name = models.CharField(max_length=50)
    slug = models.SlugField(unique=True)
    price_monthly = models.DecimalField(max_digits=10, decimal_places=2)
    max_minutes_per_month = models.IntegerField()
    features = models.JSONField(default=list)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    
    def __str__(self):
        return f"{self.name} - ${self.price_monthly}/month"
