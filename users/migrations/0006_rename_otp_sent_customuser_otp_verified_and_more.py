# Generated by Django 5.1.1 on 2024-12-17 18:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0005_customuser_otp_code_customuser_otp_sent'),
    ]

    operations = [
        migrations.RenameField(
            model_name='customuser',
            old_name='otp_sent',
            new_name='otp_verified',
        ),
        migrations.AddField(
            model_name='customuser',
            name='otp_attempts',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='customuser',
            name='otp_sent_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
