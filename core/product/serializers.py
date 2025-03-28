from rest_framework import serializers
from .models import Product, Favorite, Category, City
from decimal import Decimal, ROUND_DOWN
from django.conf import settings
import logging
logger = logging.getLogger(__name__)


class FavoriteSerializer(serializers.ModelSerializer):
    product_id = serializers.IntegerField(write_only=True, required=True)  # Ensure it's required and defined properly

    class Meta:
        model = Favorite
        fields = ['id', 'user', 'product', 'product_id', 'created_at']
        extra_kwargs = {'user': {'read_only': True}}

    def create(self, validated_data):
        user = self.context['request'].user
        product_id = validated_data.get('product_id')  # Extract product_id properly

        logger.debug(f"Product ID: {product_id}")  # Log product_id

        if not product_id:
            raise serializers.ValidationError("Product ID is required.")

        # Ensure the Product instance exists
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            logger.error(f"Product {product_id} does not exist.")
            raise serializers.ValidationError("Product does not exist.")

        # Prevent duplicate favorites
        if Favorite.objects.filter(user=user, product=product).exists():
            raise serializers.ValidationError("You have already favorited this product.")

        return Favorite.objects.create(user=user, product=product)


class CategorySerializer(serializers.ModelSerializer):
    icon_url = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()
    subcategories = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = [
            "id", "name", "parent", "icon", "icon_url", 
            "image", "image_url", "created_at", "subcategories"
        ]

    def get_icon_url(self, obj):
        """Return absolute URL for icon image"""
        request = self.context.get("request")
        if obj.icon and request is not None:
            return request.build_absolute_uri(obj.icon.url)
        return None

    def get_image_url(self, obj):
        """Return absolute URL for image"""
        request = self.context.get("request")
        if obj.image and request is not None:
            return request.build_absolute_uri(obj.image.url)
        return None

    def get_subcategories(self, obj):
        """Fetch all subcategories under this category"""
        return CategorySerializer(obj.subcategories.all(), many=True).data

    def validate_icon(self, value):
        """Validate icon file format"""
        if value:
            allowed_extensions = [".png", ".jpg", ".jpeg"]
            if not any(value.name.lower().endswith(ext) for ext in allowed_extensions):
                raise serializers.ValidationError("Only PNG, JPG, and JPEG files are allowed.")
        return value

    def validate_image(self, value):
        """Validate image file format (same as icon)"""
        if value:
            allowed_extensions = [".png", ".jpg", ".jpeg"]
            if not any(value.name.lower().endswith(ext) for ext in allowed_extensions):
                raise serializers.ValidationError("Only PNG, JPG, and JPEG files are allowed.")
        return value



class CitySerializer(serializers.ModelSerializer):
    class Meta:
        model = City
        fields = ['id','name', 'region']

    
class ProductSerializer(serializers.ModelSerializer):
    
    seller_name = serializers.CharField(source='seller.first_name', read_only=True)  # Display seller name
    category = CategorySerializer(read_only=True)  # Nested category details
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), source='category', write_only=True
    )  # Allow setting category by ID
    city = CitySerializer(read_only=True)  # Show city details
    city_id = serializers.PrimaryKeyRelatedField(
        queryset=City.objects.all(), source='city', write_only=True
    )  # Allow selecting city by ID

    image_url = serializers.SerializerMethodField()  # Handle image URLs properly
    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)  # Formatted timestamp
    formatted_price = serializers.SerializerMethodField()  # Format price as "999.99 ETB"
    currency = serializers.CharField(write_only=True)  # Allow currency to be set during creation
    converted_price = serializers.SerializerMethodField()  # Convert price dynamically

    class Meta:
        model = Product
        fields = [
            'id', 'title', 'description', 'price', 'formatted_price', 'converted_price', 'currency',
            'category', 'category_id','city', 'city_id','seller_name', 'image', 'image_url', 'created_at'
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


