from django.urls import path 

from .views import RegisterView,LoadUserView

urlpatterns = [
    path('register',RegisterView.as_view(), name= 'register'),
    path('user', LoadUserView.as_view(), name= 'user')
]
