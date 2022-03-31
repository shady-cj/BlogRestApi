# Generated by Django 4.0.1 on 2022-02-18 00:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Blog', '0005_alter_blogpost_likes'),
    ]

    operations = [
        migrations.AddField(
            model_name='blogpost',
            name='comments_by',
            field=models.ManyToManyField(related_name='blog_comments', to='Blog.Comment'),
        ),
        migrations.RemoveField(
            model_name='blogpost',
            name='comments',
        ),
        migrations.AddField(
            model_name='blogpost',
            name='comments',
            field=models.PositiveIntegerField(default=0),
        ),
    ]