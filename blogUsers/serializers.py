from rest_framework import serializers 
from django.contrib.auth.models import User 

from .models import Profile

# class FollowerSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = profile

class UserSerializer(serializers.ModelSerializer):
    followers = serializers.SerializerMethodField()
    

    class Meta:
        model = User
        fields = [
            'id',
            'first_name',
            'last_name', 
            'username',
            'followers'
            
        ]
        read_only_fields = ['id','followers']
    def get_followers(self, obj):
        followers_list = []

        for u in obj.followers.all():
            followers_list.append(u.user.id)
        
        return followers_list



    # def get_followers(self, obj):
       
    #     followers_list = []
    #     for u in obj.followers.all():
    #         followerInfo = {
    #                 "id":u.user.id,
    #                 "username":u.user.username,
    #                 "first_name":u.user.first_name,
    #                 "last_name":u.user.last_name,
    #                 "profile_picture":u.profile_picture.url
    #             }
    #         followers_list.append(followerInfo)
    #     return followers_list
        

class ProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only =True)
    # following = UserSerializer(many= True)
    class Meta:
        model = Profile
        fields =[
            'user',
            'profile_picture',
            'about',
            'following'

        ]
       
class FollowingSerializer(serializers.Serializer):
    following = serializers.SerializerMethodField()

    def get_following(self, obj):
        following = obj.following.all()
        following_list = []
        for f in following:
            f_obj = {
                'id':f.id,
                'first_name':f.first_name,
                'last_name':f.last_name,
                'username':f.username,
                'profile_picture':f.profile.profile_picture.url,

            }
            following_list.append(f_obj)

        return following_list

class FollowerSerializer(serializers.Serializer):
    followers = serializers.SerializerMethodField()
    
    def get_followers(self, obj):
        followers = obj.followers.all()
        followers_list = []
        for f in followers:
            f_obj = {
                'id':f.user.id,
                'first_name':f.user.first_name,
                'last_name':f.user.last_name,
                'username':f.user.username, 
                'profile_picture':f.profile_picture.url
            }
            followers_list.append(f_obj)

        return followers_list
