import uuid

from django.db import models
from utils.constants import *


class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Config(BaseModel):
    ave_auth = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        db_table = 'config'


class TradeAddress(BaseModel):
    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False, unique=True
    )
    address = models.CharField(max_length=42)
    name = models.CharField(max_length=100)
    remark = models.CharField(max_length=300)
    count = models.IntegerField(default=1)
    is_global = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'trade_address'

class TwitterUser(BaseModel):
    twitter = models.CharField(max_length=100, blank=True, null=True)
    twitter_id = models.CharField(max_length=100, blank=True, null=True)
    name = models.CharField(max_length=100, blank=True, null=True)
    is_deleted = models.IntegerField()
    remark = models.CharField(max_length=300, blank=True, null=True)
    logo = models.CharField(max_length=300, blank=True, null=True)
    openid = models.CharField(max_length=100, blank=True, null=True)
    is_global = models.IntegerField()
    twitter_status = models.IntegerField()

    class Meta:
        db_table = 'twitter_user'
        unique_together = (('twitter_id'),)

class Exchange(BaseModel):    
    slug = models.CharField(max_length=30, blank=True, null=False, unique=True)
    name = models.CharField(max_length=30, blank=True, null=True)
    cmc_id = models.IntegerField(unique=True, blank=True, null=True)
    chain_id = models.IntegerField(blank=True, null=True)
    url = models.URLField(max_length=2048, blank=True, null=False, default='')
    display_name = models.CharField(max_length=255, null=True)
    announcement_subable = models.IntegerField()
    announcement_order = models.IntegerField()

    class Meta:
        db_table = 'exchange'