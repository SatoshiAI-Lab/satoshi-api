from typing import Any, Literal, OrderedDict
from rest_framework import serializers
from django.contrib.auth.hashers import make_password
from .models import User, Wallet


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields: tuple[Literal['id'], Literal['password'], Literal['email']] = ("id", "password", "email")
        extra_kwargs: dict[str, dict[str, bool]] = {"password": {"write_only": True}}

    def create(self, validated_data: dict) -> Any:
        validated_data["password"] = make_password(password=validated_data.get("password"))
        return super(UserSerializer, self).create(validated_data=validated_data)

    def update(self, instance, validated_data: dict) -> Any:
        validated_data["password"] = make_password(password=validated_data.get("password"))
        return super(UserSerializer, self).update(instance=instance, validated_data=validated_data)


class WalletSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wallet
        fields: str = '__all__'
        read_only_fields: tuple[Literal['id'], Literal['user']] = ('id', 'user')

    def create(self, validated_data) -> Any:
        user: Any = self.context['request'].user
        validated_data['user'] = user
        return super(WalletSerializer, self).create(validated_data=validated_data)
    
    def to_representation(self, instance) -> OrderedDict:
        ret: OrderedDict = super().to_representation(instance=instance)
        ret.pop(key='public_key', default=None)
        ret.pop(key='private_key', default=None)
        return ret
    

class WalletListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wallet
        fields: str = '__all__'
        read_only_fields: tuple[Literal['id'], Literal['user']] = ('id', 'user')

    def create(self, validated_data) -> Any:
        user: Any = self.context['request'].user
        validated_data['user'] = user
        return super(WalletListSerializer, self).create(validated_data=validated_data)
    
    def to_representation(self, instance) -> OrderedDict:
        ret: OrderedDict = super().to_representation(instance=instance)
        ret.pop(key='public_key', default=None)
        ret.pop(key='private_key', default=None)
        
        return ret


class WalletNameUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wallet
        fields: list[str] = ['name']


class PrivateKeySerializer(serializers.ModelSerializer):
    class Meta:
        model = Wallet
        fields: list[str] = ['name', 'address', 'public_key', 'private_key', 'platform']