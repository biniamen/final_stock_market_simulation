# Generated by Django 5.1.1 on 2024-11-28 17:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0003_remove_customuser_balance_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='is_approved',
            field=models.BooleanField(default=False),
        ),
    ]