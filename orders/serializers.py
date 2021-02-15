from django.utils import timezone
from rest_framework import serializers

from .models import Order
from carts.serializers import CartSerializer


def check_delivery_at_time(value):
    if value < timezone.now():
        raise serializers.ValidationError({"detail": "You cannot set delivery_at earlier now time"})
    return value


class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['id', 'cart', 'status', 'total_cost', 'address', 'delivery_at', 'created_at']
        read_only_fields = ['id', 'cart', 'total_cost', 'created_at', 'status']
        extra_kwargs = {
            'address': {'required': True},
            'delivery_at': {'required': True, 'validators': [check_delivery_at_time]},
        }

    def create(self, validated_data):
        user = self.context['request'].user
        cart = user.my_cart
        if cart.cart_items.count() == 0:
            raise serializers.ValidationError({"detail": "Your cart is empty"})
        order = Order(
            recipient=user,
            cart=cart,
            total_cost=cart.total_cost,
            address=validated_data['address'],
            delivery_at=validated_data['delivery_at'],
        )
        order.save()
        return order


class OrderRetrieveUpdateSerializer(serializers.ModelSerializer):
    cart = CartSerializer(read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'cart', 'status', 'total_cost', 'address', 'delivery_at', 'created_at', 'recipient']
        read_only_fields = ['id', 'cart', 'total_cost', 'created_at', 'recipient']
        extra_kwargs = {
            'status': {'required': True},
            'address': {'required': True},
            'delivery_at': {'required': True, 'validators': [check_delivery_at_time]},
        }

    def update(self, instance, validated_data):
        if instance.status != Order.StatusChoices.CREATED:
            raise serializers.ValidationError({"detail": f"Your order is {instance.status}"})

        if 'status' in validated_data:
            # instance.status = CREATED, validated_data.status can be or CREATED (not update status)
            #  or CANCELLED (for update status)
            if instance.status != validated_data['status']:
                if validated_data['status'] != Order.StatusChoices.CANCELLED:
                    raise serializers.ValidationError({"detail": "You can only set status as `cancelled`"})

        instance.status = validated_data.get('status', instance.status)
        instance.delivery_at = validated_data.get('delivery_at', instance.delivery_at)
        instance.address = validated_data.get('address', instance.address)
        instance.save()
        return instance
