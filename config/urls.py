from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/user/', include('core.user.urls')), 
    path('api/product/', include('core.product.urls')),
    path('api/cart/', include('core.cart.urls')),
    path('api/chat/', include('core.chat.urls')),
    path('api/notification/', include('core.notification.urls')),

    
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)