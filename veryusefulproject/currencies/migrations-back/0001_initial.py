# Generated by Django 4.1.9 on 2023-05-20 07:53

from django.db import migrations, models
import django.db.models.deletion
import veryusefulproject.currencies.models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Currency",
            fields=[
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("modified_at", models.DateTimeField(auto_now=True)),
                (
                    "ticker",
                    models.CharField(
                        max_length=5,
                        primary_key=True,
                        serialize=False,
                        validators=[veryusefulproject.currencies.models.alphabetValidator],
                    ),
                ),
                ("desc", models.TextField()),
                ("rate", models.FloatField()),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="FiatCurrency",
            fields=[
                (
                    "currency_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="currencies.currency",
                    ),
                ),
                (
                    "name",
                    models.CharField(
                        max_length=128, validators=[veryusefulproject.currencies.models.alphabetValidator]
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
            bases=("currencies.currency",),
        ),
        migrations.CreateModel(
            name="CryptoCurrency",
            fields=[
                (
                    "currency_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="currencies.currency",
                    ),
                ),
                ("name", models.CharField(max_length=128)),
                (
                    "fiat_currency",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="FiatCurrency_PK",
                        to="currencies.fiatcurrency",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
            bases=("currencies.currency",),
        ),
    ]
