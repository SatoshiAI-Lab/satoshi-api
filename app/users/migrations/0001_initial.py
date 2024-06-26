# Generated by Django 5.0.1 on 2024-04-22 09:13

import django.db.models.deletion
import django.utils.timezone
import django_cryptography.fields
import users.managers
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.CreateModel(
            name="User",
            fields=[
                ("password", models.CharField(max_length=128, verbose_name="password")),
                (
                    "last_login",
                    models.DateTimeField(
                        blank=True, null=True, verbose_name="last login"
                    ),
                ),
                (
                    "is_superuser",
                    models.BooleanField(
                        default=False,
                        help_text="Designates that this user has all permissions without explicitly assigning them.",
                        verbose_name="superuser status",
                    ),
                ),
                (
                    "first_name",
                    models.CharField(
                        blank=True, max_length=150, verbose_name="first name"
                    ),
                ),
                (
                    "last_name",
                    models.CharField(
                        blank=True, max_length=150, verbose_name="last name"
                    ),
                ),
                (
                    "is_staff",
                    models.BooleanField(
                        default=False,
                        help_text="Designates whether the user can log into this admin site.",
                        verbose_name="staff status",
                    ),
                ),
                (
                    "is_active",
                    models.BooleanField(
                        default=True,
                        help_text="Designates whether this user should be treated as active. Unselect this instead of deleting accounts.",
                        verbose_name="active",
                    ),
                ),
                (
                    "date_joined",
                    models.DateTimeField(
                        default=django.utils.timezone.now, verbose_name="date joined"
                    ),
                ),
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                        unique=True,
                    ),
                ),
                ("email", models.EmailField(max_length=99, unique=True)),
                ("mobile", models.CharField(blank=True, max_length=15, null=True)),
                ("added_at", models.DateTimeField(auto_now_add=True)),
                ("ids", models.JSONField(blank=True, null=True)),
                (
                    "groups",
                    models.ManyToManyField(
                        blank=True,
                        help_text="The groups this user belongs to. A user will get all permissions granted to each of their groups.",
                        related_name="user_set",
                        related_query_name="user",
                        to="auth.group",
                        verbose_name="groups",
                    ),
                ),
                (
                    "user_permissions",
                    models.ManyToManyField(
                        blank=True,
                        help_text="Specific permissions for this user.",
                        related_name="user_set",
                        related_query_name="user",
                        to="auth.permission",
                        verbose_name="user permissions",
                    ),
                ),
            ],
            options={
                "verbose_name": "user",
                "verbose_name_plural": "users",
                "abstract": False,
            },
            managers=[
                ("objects", users.managers.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name="Wallet",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                        unique=True,
                    ),
                ),
                ("name", models.CharField(blank=True, max_length=100)),
                ("address", models.CharField(blank=True, max_length=130, null=True)),
                ("public_key", models.CharField(max_length=130)),
                (
                    "private_key",
                    django_cryptography.fields.encrypt(
                        models.CharField(blank=True, max_length=300, null=True)
                    ),
                ),
                (
                    "platform",
                    models.CharField(
                        blank=True,
                        choices=[("EVM", "EVM"), ("SOL", "SOL")],
                        max_length=10,
                        null=True,
                    ),
                ),
                ("added_at", models.DateTimeField(auto_now_add=True)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="WalletLog",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                        unique=True,
                    ),
                ),
                ("chain", models.CharField(blank=True, max_length=30, null=True)),
                (
                    "input_token",
                    models.CharField(blank=True, max_length=128, null=True),
                ),
                (
                    "output_token",
                    models.CharField(blank=True, max_length=128, null=True),
                ),
                ("amount", models.FloatField()),
                ("hash_tx", models.CharField(max_length=128)),
                ("type_id", models.SmallIntegerField(blank=True, null=True)),
                ("status", models.SmallIntegerField(blank=True, null=True)),
                ("added_at", models.DateTimeField(auto_now_add=True)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "db_table": "users_wallet_log",
            },
        ),
        migrations.CreateModel(
            name="UserSubscription",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                        unique=True,
                    ),
                ),
                ("message_type", models.IntegerField()),
                ("content", models.JSONField()),
                (
                    "update_time",
                    models.DateTimeField(default=django.utils.timezone.now),
                ),
                (
                    "create_time",
                    models.DateTimeField(default=django.utils.timezone.now),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "db_table": "user_subscription",
                "unique_together": {("message_type", "user")},
            },
        ),
        migrations.AddConstraint(
            model_name="wallet",
            constraint=models.UniqueConstraint(
                fields=("user", "platform", "public_key"),
                name="unique_user_platform_public_key",
            ),
        ),
        migrations.AlterUniqueTogether(
            name="walletlog",
            unique_together={("hash_tx", "chain")},
        ),
    ]
