from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProductViewSet, CategoryViewSet, FavoriteViewSet, MyListingsViewSet

router = DefaultRouter()
router.register(r'', ProductViewSet, basename='product')  
router.register(r'categories', CategoryViewSet, basename='category')

router.register('favorites', FavoriteViewSet, basename='favorite')
router.register('my-listings', MyListingsViewSet, basename='my-listings')


urlpatterns = [
    path('', include(router.urls)),
]
