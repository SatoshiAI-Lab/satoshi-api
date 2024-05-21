from typing import Any
from rest_framework import serializers

from . import models;
import os
from urllib.parse import urljoin


class CoinSearch(serializers.ModelSerializer):
    logo = serializers.SerializerMethodField()
    chain = serializers.SerializerMethodField()

    class Meta:
        model = models.Coin
        fields: list[str] = [
            'id', 'name', 'symbol', 'logo', 'chain'
        ]
    
    def get_logo(self, row) -> str:
        return urljoin(base=os.getenv(key='IMAGE_DOMAIN'), url=row.logo)
    
    def get_chain(self, row) -> list:
        return row.get_chain()
    
class CoinListSerializer(serializers.ModelSerializer):
    logo = serializers.SerializerMethodField()

    class Meta:
        model = models.Coin
        fields: list[str] = [
            'id', 'name', 'symbol', 'slug', 'logo', 'price', 'market_cap', 'percent_change_24_h'
        ]

    def get_logo(self, row) -> str:
        return urljoin(base=os.getenv(key='IMAGE_DOMAIN'), url=row.logo)
