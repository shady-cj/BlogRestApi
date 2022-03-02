from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Comment, BlogPost,Bookmark,Topic

class BlogUserModelSerializer(serializers.ModelSerializer):
    profile = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'first_name',
            'last_name',
            'profile'
        ]
        
    def get_profile(self,obj):
        
        return obj.profile.profile_picture.url

class CommentSerializer(serializers.ModelSerializer):
    author = BlogUserModelSerializer(required=False)
    timestamp = serializers.DateTimeField(read_only=True)
    class Meta:
        model = Comment
        fields = "__all__"

class TopicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Topic
        fields = "__all__"

class BlogPostCommentSerializer(serializers.ModelSerializer):
    comments_by = CommentSerializer(many = True,read_only = True)
    class Meta:
        model = BlogPost
        fields = [
            'id',
            'comments_by',
            'comments'
        ]
class BlogPostLikeSerializer(serializers.ModelSerializer):
    liked_by = BlogUserModelSerializer(many = True, read_only = True)
    class Meta:
        model = BlogPost
        fields = [
            'id',
            'likes',
            'liked_by'
        ]
class DetailBlogPostSerializer(serializers.ModelSerializer):
    created_at = serializers.DateTimeField(read_only= True)
    updated_at = serializers.DateTimeField(read_only =True)
    published_date = serializers.DateTimeField(read_only =True)
    format_published_date = serializers.CharField(read_only=True)
    comments_by = CommentSerializer(many =True, read_only =True)
    liked_by = BlogUserModelSerializer(many =True, read_only = True)
    blog_topic = TopicSerializer(required=False)
    suggested_topic =TopicSerializer(required=False)
    author = BlogUserModelSerializer(required=False)
    class Meta:
        model = BlogPost
        fields = '__all__'



class ListBlogPostSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    author = serializers.SerializerMethodField()
    title = serializers.CharField()
    content = serializers.CharField()
    published= serializers.BooleanField()
    published_date = serializers.DateTimeField()
    cover_photo = serializers.ImageField(allow_empty_file = True)
    published_period = serializers.CharField()
    featured = serializers.BooleanField()
    likes = serializers.IntegerField()
    comments = serializers.IntegerField()
    blog_topic = serializers.SerializerMethodField()

    def get_blog_topic(self,obj):
        blog = getattr(obj, 'blog_topic', None)
        if blog is not None:
            return obj.blog_topic.name

    def get_author(self,obj):
        auth = obj.author
        profile = auth.profile
        return {
            'id':auth.id,
            'first_name':auth.first_name, 
            'last_name':auth.last_name,
            'username':auth.username,
            'pics':profile.profile_picture.url

        }

class BookmarkSerializer(serializers.ModelSerializer):
    blogPost = ListBlogPostSerializer(many= True,read_only= True)
    class Meta:
        model = Bookmark
        fields =[
            'blogPost'
        ]


