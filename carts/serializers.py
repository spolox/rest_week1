from rest_framework import serializers

from .models import Cart, CartItem
from items.models import Item
from items.serializers import ItemSerializer


class CartItemSerializer(serializers.ModelSerializer):
    item = ItemSerializer(read_only=True)
    item_id = serializers.PrimaryKeyRelatedField(source='item', queryset=Item.objects.all())
    total_price = serializers.DecimalField(decimal_places=2, max_digits=8)

    class Meta:
        model = CartItem
        fields = ['id', 'item', 'item_id', 'quantity', 'price', 'total_price']
        read_only_fields = ['id', 'price', 'total_price', 'item']
        extra_kwargs = {
            'item_id': {'required': True},
            'quantity': {'required': True},
        }

    def create(self, validated_data):
        cart = self.context['request'].user.my_cart
        cart_item = CartItem(
            item=validated_data['item'],
            quantity=validated_data['quantity'],
            price=validated_data['item'].price,
            cart=cart,
        )
        cart_item.save()
        return cart_item

    def update(self, instance, validated_data):
        if 'item' in validated_data:
            instance.item = validated_data['item']
            instance.price = validated_data['item'].price
        instance.quantity = validated_data.get('quantity', instance.quantity)
        instance.save()
        return instance


class CartSerializer(serializers.ModelSerializer):
    total_cost = serializers.DecimalField(decimal_places=2, max_digits=8)
    items = CartItemSerializer(source='cart_items', many=True)

    class Meta:
        model = Cart
        fields = ['id', 'items', 'total_cost']
        read_only_fields = ['id']
