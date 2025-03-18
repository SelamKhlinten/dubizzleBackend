from rest_framework import serializers
from .models import Product, Category, Favorite
from decimal import Decimal, ROUND_DOWN
from django.conf import settings

class CategorySerializer(serializers.ModelSerializer):
    icon_url = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = '__all__'

    def get_icon_url(self, obj):
        request = self.context.get('request')
        if obj.icon and request is not None:
            return request.build_absolute_uri(obj.icon.url)
        return None

    def get_image_url(self, obj):
        request = self.context.get('request')
        if obj.image and request is not None:
            return request.build_absolute_uri(obj.image.url)
        return None

    def validate_icon(self, value):
        allowed_extensions = [".png", ".jpg", ".jpeg"]
        if not any(value.name.endswith(ext) for ext in allowed_extensions):
            raise serializers.ValidationError("Only PNG, JPG, and JPEG files are allowed.")
        return value
    
class ProductSerializer(serializers.ModelSerializer):

    seller_name = serializers.CharField(source='seller.first_name', read_only=True)  # Display seller name
    category = CategorySerializer(read_only=True)  # Nested category details
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), source='category', write_only=True
    )  # Allow setting category by ID
    image_url = serializers.SerializerMethodField()  # Handle image URLs properly
    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)  # Formatted timestamp
    formatted_price = serializers.SerializerMethodField()  # Format price as "999.99 ETB"
    currency = serializers.CharField(write_only=True)  # Allow currency to be set during creation
    converted_price = serializers.SerializerMethodField()  # Convert price dynamically

    class Meta:
        model = Product
        fields = [
            'id', 'title', 'description', 'price', 'formatted_price', 'converted_price', 'currency',
            'seller_name', 'category', 'category_id', 'image', 'image_url', 'created_at'
        ]
        read_only_fields = ['seller_name', 'created_at', 'formatted_price', 'converted_price']

    def get_image_url(self, obj):
        """Return the full image URL"""
        request = self.context.get('request')
        if obj.image and request is not None:
            return request.build_absolute_uri(obj.image.url)
        return None

    def perform_create(self, serializer):
        """Automatically set owner & seller before saving, and handle currency"""
        if self.request.user.is_authenticated:
            # Get currency from the request or default to 'ETB'
            currency = self.request.data.get('currency', 'ETB')

            # Set currency in the validated data
            serializer.validated_data['currency'] = currency

            # Save the product with seller and owner set to the authenticated user
            serializer.save(seller=self.request.user, owner=self.request.user)
        else:
            raise serializers.ValidationError({"error": "Authentication required to create a product."})

    def create(self, validated_data):
        """Override create to handle the logic before saving"""
        request = self.context.get('request')
        validated_data['owner'] = request.user  # Set owner automatically
        validated_data['seller'] = request.user  # Assuming seller is also owner

        # Set the currency to 'ETB' by default if not provided
        currency = validated_data.get('currency', 'ETB')  # Default to 'ETB' if currency is not provided
        validated_data['currency'] = currency  # Set the currency field

        return super().create(validated_data)


    def get_converted_price(self, obj):
        """Return a structured breakdown of the price, including conversion details."""
        request = self.context.get('request')
        target_currency = request.query_params.get('currency', obj.currency)

        original_price = Decimal(obj.price)
        converted_price = obj.convert_price(target_currency)
        exchange_rate = Decimal(converted_price / original_price) if original_price else Decimal("1.0")

        return {
            "amount": float(converted_price.quantize(Decimal("0.01"), rounding=ROUND_DOWN)),
            "currency": target_currency,
            "exchange_rate": float(exchange_rate.quantize(Decimal("0.00001"), rounding=ROUND_DOWN))
        }

    def get_formatted_price(self, obj):
        """Return the original price in a structured format."""
        return {
            "amount": float(obj.price),
            "currency": obj.currency,
            "formatted": f"{float(obj.price):.2f} {obj.currency}"
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