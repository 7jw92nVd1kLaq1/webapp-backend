# Generated by Django 4.1.9 on 2023-09-03 14:35

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("orders", "0011_alter_orderaddresslink_address"),
    ]

    operations = [
        migrations.AlterField(
            model_name="orderreview",
            name="rating",
            field=models.DecimalField(decimal_places=2, max_digits=3),
        ),
        migrations.AddIndex(
            model_name="order",
            index=models.Index(fields=["url_id"], name="orders_orde_url_id_5f1fed_idx"),
        ),
    ]
