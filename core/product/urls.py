from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProductViewSet, CategoryViewSet, FavoriteViewSet, MyListingsViewSet

router = DefaultRouter()
router.register(r'products', ProductViewSet, basename='product')  # Ensure correct name is given
router.register(r'categories', CategoryViewSet, basename='categories')
router.register(r'favorites', FavoriteViewSet, basename='favorite')
router.register(r'my-listings', MyListingsViewSet, basename='my-listings')

urlpatterns = [
    path('', include(router.urls)),
]
