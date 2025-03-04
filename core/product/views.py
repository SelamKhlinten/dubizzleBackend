from .models import Product, Category
from .serializers import ProductSerializer, CategorySerializer
from rest_framework.filters import OrderingFilter, SearchFilter
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.pagination import PageNumberPagination
from rest_framework.viewsets import ModelViewSet
import django_filters
from django.core.cache import cache
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Favorite, Product
from .serializers import FavoriteSerializer
from ..user.permissions import IsAdminOrOwner


class FavoriteViewSet(viewsets.ModelViewSet):
    serializer_class = FavoriteSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Favorite.objects.filter(user=self.request.user)  #Only return user’s favorites

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        favorite = serializer.save()
        return Response(FavoriteSerializer(favorite).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['DELETE'])
    def remove(self, request, pk=None):
        """Custom endpoint to remove a product from favorites"""
        try:
            favorite = Favorite.objects.get(user=request.user, product_id=pk)
            favorite.delete()
            return Response({"message": "Removed from favorites"}, status=status.HTTP_204_NO_CONTENT)
        except Favorite.DoesNotExist:
            return Response({"error": "Product not in favorites"}, status=status.HTTP_400_BAD_REQUEST)


class IsOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.owner == request.user

class ProductFilter(django_filters.FilterSet):
    min_price = django_filters.NumberFilter(field_name="price", lookup_expr="gte")
    max_price = django_filters.NumberFilter(field_name="price", lookup_expr="lte")
    category = django_filters.CharFilter(field_name="category__name", lookup_expr="iexact")

    class Meta:
        model = Product
        fields = ['category', 'min_price', 'max_price']

class ProductPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

class ProductViewSet(ModelViewSet):
    
    queryset = Product.objects.select_related('category').prefetch_related('images').all()

    serializer_class = ProductSerializer
    permission_classes = [IsOwner | permissions.IsAuthenticated]
    pagination_class = ProductPagination
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_class = ProductFilter
    filterset_fields = ['category']
    ordering_fields = ['price', 'created_at']
    ordering = ['-created_at']
    search_fields = ['title', 'description']

    def get_serializer_context(self):
        return {"request": self.request}

    def get_queryset(self):
        products = cache.get("products")
        if not products:
            products = Product.objects.all()
            cache.set("products", products, timeout=60 * 5)  # Cache for 5 minutes
        return products
    
    def perform_create(self, serializer):
        if self.request.user.is_authenticated:
            serializer.save(seller=self.request.user, owner=self.request.user)
        else:
            raise serializer.ValidationError({"error": "Authentication required to create a product."})
        
class CategoryViewSet(ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated]


class MyListingsViewSet(viewsets.ModelViewSet):
    serializer_class = ProductSerializer
    permission_classes = [IsAdminOrOwner]

    def get_queryset(self):
        user = self.request.user
        if user.role == "admin":
            return Product.objects.all()
        if user.role == "vendor":
            return Product.objects.filter(seller=user)
        return Product.objects.none()
