from django.db import models
import os
from urllib.parse import urljoin


class Coin(models.Model):
    name = models.CharField(max_length=255, blank=True, null=True, verbose_name='Currency Name')
    symbol = models.CharField(max_length=255, blank=True, null=True, verbose_name='Currency Abbreviation')
    slug = models.CharField(max_length=255, blank=True, null=True, verbose_name='Identifier')
    max_supply = models.FloatField(blank=True, null=True, verbose_name='Max Supply')
    total_supply = models.FloatField(blank=True, null=True, verbose_name='Total Supply')
    circulating_supply = models.FloatField(blank=True, null=True, verbose_name='Circulating Supply')
    price = models.FloatField(blank=True, null=True, default=0, verbose_name='Price')
    market_cap = models.FloatField(blank=True, null=True, default=0, verbose_name='Market Cap')
    percent_change_1_h = models.FloatField(blank=True, null=True, verbose_name='1h Change')
    percent_change_24_h = models.FloatField(blank=True, null=True, verbose_name='24h Change')
    percent_change_7_d = models.FloatField(blank=True, null=True, verbose_name='7d Change')
    percent_change_30_d = models.FloatField(blank=True, null=True, verbose_name='30d Change')
    logo = models.CharField(max_length=255, blank=True, null=True, verbose_name='Currency Logo')

    def get_chain(self):
        chain_sql = f"""
        select tcd.id, tcd.address, c.symbol, c.logo from token_chain_data tcd 
        left join chain c on tcd.platform_id=c.platform_id 
        where tcd.token_id = {self.id}
        """
        chain_obj = CoinChainData.objects.using('coin_source').raw(chain_sql)
        chain = []
        if chain_obj:
            for c in chain_obj:
                chain.append(dict(
                    address=c.address, 
                    name = c.symbol, 
                    logo = urljoin(os.getenv('IMAGE_DOMAIN'), c.logo) if c.logo else os.getenv('IMAGE_DOMAIN') + '/img/chain/base.png',
                ))
        return chain

    class Meta:
        db_table = 'token'

class CoinChainData(models.Model):
    token = models.ForeignKey('Coin', on_delete = models.CASCADE)
    address = models.CharField(max_length=150)
    platform_id = models.IntegerField()
    token_type_id = models.IntegerField(default=1)

    class Meta:
        db_table = 'token_chain_data'
