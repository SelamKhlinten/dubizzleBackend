# Generated by Django 5.1.6 on 2025-02-27 08:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0007_product_currency'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='currency',
            field=models.CharField(choices=[('ETB', 'Ethiopian Birr'), ('USD', 'US Dollar')], default='ETB', max_length=3),
        ),
    ]
