from django.db import models
from django.contrib.auth.models import User
from Blog.models import Bookmark
from django.db.models.signals import post_save

# class Notifications(models.Model):
#     events = models.CharField()
#     d

def path_file_name(instance, filename):
    return '/'.join(filter(None, ('profile', instance.user.username, filename)))


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete= models.CASCADE)
    profile_picture = models.ImageField(upload_to=path_file_name,default='/profile/user_akbm7u.png',null=True, blank=True)
    about = models.TextField()
    following = models.ManyToManyField(User,related_name='followers',blank=True)

    def __str__(self):

        return self.user.username



def CreateProfile(instance, sender, created, *args, **kwargs):
    if created:
        Profile.objects.create(user = instance)
        Bookmark.objects.create(user = instance)
   
def SetDefaultProfPicture(instance, sender,created, *args,**kwargs):
    if bool(instance.profile_picture) is False:
        instance.profile_picture = '/profile/user_akbm7u.png'
        instance.save()

post_save.connect(CreateProfile, sender= User)
post_save.connect(SetDefaultProfPicture,sender=Profile)