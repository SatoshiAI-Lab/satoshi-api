import uuid

from django.db import models
from django.utils.timezone import now
from django.core.exceptions import ValidationError
from utils.constants import *


class UserSubscription(models.Model):
    message_type = models.IntegerField()
    content = models.JSONField()
    user = models.ForeignKey('users.User', on_delete=models.CASCADE)
    update_time = models.DateTimeField(default=now)
    create_time = models.DateTimeField(default=now)

    class Meta:
        db_table = 'user_subscription'
        unique_together = (('message_type', 'user'),)

    def clean(self):
        if self.message_type < 0 or self.message_type > 4:
            raise ValidationError({'content': 'Must between 0 and 4.'})
        if self.message_type == 0: # news
            if not isinstance(self.content, dict) or not 'switch' in self.content or self.content['switch'] not in ['on', 'off']:
                raise ValidationError({'content': 'Must be a dictionary containing switch.'})
        elif self.message_type == 1: # twitter
            if not (isinstance(self.content, list) and all(isinstance(item, str) and len(item) > 0 for item in self.content)):
                raise ValidationError({'content': 'Must be a list of strings.'})
            if len(self.content) != len(set(self.content)):
                raise ValidationError({'content': 'Elements are repeated.'})
        elif self.message_type == 2: # announcement
            if not (isinstance(self.content, list) and all(isinstance(item, int) and item > 0 for item in self.content)):
                raise ValidationError({'content': 'Must be a list of integers.'})
            if len(self.content) != len(set(self.content)):
                raise ValidationError({'content': 'Elements are repeated.'})
        elif self.message_type == 3: # trade
            if not (isinstance(self.content, list) and all(isinstance(item, dict) and len(item.get('address', '')) > 41 for item in self.content)):
                raise ValidationError({'content': 'MIt must be a dictionary array. The element values in other dictionaries must contain address.'})
            addresses = [c['address'] for c in self.content]
            if len(addresses) != len(set(addresses)):
                raise ValidationError({'content': 'Address elements are repeated.'})
        elif self.message_type == 4: # pool
            if not (isinstance(self.content, list) and all(isinstance(item, dict) and item.get('chain', '') in CHAIN_DICT for item in self.content)):
                raise ValidationError({'content': 'MIt must be a dictionary array. The element values in other dictionaries must contain chain.'})
            chains = [c['chain'] for c in self.content]
            if len(chains) != len(set(chains)):
                raise ValidationError({'content': 'Chain elements are repeated.'})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class TradeAddress(BaseModel):
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
    user_id = models.IntegerField()
    is_deleted = models.IntegerField()
    remark = models.CharField(max_length=300, blank=True, null=True)
    logo = models.CharField(max_length=300, blank=True, null=True)
    openid = models.CharField(max_length=100, blank=True, null=True)
    is_global = models.IntegerField()
    twitter_status = models.IntegerField()

    class Meta:
        db_table = 'twitter_user'
        unique_together = (('twitter_id', 'user_id'),)

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