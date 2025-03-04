from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/user/', include('core.user.urls')), 
    path('api/product/', include('core.product.urls')),
    
]
