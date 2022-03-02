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

class ListBlogPostViewset(ModelViewSet):
    serializer_class = ListBlogPostSerializer
    queryset = BlogPost.objects.filter(trashed =False,published=True).select_related('author','blog_topic')

    def get_queryset(self):
        super().get_queryset()
        search_params = self.request.query_params.get('filter')
        topic_search_params = self.request.query_params.get('topic')

        if search_params in ['all','featured','following']:
            if search_params == 'all':
                return BlogPost.objects.filter(trashed =False,published=True).select_related('author','blog_topic')
            elif search_params == 'featured':
                return BlogPost.objects.filter(featured = True,trashed =False,published=True).select_related('author','blog_topic')
            elif search_params == 'following':
                try:
                    user = self.request.user
                    p = Profile.objects.filter(user= user).prefetch_related('following').first()
                    following = p.following.all()
                    return BlogPost.objects.filter(author__in = following,trashed =False,published=True).select_related('author','blog_topic')
                except Exception as e:
                    print(e)
                    raise exceptions.NotFound(e)
        elif topic_search_params is not None:
            try:
                # topic = Topic.objects.filter(name = topic_search_params).prefetch_related('topic').first()

                topic = Topic.objects.get(name = topic_search_params)
                blogpost = BlogPost.objects.filter(blog_topic = topic,trashed =False,published=True).select_related('author','blog_topic')
                return blogpost
            except Topic.DoesNotExist as e:
                print(e)
                raise exceptions.NotFound(e)
                
        
        else:
            return BlogPost.objects.filter(trashed =False,published=True).select_related('author','blog_topic')
    


    
class ListBookmarkPostViewSet(ModelViewSet):
    serializer_class = BookmarkSerializer
    queryset = Bookmark.objects.all()

    def get_queryset(self):
        super().get_queryset()
        user = self.request.user
        
        return Bookmark.objects.filter(user = user).prefetch_related('blogPost')


class ListTopicsViewSet(ModelViewSet):
    serializer_class = TopicSerializer
    queryset = Topic.objects.filter(approved=True)



class CreateBlogPostAPIView(CreateAPIView):
    serializer_class = DetailBlogPostSerializer

    def perform_create(self,serializer):
        topic_name = self.request.data.get('topic_name')
        try:
            # check if topic is already exists
            t = Topic.objects.filter(name__iexact = topic_name)
            if t.exists():

                topic = Topic.objects.filter(name = topic_name, approved =True).first()
                return serializer.save(author=self.request.user,blog_topic = topic )

            else:
                topic = Topic.objects.create(name = topic_name)
                return serializer.save(author=self.request.user,suggested_topic = topic )

            # if not topic
        except Exception as e:
            print(e)
            return None 

class RetrieveBlogPostAPIView(RetrieveUpdateAPIView):
    serializer_class = DetailBlogPostSerializer
    queryset = BlogPost.objects.all().select_related('author','blog_topic').prefetch_related('liked_by','comments_by')

    def perform_update(self, serializer):
        get_id = self.kwargs.get('pk')

        b= BlogPost.objects.get(id = get_id)
        if b.author == self.request.user:
            if b.trashed:
                raise exceptions.NotFound('Article has already been Trashed by you')
            return serializer.save()
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



    
