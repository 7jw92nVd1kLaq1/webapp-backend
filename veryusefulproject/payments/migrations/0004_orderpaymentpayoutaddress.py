# Generated by Django 4.1.9 on 2023-10-10 04:04

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("currencies", "0005_fiatcurrency_symbol"),
        ("payments", "0003_orderpaymentinvoice_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="OrderPaymentPayoutAddress",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("modified_at", models.DateTimeField(auto_now=True)),
                ("payout_address", models.TextField()),
                (
                    "cryptocurrency",
                    models.ForeignKey(
                        null=True, on_delete=django.db.models.deletion.SET_NULL, to="currencies.cryptocurrency"
                    ),
                ),
                (
                    "payment",
                    models.ForeignKey(
                        null=True, on_delete=django.db.models.deletion.SET_NULL, to="payments.orderpayment"
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
    ]
