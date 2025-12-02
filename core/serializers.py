from rest_framework import serializers
from .models import Product

# serializer for input data
class ProductInputSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['url', 'email']
        read_only_fields = ['user']

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)

# serializer for output data
class ProductOutputSerializer(serializers.ModelSerializer):
    price = serializers.SerializerMethodField()
    product_name = serializers.CharField(source="name")

    class Meta:
        model = Product
        fields = ['id', 'email', 'product_name', 'url', 'price']

    def get_price(self, obj):
        if obj.last_price is None:
            return 0
        return f"Rp {obj.last_price:,.0f}".replace(",", ".")

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)