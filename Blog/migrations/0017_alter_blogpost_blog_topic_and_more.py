# Generated by Django 4.0.1 on 2022-02-24 07:56

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('Blog', '0016_blogpost_suggested_topic'),
    ]

    operations = [
        migrations.AlterField(
            model_name='blogpost',
            name='blog_topic',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='topic', to='Blog.topic'),
        ),
        migrations.AlterField(
            model_name='blogpost',
            name='suggested_topic',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='suggest', to='Blog.topic'),
        ),
    ]