# Generated by Django 4.0.1 on 2022-02-21 13:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Blog', '0010_topic_blogpost_blog_topic'),
    ]

    operations = [
        migrations.AddField(
            model_name='topic',
            name='approved',
            field=models.BooleanField(default=False),
        ),
    ]