# Generated by Django 4.0.2 on 2022-02-21 23:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('auth_provider', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='author',
            options={},
        ),
        migrations.AddField(
            model_name='author',
            name='github_url',
            field=models.CharField(blank=True, max_length=512),
        ),
        migrations.AddField(
            model_name='author',
            name='profile_image_url',
            field=models.CharField(blank=True, max_length=512),
        ),
    ]
