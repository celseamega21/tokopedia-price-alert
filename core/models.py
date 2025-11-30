from django.db import models
from django.contrib.auth import get_user_model
from scraper.models import ScraperEngine

User = get_user_model()

class Product(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='products')
    email = models.EmailField()
    name = models.CharField(max_length=500)
    url = models.URLField(max_length=700)
    engine = models.ForeignKey(ScraperEngine, on_delete=models.SET_NULL, related_name='products', null=True, blank=True)
    last_price = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
class PriceHistory(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    price = models.PositiveIntegerField()
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']
