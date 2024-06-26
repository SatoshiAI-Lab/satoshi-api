import json
from typing import Literal
import uuid

from django.utils.timezone import now
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.core.exceptions import ObjectDoesNotExist
from users.managers import UserManager
from rest_framework import serializers
from utils import constants

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
    REQUIRED_FIELDS: list[str] = []

    def __str__(self) -> str:
        return self.email

    objects = UserManager()

    def save(self, *args, **kwargs) -> None:
        if not self.ids:
            self.ids: str = json.dumps(constants.DEFAULT_IDS)
        return super().save(*args, **kwargs)


class Wallet(models.Model):
    PLATFORM_CHOICES: list = [
        ("EVM", "EVM"),
        ("SOL", "SOL"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, unique=True)
    name = models.CharField(max_length=100, blank=True)
    address = models.CharField(max_length=130, blank=True, null=True)
    public_key = models.CharField(max_length=130)
    private_key = encrypt(base_field=models.CharField(max_length=300, blank=True, null=True))
    platform = models.CharField(max_length=10, choices=PLATFORM_CHOICES, blank=True, null=True)
    user = models.ForeignKey('User', on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints: list[models.UniqueConstraint] = [
            models.UniqueConstraint(fields=['user', 'platform', 'public_key'], name='unique_user_platform_public_key')
        ]

    def save(self, *args, **kwargs) -> None:
        try:
            type(self).objects.get(pk=self.pk)
            is_update = True
        except ObjectDoesNotExist:
            is_update = False

        if not self.platform:
            self.platform: str = constants.DEFAULT_PLATFORM
        
        if not is_update:
            if Wallet.objects.filter(user=self.user, platform=self.platform, public_key=self.public_key).exists():
                raise serializers.ValidationError(detail=dict(detail='Record already exists.'))

        if not self.name:
            self.name: str = "Wallet " + self.address[-4:]
        super(Wallet, self).save(*args, **kwargs)

    def __str__(self) -> str:
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
        db_table: str = 'users_wallet_log'
        unique_together: tuple[tuple[Literal['hash_tx'], Literal['chain']]] = (('hash_tx', 'chain'),)

 
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
        db_table: str = 'user_subscription'
        unique_together: tuple[tuple[Literal['message_type'], Literal['user']]] = (('message_type', 'user'),)

    def save(self, *args, **kwargs) -> None:
        self.full_clean()
        super().save(*args, **kwargs)