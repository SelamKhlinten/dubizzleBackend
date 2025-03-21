from django.contrib import admin
from .models import Category, City

class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'icon', 'image']

class CityAdmin(admin.ModelAdmin):
    list_display = ['name', 'region']  # Display city name and region in the admin panel
    search_fields = ['name', 'region']  # Allow searching by name or region

admin.site.register(Category, CategoryAdmin)
admin.site.register(City, CityAdmin)  # Register the City model
