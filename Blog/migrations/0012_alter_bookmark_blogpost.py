# Generated by Django 4.0.1 on 2022-02-21 13:33

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('Blog', '0011_topic_approved'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bookmark',
            name='blogPost',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='bookmark_post', to='Blog.blogpost'),
        ),
    ]
