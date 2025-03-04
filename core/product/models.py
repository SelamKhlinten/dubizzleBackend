from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model
from decimal import Decimal
import requests
from core.utils.currency import fetch_live_exchange_rate

User = get_user_model()

class Category(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name

class Product(models.Model): 
    title = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(

        max_length=3,
        choices=[
            ('ETB', 'Ethiopian Birr'),
            ('USD', 'US Dollar'),
            ('AED', 'UAE Dirham')  
        ],
        default='ETB'
    )

    
    category = models.ForeignKey(
        'Category', on_delete=models.SET_NULL, null=True, blank=True, related_name="products"
    )
    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, related_name="products_sold"
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='products_owned'
    )
    
    status = models.CharField(
        max_length=10,
        choices=[('active', 'Active'), ('sold', 'Sold'), ('expired', 'Expired')],
        default='active'
    )
    image = models.ImageField(upload_to="product_images/", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    

    def convert_price(self, target_currency):
        """Convert price dynamically based on real-time exchange rates."""
        if self.currency == target_currency or not self.price:
            return self.price  # No conversion needed or price is None

        exchange_rate = fetch_live_exchange_rate(target_currency)
        if exchange_rate == Decimal("1.0") and target_currency != "ETB":
            print(f"Warning: Failed to fetch exchange rate for {target_currency}. Using fallback.")
            return self.price  # Return the original price if API fails

        return round(self.price * exchange_rate, 2)





    def __str__(self):
        seller_name = self.seller.first_name if self.seller else "Unknown"
        return f"{self.title} - {self.price} {self.currency} (Seller: {seller_name})"


class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='favorited_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product')  # Prevent duplicate favorites

    def __str__(self):
        return f"{self.user.username} favorited {self.product.name}"

