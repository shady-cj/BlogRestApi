from django.contrib import admin

# Register your models here.
from .models import BlogPost,Topic,Bookmark

admin.site.register(BlogPost)
admin.site.register(Topic)
admin.site.register(Bookmark)

