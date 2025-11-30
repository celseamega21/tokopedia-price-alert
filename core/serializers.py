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
    class Meta:
        model = Product
        fields = ['id', 'name', 'url', 'last_price', 'email']

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)