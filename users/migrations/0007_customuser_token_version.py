# Generated by Django 5.1.1 on 2025-01-17 15:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0006_rename_otp_sent_customuser_otp_verified_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='token_version',
            field=models.IntegerField(default=0),
        ),
    ]
