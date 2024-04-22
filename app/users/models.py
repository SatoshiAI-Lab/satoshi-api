import json
import uuid

from django.utils.timezone import now
from django.core.exceptions import ValidationError
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.core.exceptions import ObjectDoesNotExist
from users.managers import UserManager
from rest_framework import serializers
from utils.constants import *

from django_cryptography.fields import encrypt


class User(AbstractUser):
    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False, unique=True
    )
    username = None
    email = models.EmailField(max_length=99, unique=True)
    mobile = models.CharField(
        max_length=15,
        blank=True,
        null=True,
    )
    added_at = models.DateTimeField(
        auto_now_add=True,
    )
    ids = models.JSONField(blank=True, null=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email

    objects = UserManager()

    def save(self, *args, **kwargs):
        if not self.ids:
            self.ids = json.dumps(DEFAULT_IDS)
        return super().save(*args, **kwargs)


class Wallet(models.Model):
    PLATFORM_CHOICES = [
        ("EVM", "EVM"),
        ("SOL", "SOL"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, unique=True)
    name = models.CharField(max_length=100, blank=True)
    address = models.CharField(max_length=130, blank=True, null=True)
    public_key = models.CharField(max_length=130)
    # Use the encrypt field provided by django-cryptography for encrypted storage
    private_key = encrypt(models.CharField(max_length=300, blank=True, null=True))
    platform = models.CharField(max_length=10, choices=PLATFORM_CHOICES, blank=True, null=True)
    user = models.ForeignKey('User', on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'platform', 'public_key'], name='unique_user_platform_public_key')
        ]

    def save(self, *args, **kwargs):
        try:
            type(self).objects.get(pk=self.pk)
            is_update = True
        except ObjectDoesNotExist:
            is_update = False

        if not self.platform:
            self.platform = DEFAULT_PLATFORM
        
        if not is_update:
            if Wallet.objects.filter(user=self.user, platform=self.platform, public_key=self.public_key).exists():
                raise serializers.ValidationError({"public_key": "This public key already exists."})

        if not self.name:
            self.name = "Wallet " + self.address[-4:]
        super(Wallet, self).save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} - {self.platform} - {self.user.email}"
    

class WalletLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, unique=True)
    chain = models.CharField(max_length=30, blank=True, null=True)
    input_token = models.CharField(max_length=128, blank=True, null=True)
    output_token = models.CharField(max_length=128, blank=True, null=True)
    amount = models.FloatField()
    hash_tx = models.CharField(max_length=128)
    type_id = models.SmallIntegerField(blank=True, null=True)
    status = models.SmallIntegerField(blank=True, null=True)
    user = models.ForeignKey('User', on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'users_wallet_log'
        unique_together = (('hash_tx', 'chain'),)

 
class UserSubscription(models.Model):
    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False, unique=True
    )
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