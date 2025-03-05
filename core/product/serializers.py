from rest_framework import serializers
from .models import Product, Category, Favorite
from decimal import Decimal


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name']

class ProductSerializer(serializers.ModelSerializer):

    seller_name = serializers.CharField(source='seller.first_name', read_only=True)  # Display seller name
    category = CategorySerializer(read_only=True)  # Nested category details
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), source='category', write_only=True
    )  # Allow setting category by ID
    image_url = serializers.SerializerMethodField()  # Handle image URLs properly
    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)  # Formatted timestamp
    formatted_price = serializers.SerializerMethodField()  # Format price as "999.99 ETB"
    currency = serializers.CharField(read_only=True)  # Make currency read-only (since it’s in the model)
    converted_price = serializers.SerializerMethodField()  # Convert price dynamically

    class Meta:
        model = Product
        fields = [
            'id', 'title', 'description', 'price', 'formatted_price', 'converted_price', 'currency',
            'seller_name', 'category', 'category_id', 'image', 'image_url', 'created_at'
        ]

        # fields = "__all__"

        read_only_fields = ['seller_name', 'created_at', 'formatted_price', 'converted_price', 'currency']

    def get_image_url(self, obj):
        """Return the full image URL"""
        request = self.context.get('request')
        if obj.image and request is not None:
            return request.build_absolute_uri(obj.image.url)
        return None

    def create(self, validated_data):
        """Automatically set owner & seller before saving"""
        request = self.context.get('request')
        validated_data['owner'] = request.user  # Set owner automatically
        validated_data['seller'] = request.user  # Assuming seller is also owner
        return super().create(validated_data)
    
    def get_converted_price(self, obj):
        """Return a structured breakdown of the price, including conversion details."""
        request = self.context.get('request')
        target_currency = request.query_params.get('currency', obj.currency)
        
        original_price = Decimal(obj.price)
        converted_price = obj.convert_price(target_currency)

        return {
            "original_price": f"{original_price} {obj.currency}",
            "converted_price": f"{converted_price} {target_currency}",
            "exchange_rate": float(converted_price / original_price) if original_price else 1.0
        }

    def get_formatted_price(self, obj):
        """Return the original price in a structured format."""
        return {
            "amount": obj.price,
            "currency": obj.currency,
            "formatted": f"{obj.price} {obj.currency}"
        }


class FavoriteSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)  # Show full product details
    product_id = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all(), write_only=True)

    class Meta:
        model = Favorite
        fields = ['id', 'product', 'product_id', 'created_at']

    def create(self, validated_data):
        user = self.context['request'].user
        product = validated_data['product_id']

        # Check if favorite already exists
        favorite, created = Favorite.objects.get_or_create(user=user, product=product)
        return favorite