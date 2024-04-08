from rest_framework import serializers
from django.contrib.auth.hashers import make_password
from .models import User, Wallet
from w3.wallet import WalletHandler
from utils.constants import *


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "password", "email")
        extra_kwargs = {"password": {"write_only": True}}

    def create(self, validated_data):
        validated_data["password"] = make_password(validated_data.get("password"))
        return super(UserSerializer, self).create(validated_data)

    def update(self, instance, validated_data):
        validated_data["password"] = make_password(validated_data.get("password"))
        return super(UserSerializer, self).update(instance, validated_data)


class WalletSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wallet
        fields = '__all__'
        read_only_fields = ('id', 'user')

    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['user'] = user
        return super(WalletSerializer, self).create(validated_data)
    
    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret.pop('public_key', None)
        ret.pop('private_key', None)
        
        # wallet_handler = WalletHandler()
        # data = wallet_handler.get_balances(ret.get('chain', DEFAULT_CHAIN), ret['address'])
        # ret['value'] = data.get('value', 0)
        # ret['tokens'] = data.get('tokens', [])
        return ret
    

class WalletListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wallet
        fields = '__all__'
        read_only_fields = ('id', 'user')

    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['user'] = user
        return super(WalletListSerializer, self).create(validated_data)
    
    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret.pop('public_key', None)
        ret.pop('private_key', None)
        
        return ret


class WalletNameUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wallet
        fields = ['name']


class PrivateKeySerializer(serializers.ModelSerializer):
    class Meta:
        model = Wallet
        fields = ['name', 'address', 'public_key', 'private_key', 'platform']