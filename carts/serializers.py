from rest_framework import serializers

from .models import Cart, CartItem
from items.models import Item
from items.serializers import ItemSerializer


class CartItemSerializer(serializers.ModelSerializer):
    item = ItemSerializer(read_only=True)
    item_id = serializers.PrimaryKeyRelatedField(source='item', queryset=Item.objects.all())
    total_price = serializers.SerializerMethodField('get_total_price')

    class Meta:
        model = CartItem
        fields = ['id', 'item', 'item_id', 'quantity', 'price', 'total_price']
        extra_kwargs = {
            'id': {'read_only': True},
            'item': {'read_only': True},
            'item_id': {'required': True},
            'quantity': {'required': True},
            'price': {'read_only': True},
            'total_price': {'read_only': True},
        }

    def get_total_price(self, obj):
        return f'{obj.price * obj.quantity:.2f}'

    def create(self, validated_data):
        cart, _ = Cart.objects.get_or_create(user=self.context['request'].user)
        cart_item = CartItem(
            item=validated_data['item'],
            quantity=validated_data['quantity'],
            price=validated_data['item'].price,
            cart=cart,
        )
        cart_item.save()
        return cart_item

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            if attr == 'item':
                setattr(instance, 'price', value.price)
            setattr(instance, attr, value)
        instance.save()
        return instance


class CartSerializer(serializers.ModelSerializer):
    total_cost = serializers.SerializerMethodField('get_total_cost')
    items = CartItemSerializer(source='cart_items', many=True)

    class Meta:
        model = Cart
        fields = ['id', 'items', 'total_cost']
        extra_kwargs = {
            'id': {'read_only': True},
        }

    def get_total_cost(self, obj):
        total_cost = 0
        for cart_item in obj.cart_items.all():
            total_cost += cart_item.price * cart_item.quantity
        return f'{total_cost:.2f}'
