
from .views import (
    ListBlogPostViewset,
    ListBookmarkPostViewSet,
    ListTopicsViewSet,
    ListTopicsPostAPIView,
    CreateBlogPostAPIView,
    RetrieveBlogPostAPIView,
    ListUserStoryAPIView,
    ActionApiView
    )
from rest_framework.routers import DefaultRouter
from django.urls import path, include

router = DefaultRouter()
router.register('feed', ListBlogPostViewset)
router.register('bookmarks',ListBookmarkPostViewSet)
router.register('topic', ListTopicsViewSet)



urlpatterns = [
    path('blogs/', include(router.urls)),
    path('create-article',CreateBlogPostAPIView.as_view(),name='create-article'),
    path('detail/<int:pk>',RetrieveBlogPostAPIView.as_view(),name='retrieve-update'),
    path('story/<str:story_type>',ListUserStoryAPIView.as_view(), name ='story'),
    path('topic/<str:topic>',ListTopicsPostAPIView.as_view(), name ='topic'),
    path('activities/<str:action_type>',ActionApiView.as_view(),name= 'activities')
]