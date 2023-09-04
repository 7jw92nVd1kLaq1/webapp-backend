# Generated by Django 4.1.9 on 2023-06-21 07:57

from decimal import Decimal
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("orders", "0006_orderintermediarycandidate_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="ordertrackingnumber",
            name="shipping_cost",
            field=models.DecimalField(decimal_places=2, default=Decimal("0"), max_digits=10),
        ),
    ]
