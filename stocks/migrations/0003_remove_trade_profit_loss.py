# Generated by Django 5.1.1 on 2024-11-26 17:54

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('stocks', '0002_alter_orders_status'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='trade',
            name='profit_loss',
        ),
    ]
