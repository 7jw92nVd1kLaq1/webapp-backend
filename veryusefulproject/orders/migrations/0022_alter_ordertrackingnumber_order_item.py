# Generated by Django 4.1.9 on 2023-11-04 10:44

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("orders", "0021_orderdisputemessage_read_ordermessage_read"),
    ]

    operations = [
        migrations.AlterField(
            model_name="ordertrackingnumber",
            name="order_item",
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to="orders.orderitem"),
        ),
    ]
