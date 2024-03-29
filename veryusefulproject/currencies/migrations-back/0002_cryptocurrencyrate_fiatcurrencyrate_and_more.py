# Generated by Django 4.1.9 on 2023-05-26 07:06

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import veryusefulproject.currencies.models


class Migration(migrations.Migration):
    dependencies = [
        ("currencies", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="CryptoCurrencyRate",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("modified_at", models.DateTimeField(auto_now=True)),
                ("rate", models.FloatField()),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="FiatCurrencyRate",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("modified_at", models.DateTimeField(auto_now=True)),
                ("rate", models.FloatField()),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.RemoveField(
            model_name="cryptocurrency",
            name="currency_ptr",
        ),
        migrations.RemoveField(
            model_name="cryptocurrency",
            name="fiat_currency",
        ),
        migrations.RemoveField(
            model_name="fiatcurrency",
            name="currency_ptr",
        ),
        migrations.AddField(
            model_name="cryptocurrency",
            name="created_at",
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="cryptocurrency",
            name="desc",
            field=models.TextField(default=""),
        ),
        migrations.AddField(
            model_name="cryptocurrency",
            name="modified_at",
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddField(
            model_name="cryptocurrency",
            name="rate",
            field=models.FloatField(default=0.0),
        ),
        migrations.AddField(
            model_name="cryptocurrency",
            name="ticker",
            field=models.CharField(
                default="Igl24",
                max_length=5,
                primary_key=True,
                serialize=False,
                validators=[veryusefulproject.currencies.models.alphabetValidator],
            ),
        ),
        migrations.AddField(
            model_name="fiatcurrency",
            name="created_at",
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="fiatcurrency",
            name="desc",
            field=models.TextField(default=""),
        ),
        migrations.AddField(
            model_name="fiatcurrency",
            name="modified_at",
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddField(
            model_name="fiatcurrency",
            name="rate",
            field=models.FloatField(default=0.0),
        ),
        migrations.AddField(
            model_name="fiatcurrency",
            name="ticker",
            field=models.CharField(
                default="Igl24",
                max_length=5,
                primary_key=True,
                serialize=False,
                validators=[veryusefulproject.currencies.models.alphabetValidator],
            ),
        ),
        migrations.DeleteModel(
            name="Currency",
        ),
        migrations.AddField(
            model_name="fiatcurrencyrate",
            name="fiat_currency",
            field=models.ForeignKey(
                null=True, on_delete=django.db.models.deletion.CASCADE, to="currencies.fiatcurrency"
            ),
        ),
        migrations.AddField(
            model_name="cryptocurrencyrate",
            name="cryptocurrency",
            field=models.ForeignKey(
                null=True, on_delete=django.db.models.deletion.CASCADE, to="currencies.cryptocurrency"
            ),
        ),
        migrations.AddField(
            model_name="cryptocurrencyrate",
            name="fiat_currency",
            field=models.ForeignKey(
                null=True, on_delete=django.db.models.deletion.RESTRICT, to="currencies.fiatcurrency"
            ),
        ),
    ]
