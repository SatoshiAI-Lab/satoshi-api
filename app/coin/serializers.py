from rest_framework import serializers

from . import models;
import os
from urllib.parse import urljoin


class CoinSearch(serializers.ModelSerializer):
    logo = serializers.SerializerMethodField()
    chain = serializers.SerializerMethodField()

    class Meta:
        model = models.Coin
        fields = [
            'id', 'name', 'symbol', 'logo', 'chain'
        ]
    
    def get_logo(self, row):
        return urljoin(os.getenv('IMAGE_DOMAIN'), row.logo)
    
    def get_chain(self, row):
        return row.get_chain()
