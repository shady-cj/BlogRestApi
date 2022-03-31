from django.shortcuts import render
from .models import BlogPost,Bookmark,Topic,Comment
from blogUsers.models import Profile
from django.contrib.auth.models import User
from blogUsers.serializers import ProfileSerializer
from .serializers import ListBlogPostSerializer,BookmarkSerializer,TopicSerializer,DetailBlogPostSerializer,CommentSerializer,BlogPostCommentSerializer,BlogPostLikeSerializer,BookmarkSerializer
from rest_framework.generics import RetrieveUpdateAPIView,CreateAPIView,ListAPIView
from rest_framework.views import APIView
import json
from rest_framework.response import Response
# from rest_framework.decorators import action
from rest_framework.viewsets import ModelViewSet
from rest_framework import permissions,exceptions,status
from django.db import transaction

class ListBlogPostViewset(ModelViewSet):
    serializer_class = ListBlogPostSerializer
    queryset = BlogPost.objects.filter(trashed =False,published=True,blog_topic__approved=True).select_related('author','blog_topic')

    def get_queryset(self):
        super().get_queryset()
        search_params = self.request.query_params.get('filter')
        user = self.request.user

        if search_params in ['all','recommended','following']:
            if search_params == 'all':
                return BlogPost.objects.filter(trashed =False,published=True, blog_topic__approved = True).select_related('author','blog_topic')
            elif search_params == 'recommended':
                get_user_topics = user.following_topics.all()
                # get_user_post_views = user.viewed_posts.all()
                # topic_lists = get_user_topics + get_user_post_views
                return BlogPost.objects.filter(blog_topic__in = get_user_topics, trashed =False,published=True, blog_topic__approved =True).select_related('author','blog_topic')
            elif search_params == 'following':
                try:
                    user = self.request.user
                    p = Profile.objects.filter(user= user).prefetch_related('following').first()
                    following = p.following.all()
                    return BlogPost.objects.filter(author__in = following,trashed =False,published=True, blog_topic__approved =True).select_related('author','blog_topic')
                except Exception as e:
                    print(e)
                    raise exceptions.NotFound(e)
        
                
        
        else:
            return BlogPost.objects.filter(trashed =False,published=True, blog_topic__approved=True).select_related('author','blog_topic')
    


    
class ListBookmarkPostViewSet(ModelViewSet):
    serializer_class = BookmarkSerializer
    queryset = Bookmark.objects.all()

    def get_queryset(self):
        super().get_queryset()
        user = self.request.user
        search_params = self.request.query_params.get('filter')

        if search_params is None:
            return Bookmark.objects.filter(user = user).prefetch_related('blogPost')

        if search_params in ['saved', 'recent']:
            if search_params == 'saved':
                return Bookmark.objects.filter(user = user).prefetch_related('blogPost')
            else:
                pass
            # Implement recenty viewed posts by the user.
        else:
            raise exceptions.NotFound('Invalid search parameter')

        





class ListTopicsViewSet(ModelViewSet):
    serializer_class = TopicSerializer
    queryset = Topic.objects.filter(approved=True)


class ListTopicsPostAPIView(ListAPIView):
    serializer_class = ListBlogPostSerializer
    queryset = BlogPost.objects.filter(trashed =False,published=True).select_related('author','blog_topic')

    def get_queryset(self):
        super().get_queryset()
        topic_name= self.kwargs.get('topic')
        topic = Topic.objects.filter(name__iexact=topic_name, approved=True)
        if topic.exists() and topic.count() == 1:
            blogpost = BlogPost.objects.filter(blog_topic = topic.first(),trashed =False,published=True).select_related('author','blog_topic')
            return blogpost
        else:
            return None
        


class CreateBlogPostAPIView(CreateAPIView):
    serializer_class = DetailBlogPostSerializer

    
    def perform_create(self,serializer):
        
        topic_name = self.request.data.get('topic_name')

        try:
            # check if topic is already exists
            with transaction.atomic():
                t = Topic.objects.filter(name__iexact = topic_name)
                if t.exists():
                    topic = t.first()

                    if topic.approved:
                        serializer.save(author=self.request.user,blog_topic = topic )
                    else:
                        serializer.save(author.self.request.user, suggested_topic=topic)

                else:
                    topic_img = self.request.data.get('topic_img')
                    topic = Topic.objects.create(name = topic_name)
                    if topic_img is not None:
                        topic = Topic.objects.create(name = topic_name,image= topic_img)
                    serializer.save(author=self.request.user,suggested_topic=topic)

                # if not topic
        except Exception as e:
            print(e)
            raise exceptions.NotFound("Something Went Wrong")

class RetrieveBlogPostAPIView(RetrieveUpdateAPIView):
    serializer_class = DetailBlogPostSerializer
    queryset = BlogPost.objects.all().select_related('author','blog_topic').prefetch_related('liked_by','comments_by')

    def perform_update(self, serializer):
        get_id = self.kwargs.get('pk')

        b= BlogPost.objects.get(id = get_id)
        if b.author == self.request.user:
            if b.trashed:
                raise exceptions.NotFound('Article has already been Trashed by you')
            serializer.save()
        else:
            raise exceptions.PermissionDenied('You are not the author of this Blog Post')
    def retrieve(self, request, *args, **kwargs):
        get_id = self.kwargs.get('pk')
        b = BlogPost.objects.get(id= get_id)
        if b.author != self.request.user:
            if any([b.trashed == True, b.published== False]):
                return Response({"error":"This post is not available"},status = status.HTTP_403_FORBIDDEN)


        return super().retrieve(request,*args, **kwargs)



class ListUserStoryAPIView(ListAPIView):
    serializer_class = ListBlogPostSerializer
    queryset = BlogPost.objects.filter(trashed=False,published=True).select_related('author','blog_topic')

    def get_queryset(self):
        super().get_queryset()
        story_type = self.kwargs.get('story_type')
        if story_type == 'published':
            return BlogPost.objects.filter(trashed=False,published=True,author = self.request.user).select_related('author','blog_topic')
        elif story_type == 'drafts':
            return BlogPost.objects.filter(trashed=False,published=False,author = self.request.user).select_related('author','blog_topic')
        elif story_type == 'trash':
            return BlogPost.objects.filter(trashed=True,author= self.request.user).select_related('author','blog_topic')
            


class ActionApiView(APIView):
    def post(self, request, action_type=None, *args, **kwargs):
        if action_type == None:
            return Response({
                'error':'Invalid action type'
            },status = status.HTTP_400_BAD_REQUEST)
        
        else:
            payload = request.data

            if action_type == 'like':
                try:
                    post_id = payload.get('post_id')
                    action = payload.get('action')
                    blogpost = BlogPost.objects.get(id =int(post_id))
                    if action == 'like':
                        blogpost.liked_by.add(request.user)
                    elif action == 'unlike':
                        blogpost.liked_by.remove(request.user)
                    
                    else:
                        return Response({
                            'error':'Something Went Wrong'
                        },status = status.HTTP_400_BAD-REQUEST)
                    # serializer = BlogPostLikeSerializer(BlogPost.objects.filter(id = int(post_id)).prefetch_related('liked_by').first())
                    like_count= BlogPost.objects.get(id=int(post_id)).likes
                    return Response({
                        'message':f"{action} successful",
                        'data':like_count
                    }, status= status.HTTP_200_OK)
                except Exception as e:
                    raise exceptions.PermissionDenied(f'Something went wrong Traceback {e}')

            elif action_type == 'bookmark':
                try:
                    post_id = payload.get('post_id')
                    action = payload.get('action')
                    blogPost = BlogPost.objects.get(id = int(post_id))
                    bookmark_user = Bookmark.objects.get(user = request.user)
                    if action == 'add':
                        bookmark_user.blogPost.add(blogPost)
                        message = 'Article Added To Your Bookmark'
                    elif action == 'remove':
                        bookmark_user.blogPost.remove(blogPost)
                        message = 'Article Removed From Your Bookmark'
                    else:
                        return Response({'error':'Invalid Action'}, status = status.HTTP_400_BAD_REQUEST)
                    

                    return Response({'message':message}, status = status.HTTP_200_OK)



                except Exception as e:
                    raise exceptions.PermissionDenied(f'Something went wrong Traceback {e}')

            elif action_type == 'comments':
                try:
                    post_id = payload.get('post_id')
                    comment_data = payload.get('comment')
                    serialized_comment = CommentSerializer(data= comment_data)
                    serialized_comment.is_valid(raise_exception=True)
                    serialized_comment.validated_data['author'] = request.user
                    serialized_comment.save()
                    get_comment_id = serialized_comment.data.get('id')
                    comment_inst = Comment.objects.get(id = int(get_comment_id))
                    b = BlogPost.objects.get(id = int(post_id))
                    b.comments_by.add(comment_inst)
                    serializer = BlogPostCommentSerializer(BlogPost.objects.filter(id = int(post_id)).prefetch_related('comments_by').first())
                    return Response({
                        'message':'comments made successfully',
                        'data':serializer.data
            
                    },status= status.HTTP_200_OK)
                except Exception as e:
                    raise exceptions.PermissionDenied(f'Something went wrong Traceback {e}')

            elif action_type == 'follow':
                try:
                    user_id = payload.get('user_id')
                    action = payload.get('action')
                    get_user = User.objects.filter(id = int(user_id)).prefetch_related('followers').first()
                    auth_user_profile = Profile.objects.get(user = request.user)
                    if action == 'follow':
                        if auth_user_profile not in get_user.followers.all():
                            auth_user_profile.following.add(get_user)
                            # serializer = ProfileSerializer(Profile.objects.filter(user = request.user).select_related('user').first())
                            return Response({
                                'message':'Follow Successful'
                                # 'data':serializer.data
                                
                            },status = status.HTTP_200_OK )
                        else:
                            return Response({
                                'error':f'User is already Following'
                            },status = status.HTTP_400_BAD_REQUEST )
                        
                    elif action == 'unfollow':
                        if auth_user_profile in get_user.followers.all():
                            auth_user_profile.following.remove(get_user)
                            # serializer = ProfileSerializer(Profile.objects.filter(user = request.user).select_related('user').first())
                            return Response({
                                'message':'Unfollow Successful'
                                # 'data':serializer.data
                                
                            },status = status.HTTP_200_OK )
                        else:
                            return Response({
                                'error':f'User is not already Following'
                            },status = status.HTTP_400_BAD_REQUEST)

                except Exception as e:
                    raise exceptions.PermissionDenied(f'Something went wrong Traceback {e}')



    
