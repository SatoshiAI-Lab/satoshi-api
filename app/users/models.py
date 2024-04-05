import uuid
from eth_utils import keccak

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.core.exceptions import ObjectDoesNotExist
from users.managers import UserManager
from rest_framework import serializers

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
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email

    objects = UserManager()


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
            self.platform = 'SOL'
        
        if not self.address:
            if self.platform == 'EVM':
                public_key_bytes = bytes.fromhex(self.public_key[2:])
                self.address = "0x" + keccak(public_key_bytes[1:]).hex()[-40:]
            elif self.platform == 'SOL':
                self.address = self.public_key

        if not is_update:
            if Wallet.objects.filter(user=self.user, platform=self.platform, public_key=self.public_key).exists():
                raise serializers.ValidationError({"public_key": "This public key already exists."})

        if not self.name:
            self.name = "Wallet " + self.address[-4:]
        super(Wallet, self).save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} - {self.platform} - {self.user.email}"
    

class WalletLog(models.Model):
    PLATFORM_CHOICES = [
        ("EVM", "EVM"),
        ("SOL", "SOL"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, unique=True)
    platform = models.CharField(max_length=10, choices=PLATFORM_CHOICES, blank=True, null=True)
    input_token = models.CharField(max_length=128)
    output_token = models.CharField(max_length=128)
    amount = models.FloatField()
    hash_tx = models.CharField(max_length=128)
    type_id = models.SmallIntegerField(blank=True, null=True)
    status = models.SmallIntegerField(blank=True, null=True)
    user = models.ForeignKey('User', on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'users_wallet_log'
        unique_together = (('hash_tx', 'platform'),)
