# Generated by Django 4.0.2 on 2022-04-03 03:07

from django.conf import settings
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('follow', '0005_remoterquest_remotefollow'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='RemoteRquest',
            new_name='RemoteRequest',
        ),
    ]
