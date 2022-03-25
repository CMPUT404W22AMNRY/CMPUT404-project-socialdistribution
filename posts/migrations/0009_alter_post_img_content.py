# Generated by Django 4.0.2 on 2022-03-24 21:29

from django.db import migrations, models
import posts.models
import socialdistribution.storage


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0008_alter_post_img_content'),
    ]

    operations = [
        migrations.AlterField(
            model_name='post',
            name='img_content',
            field=models.ImageField(blank=True, null=True, storage=socialdistribution.storage.ImageStorage(), upload_to=posts.models.img_content_filename, verbose_name='Image'),
        ),
    ]
