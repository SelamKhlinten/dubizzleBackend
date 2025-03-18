from .models import Product, Category
from .serializers import ProductSerializer, CategorySerializer
from rest_framework.filters import OrderingFilter, SearchFilter
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.pagination import PageNumberPagination
from rest_framework.viewsets import ModelViewSet
from django.core.cache import cache
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Favorite
from .serializers import FavoriteSerializer
from ..user.permissions import IsAdminOrOwner
from rest_framework import filters
import django_filters
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.exceptions import PermissionDenied
from rest_framework.authentication import SessionAuthentication, BasicAuthentication

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    # http_method_names = ['get', 'post', 'put', 'patch', 'delete']

    filter_backends = [OrderingFilter, DjangoFilterBackend, SearchFilter]
    filterset_fields = ['name']
    search_fields = ['name']
    ordering_fields = ['name']

    def get_serializer_context(self):
        return {"request": self.request}  # Ensures URLs are generated correctly

    def get_queryset(self):
        """
        Returns categories with caching and optional sorting.
        """
        if self.action in ["list", "retrieve"]:  # Only use caching for GET requests
            sort_by = self.request.query_params.get('sort_by', None)
            # categories = cache.get("categories")

            # if categories is None:  
            #     categories = list(Category.objects.all())  # Ensure list format
            #     cache.set("categories", categories, timeout=60 * 5)

            if sort_by:
                try:
                    categories = sorted(categories, key=lambda x: getattr(x, sort_by))
                except AttributeError:
                    return Category.objects.all()  # Fallback to DB query if sorting fails

            return Category.objects.filter(id__in=[c.id for c in categories])  # Return as queryset

        return Category.objects.all()  # Default queryset for non-list actions

    @action(detail=False, methods=['patch'], permission_classes=[IsAdminUser])
    def bulk_update(self, request):
        """
        Updates multiple categories at once.
        """
        ids = request.data.get('ids', [])
        name = request.data.get('name')

        if not ids or not name:
            return Response({"detail": "Please provide valid IDs and a name."}, status=status.HTTP_400_BAD_REQUEST)

        categories = Category.objects.filter(id__in=ids)
        if not categories.exists():
            return Response({"detail": "No matching categories found."}, status=status.HTTP_404_NOT_FOUND)

        categories.update(name=name)
        return Response({"detail": "Categories updated successfully."}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['delete'], permission_classes=[IsAdminUser])
    def bulk_delete(self, request):
        """
        Deletes multiple categories at once.
        """
        ids = request.data.get('ids', [])

        if not ids:
            return Response({"detail": "Please provide IDs to delete."}, status=status.HTTP_400_BAD_REQUEST)

        deleted_count, _ = Category.objects.filter(id__in=ids).delete()
        if deleted_count == 0:
            return Response({"detail": "No matching categories found."}, status=status.HTTP_404_NOT_FOUND)

        return Response({"detail": f"{deleted_count} categories deleted successfully."}, status=status.HTTP_200_OK)



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
