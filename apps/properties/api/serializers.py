from rest_framework import serializers
from decimal import Decimal
from apps.properties.models import (
    Property, PropertyCategory, PropertyType, PropertyImage,
    PropertyAmenity, PropertyRule, PropertyFavorite
)

class PropertyCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertyCategory
        fields = ['id', 'name', 'slug']


class PropertyTypeSerializer(serializers.ModelSerializer):
    category = PropertyCategorySerializer(read_only=True)

    class Meta:
        model = PropertyType
        fields = ['id', 'name', 'slug', 'category']


class PropertyImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertyImage
        fields = ['id', 'image', 'is_cover', 'order']


class PropertyAmenitySerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertyAmenity
        fields = ['id', 'name', 'icon']


class PropertyRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertyRule
        fields = ['id', 'rule']


class PropertyListSerializer(serializers.ModelSerializer):
    property_type = PropertyTypeSerializer(read_only=True)
    cover_image = serializers.SerializerMethodField()

    class Meta:
        model = Property
        fields = [
            'id', 'title', 'city', 'district', 'price', 'pricing_period', 'surface',
            'bedrooms', 'bathrooms', 'max_guests', 'status',
            'property_type', 'cover_image', 'created_at'
        ]

    def get_cover_image(self, obj):
        cover = obj.images.filter(is_cover=True).first() or obj.images.first()
        if cover and cover.image:
            return cover.image.url
        return None


class PropertyDetailSerializer(serializers.ModelSerializer):
    property_type = PropertyTypeSerializer(read_only=True)
    images = PropertyImageSerializer(many=True, read_only=True)
    amenities = PropertyAmenitySerializer(many=True, read_only=True)
    rules = PropertyRuleSerializer(many=True, read_only=True)
    owner_email = serializers.EmailField(source='owner.email', read_only=True)

    class Meta:
        model = Property
        fields = [
            'id', 'title', 'description', 'address', 'city', 'district',
            'latitude', 'longitude', 'price', 'pricing_period', 'surface', 'bedrooms',
            'bathrooms', 'max_guests', 'status', 'owner_email',
            'property_type', 'images', 'amenities', 'rules', 'created_at'
        ]


class PropertyCreateUpdateSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255)
    description = serializers.CharField()
    price = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal('0.01'))
    address = serializers.CharField(max_length=255)
    city = serializers.CharField(max_length=100)
    district = serializers.CharField(max_length=100)
    latitude = serializers.DecimalField(max_digits=9, decimal_places=6, required=False, allow_null=True)
    longitude = serializers.DecimalField(max_digits=9, decimal_places=6, required=False, allow_null=True)
    surface = serializers.IntegerField(min_value=1)
    bedrooms = serializers.IntegerField(min_value=0)
    bathrooms = serializers.IntegerField(min_value=0)
    max_guests = serializers.IntegerField(min_value=1)
    property_type_id = serializers.UUIDField()


class PropertyFavoriteSerializer(serializers.ModelSerializer):
    property = PropertyListSerializer(read_only=True)

    class Meta:
        model = PropertyFavorite
        fields = ['id', 'property', 'created_at']
