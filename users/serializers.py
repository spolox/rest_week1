from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from .models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'first_name', 'last_name',
                  'middle_name', 'phone', 'address']
        extra_kwargs = {
            'id': {'read_only': True},
            'username': {'read_only': True},
            'email': {
                'required': True,
                'validators': [UniqueValidator(queryset=User.objects.all())],
            },
            'password': {
                'write_only': True,
                'required': True,
            },
            'first_name': {'required': True},
            'last_name': {'required': True},
            'middle_name': {'required': True},
            'phone': {'required': True},
            'address': {'required': True},
        }

    def create(self, validated_data):
        username = validated_data['email'].split('@')[0]
        user = User(
            username=username,
            email=validated_data['email'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            middle_name=validated_data['middle_name'],
            phone=validated_data['phone'],
            address=validated_data['address'],
        )
        user.set_password(validated_data['password'])
        user.save()
        return user

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            if attr == 'password':
                instance.set_password(value)
            else:
                if attr == 'email':
                    setattr(instance, 'username', value.split('@')[0])
                setattr(instance, attr, value)
        instance.save()
        return instance
