from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CartViewSet

router = DefaultRouter()
router.register(r'', CartViewSet, basename='cart')  # Remove 'cart' to avoid duplication

urlpatterns = [
    path('', include(router.urls)),
]
