# Generated by Django 4.0.1 on 2022-02-17 22:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Blog', '0004_alter_blogpost_cover_photo'),
    ]

    operations = [
        migrations.AlterField(
            model_name='blogpost',
            name='likes',
            field=models.PositiveIntegerField(default=0),
        ),
    ]