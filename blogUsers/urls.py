from django.urls import path 

from .views import RegisterView,LoadUserView,UserProfileFollowInfo,EditUserProfileApiView

urlpatterns = [
    path('register',RegisterView.as_view(), name= 'register'),
    path('user', LoadUserView.as_view(), name= 'user'),
    path('profile/<str:username>/<str:f_type>',UserProfileFollowInfo.as_view(),name='follow_info'),
    path('profile/update', EditUserProfileApiView.as_view(), name= 'update_profile')
]
