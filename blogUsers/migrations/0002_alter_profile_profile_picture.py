# Generated by Django 4.0.1 on 2022-02-17 22:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blogUsers', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='profile_picture',
            field=models.ImageField(null=True, upload_to='profile/<django.db.models.fields.related.OneToOneField>'),
        ),
    ]
