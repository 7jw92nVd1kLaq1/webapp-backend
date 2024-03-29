# Generated by Django 4.1.9 on 2023-06-12 11:08

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("currencies", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Cart",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("modified_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="CartItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("modified_at", models.DateTimeField(auto_now=True)),
                ("image_url", models.URLField()),
                ("name", models.TextField()),
                ("quantity", models.PositiveIntegerField()),
                ("price", models.FloatField()),
                ("url", models.URLField()),
                ("options", models.JSONField()),
                ("cart", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="carts.cart")),
                (
                    "fiat_currency",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="currencies.fiatcurrency"),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
    ]
