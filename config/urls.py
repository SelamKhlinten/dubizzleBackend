from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

# @csrf_exempt
# def test_view(request):
#     return HttpResponse(f"Method: {request.method}")


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/user/', include('core.user.urls')), 
    path('api/product/', include('core.product.urls')),
    path('api/cart/', include('core.cart.urls')),
    path('api/chat/', include('core.chat.urls')),
    path('api/notification/', include('core.notification.urls')),
    # path('test/', test_view),

    
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)