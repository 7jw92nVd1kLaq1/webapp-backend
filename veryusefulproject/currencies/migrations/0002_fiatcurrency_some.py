# Generated by Django 4.1.9 on 2023-06-12 11:22

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("currencies", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="fiatcurrency",
            name="some",
            field=models.BooleanField(default=True),
            preserve_default=False,
        ),
    ]