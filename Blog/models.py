from django.db import models
from ckeditor.fields import RichTextField
from django.utils import timezone 
from django.contrib.auth.models import User
from datetime import datetime
import math
from django.db.models.signals import m2m_changed,post_save


def path_file_name(instance, filename):
    return '/'.join(filter(None, ('blogs', instance.author.username,instance.id,'%Y', filename)))

class Topic(models.Model):
    name = models.CharField(max_length = 255)
    approved = models.BooleanField(default=False)


    def __str__(self):
        return self.name

    

class BlogPost(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE,related_name="user_posts")
    title = models.CharField(max_length = 255)
    caption = models.CharField(max_length = 255,null = True)
    cover_photo = models.ImageField(upload_to=path_file_name,null=True,blank=True)
    content = RichTextField()
    created_at = models.DateTimeField(auto_now_add= True)
    updated_at = models.DateTimeField(auto_now = True)
    published = models.BooleanField(default = False,blank= True)
    published_date = models.DateTimeField(null =True,blank=True)
    featured = models.BooleanField(default=False)
    comments_by = models.ManyToManyField('Comment',related_name ='blog_comments',blank=True)
    comments = models.PositiveIntegerField(default= 0)
    likes = models.PositiveIntegerField(default= 0)
    liked_by = models.ManyToManyField(User, related_name = 'post_likedBy',blank=True )
    blog_topic = models.ForeignKey(Topic,on_delete=models.CASCADE, related_name= 'topic',null = True,blank= True)
    suggested_topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name = 'suggest' , null = True,blank=True)
    trashed = models.BooleanField(default=False)

    @property
    def format_published_date(self):
        return self.published_date.strftime(" %I:%M %p · %b %d, %Y")
    @property
    def published_period(self):
        if self.published_date:
            data= timezone.now() - self.published_date
            if data.days == 0:
                secs = data.seconds
                hours = math.floor(secs / 3600)
                
                minutes = math.floor(secs / 60)
                if hours > 0:
                    return f'{hours} hour{self.pluralize_words(hours)} ago'
                elif minutes > 0:
                    return f'{minutes} minute{self.pluralize_words(minutes)} ago'
                else:

                    return f'{secs} second{self.pluralize_words(secs)} ago'
            elif data.days > 0 and data.days < 30:
                return f'{data.days} day{self.pluralize_words(data.days)} ago'

            elif data.days >= 30:
                months = math.floor(data.days / 30)
                if months > 0 and months < 12:
                    return f'{months} day{self.pluralize_words(months)} ago'
                
                elif months >= 12:
                    years =math.floor( months / 12)
                    if years > 0:
                        return self.published_date("%d %b, %Y")
            
    def pluralize_words(self, num):
        if num > 1:
            return 's'
        else:
            return ''

    def __str__(self):
        return self.author.username + ' ' + self.title


class Comment(models.Model):
    author = models.ForeignKey(User, on_delete= models.CASCADE, related_name = 'user_comments')
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add =True)

class Bookmark(models.Model):
    user = models.OneToOneField(User, on_delete = models.CASCADE , related_name = 'bookmark_user')
    blogPost = models.ManyToManyField(BlogPost, related_name = 'bookmark_post', blank = True)

    def __str__(self):
        return self.user.username
    

def IncrementLike(sender,instance, action, *args,**kwargs):
    if action in ['post_add', 'post_remove','post_clear']:
        if kwargs.get('reverse') == False:
            count = instance.liked_by.all().count()
            BlogPost.objects.filter(id = instance.id).update(likes = count)
        
        elif kwargs.get('reverse') == True:
            for id_set in kwargs.get('pk_set'):     
                inst = BlogPost.objects.get(id = id_set).liked_by.all().count()
                BlogPost.objects.filter(id = id_set).update(likes= inst)
        

        
def IncrementComment(sender,instance, action, *args,**kwargs):
    if action in ['post_add', 'post_remove','post_clear']:
        if kwargs.get('reverse') == False:
            count = instance.comments_by.all().count()
            BlogPost.objects.filter(id = instance.id).update(comments = count)
        elif kwargs.get('reverse') == True:
            for id_set in kwargs.get('pk_set'):
                inst = BlogPost.objects.get(id = id_set).comments_by.all().count()
                BlogPost.objects.filter(id = id_set).update(comments= inst)


def BlogPublished(instance,sender,created, *args,**kwargs):
    if all([instance.published,instance.published_date is None]):
        instance.published_date = timezone.now()
        instance.save()

    if instance.suggested_topic is not None:
        if instance.suggested_topic.approved:
            instance.blog_topic = instance.suggested_topic
            instance.suggested_topic = None
            instance.save()

def TopicApproved(instance, sender,created, *args,**kwargs):
    if instance.approved:
        if instance.suggest.all().exists():
            for posts in instance.suggest.all():
                posts.save()


post_save.connect(BlogPublished, sender= BlogPost)
post_save.connect(TopicApproved, sender = Topic)
m2m_changed.connect(IncrementLike, sender= BlogPost.liked_by.through)
m2m_changed.connect(IncrementComment, sender= BlogPost.comments_by.through)