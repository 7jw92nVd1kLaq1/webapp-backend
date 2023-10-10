# Generated by Django 4.1.9 on 2023-09-13 05:24

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("payments", "0002_alter_orderpayment_additional_cost_and_more"),
        ("orders", "0013_businessurl_remove_business_industry_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="orderaddresslink",
            name="address",
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="orders.orderaddress"),
        ),
        migrations.AlterField(
            model_name="orderaddresslink",
            name="order",
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to="orders.order"),
        ),
        migrations.AlterField(
            model_name="ordercustomerlink",
            name="customer",
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name="ordercustomerlink",
            name="order",
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to="orders.order"),
        ),
        migrations.AlterField(
            model_name="orderdisputemessage",
            name="user",
            field=models.ForeignKey(
                default=123, on_delete=django.db.models.deletion.RESTRICT, to=settings.AUTH_USER_MODEL
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="orderintermediarylink",
            name="intermediary",
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name="orderintermediarylink",
            name="order",
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to="orders.order"),
        ),
        migrations.AlterField(
            model_name="ordermessage",
            name="order",
            field=models.ForeignKey(
                default=123, on_delete=django.db.models.deletion.RESTRICT, related_name="messages", to="orders.order"
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="ordermessage",
            name="user",
            field=models.ForeignKey(
                default=123, on_delete=django.db.models.deletion.RESTRICT, to=settings.AUTH_USER_MODEL
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="orderpaymentlink",
            name="order",
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to="orders.order"),
        ),
        migrations.AlterField(
            model_name="orderpaymentlink",
            name="payment",
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to="payments.orderpayment"),
        ),
    ]