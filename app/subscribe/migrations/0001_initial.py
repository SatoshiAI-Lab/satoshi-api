# Generated by Django 5.0.1 on 2024-04-05 08:03

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Exchange",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("slug", models.CharField(blank=True, max_length=30, unique=True)),
                ("name", models.CharField(blank=True, max_length=30, null=True)),
                ("cmc_id", models.IntegerField(blank=True, null=True, unique=True)),
                ("chain_id", models.IntegerField(blank=True, null=True)),
                ("url", models.URLField(blank=True, default="", max_length=2048)),
                ("display_name", models.CharField(max_length=255, null=True)),
                ("announcement_subable", models.IntegerField()),
                ("announcement_order", models.IntegerField()),
            ],
            options={
                "db_table": "exchange",
            },
        ),
        migrations.CreateModel(
            name="TradeAddress",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("address", models.CharField(max_length=42)),
                ("name", models.CharField(max_length=100)),
                ("remark", models.CharField(max_length=300)),
                ("is_global", models.IntegerField(default=0)),
            ],
            options={
                "db_table": "trade_address",
            },
        ),
        migrations.CreateModel(
            name="TwitterUser",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("twitter", models.CharField(blank=True, max_length=100, null=True)),
                ("twitter_id", models.CharField(blank=True, max_length=100, null=True)),
                ("name", models.CharField(blank=True, max_length=100, null=True)),
                ("user_id", models.IntegerField()),
                ("is_deleted", models.IntegerField()),
                ("remark", models.CharField(blank=True, max_length=300, null=True)),
                ("logo", models.CharField(blank=True, max_length=300, null=True)),
                ("openid", models.CharField(blank=True, max_length=100, null=True)),
                ("is_global", models.IntegerField()),
                ("twitter_status", models.IntegerField()),
            ],
            options={
                "db_table": "twitter_user",
                "unique_together": {("twitter_id", "user_id")},
            },
        ),
        migrations.CreateModel(
            name="UserSubscription",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
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
            },
        ),
    ]
