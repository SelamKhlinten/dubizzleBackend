from django.contrib import admin
from .models import Category, City, Product

class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'icon', 'image']

class CityAdmin(admin.ModelAdmin):
    list_display = ['name', 'region']  # Display city name and region in the admin panel
    search_fields = ['name', 'region']  # Allow searching by name or region

class ProductAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'city', 'price', 'seller', 'created_at']
    search_fields = ['title', 'category__name', 'city__name', 'seller__username']
    list_filter = ['category', 'city', 'created_at']
    ordering = ['-created_at']

admin.site.register(Category, CategoryAdmin)
admin.site.register(City, CityAdmin)  # Register the City model
admin.site.register(Product, ProductAdmin)  # Register the Product model