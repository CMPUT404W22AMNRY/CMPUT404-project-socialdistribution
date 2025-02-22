# Generated by Django 4.0.2 on 2022-04-04 04:26

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0011_remotelike'),
    ]

    operations = [
        migrations.CreateModel(
            name='RemoteComment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('author_url', models.CharField(max_length=512)),
                ('comment', models.TextField()),
                ('content_type', models.CharField(choices=[('text/markdown', 'Commonmark'), ('text/plain', 'Plaintext'), ('application/base64', 'Base64Encoded'), ('image/png;base64', 'PNG'), ('image/jpeg;base64', 'JPEG')], default='text/plain', max_length=18)),
                ('date_published', models.DateTimeField(auto_now_add=True)),
                ('post', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='posts.post')),
            ],
        ),
    ]
