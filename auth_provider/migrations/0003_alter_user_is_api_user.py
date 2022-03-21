# Generated by Django 4.0.2 on 2022-03-19 22:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('auth_provider', '0002_user_is_api_user'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='is_api_user',
            field=models.BooleanField(default=False, help_text='Designates whether user has access to REST API', verbose_name='api access status'),
        ),
    ]
