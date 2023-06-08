# Generated by Django 4.1.9 on 2023-05-26 07:19

from django.db import migrations, models
import django.db.models.deletion
import veryusefulproject.currencies.models


class Migration(migrations.Migration):
    dependencies = [
        ("currencies", "0001_initial"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="cryptocurrency",
            name="fiat_currency",
        ),
        migrations.AlterField(
            model_name="currency",
            name="desc",
            field=models.TextField(default=""),
        ),
        migrations.AlterField(
            model_name="currency",
            name="rate",
            field=models.FloatField(default=0.0),
        ),
        migrations.AlterField(
            model_name="currency",
            name="ticker",
            field=models.CharField(
                default="ps0Lj",
                max_length=5,
                primary_key=True,
                serialize=False,
                validators=[veryusefulproject.currencies.models.alphabetValidator],
            ),
        ),
        migrations.CreateModel(
            name="FiatCurrencyRate",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("modified_at", models.DateTimeField(auto_now=True)),
                ("rate", models.FloatField()),
                (
                    "fiat_currency",
                    models.ForeignKey(
                        null=True, on_delete=django.db.models.deletion.CASCADE, to="currencies.fiatcurrency"
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="CryptoCurrencyRate",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("modified_at", models.DateTimeField(auto_now=True)),
                ("rate", models.FloatField()),
                (
                    "cryptocurrency",
                    models.ForeignKey(
                        null=True, on_delete=django.db.models.deletion.CASCADE, to="currencies.cryptocurrency"
                    ),
                ),
                (
                    "fiat_currency",
                    models.ForeignKey(
                        null=True, on_delete=django.db.models.deletion.RESTRICT, to="currencies.fiatcurrency"
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
    ]