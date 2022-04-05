from rest_framework.views import APIView 
from rest_framework.response import Response 
from rest_framework import permissions, status
from django.contrib.auth.models import User 
from .serializers import UserSerializer,ProfileSerializer,FollowerSerializer,FollowingSerializer
from .models import Profile 
import random 
import string

class RegisterView(APIView):
    permission_classes =(permissions.AllowAny, )
    
    def post(self,request):
        try:
            data = request.data
            first_name = data.get('first_name').strip()
            last_name = data.get('last_name').strip()
            password = data.get('password')
            if len(password)>= 8:
                username = first_name
                count = 1
                while True:
                    if not User.objects.filter(username= username).exists():
                        user = User.objects.create_user(
                            first_name = first_name ,
                            last_name = last_name,
                            username = username, 
                            password = password 
                        )
                        user.save()

                        if User.objects.filter(username= username).exists():
                            return Response (
                                {'success': 'Account Created Successfully'},
                                status= status.HTTP_201_CREATED
                            )
                        
                        else:
                            return Response (
                                {'error': 'Something went wrong while trying to create account'},
                                status= status.HTTP_500_INTERNAL_SERVER_ERROR
                            )

                        # break
                    else:
                        username = username +'_'+ str(''.join(random.choices(string.ascii_letters, k=count)))
                        count+=1
            else:
                return Response(
                    {'error':'Password must be at least 8 characters in length'},
                    status = status.HTTP_400_BAD_REQUEST

                )


        except Exception as e:
            print('exception for register', e)
            return Response(
                {'error':'Something went wrong when trying to register account'},
                status = status.HTTP_400_BAD_REQUEST
            )

class LoadUserView(APIView):
    def get(self, request,format=None):
        try:
            user =request.user
            profile = Profile.objects.filter(user__id = user.id).prefetch_related('following').first()
            profile = ProfileSerializer(profile)
            return Response(
                {'user':profile.data},
                status = status.HTTP_200_OK
            )
        except Exception as e:
            print(e)
            return Response(
                {
                    'error':'Something went wrong when trying to load user'
                }, status = status.HTTP_400_BAD_REQUEST
            )

class UserProfileFollowInfo(APIView):
    def get(self, request, username=None,f_type=None, format=None):
        if username:
            try:
                user = User.objects.get(username =username)
                if f_type in ['following','followers']:
                    try:
                        if f_type == 'following':
                            prof = Profile.objects.filter(user= user).prefetch_related('following').first()
                            s_data = FollowingSerializer(prof) 
                            return Response({
                                'data':s_data.data
                            }, status = status.HTTP_200_OK)
                        else:
                            s_data = FollowerSerializer(user)
                            return Response({
                                'data':s_data.data
                            },status = status.HTTP_200_OK)
                    except Exception as e:
                        return Response({
                            'error':'Something Went Wrong'
                        })
                        

                else:

                    return Response({
                        'message':'Not Found'
                    },status = status.HTTP_404_NOT_FOUND)
            except User.DoesNotExist:
                return Response({
                    'error':f'No such user with the username {username}'
                }, status = status.HTTP_400_BAD_REQUEST)

        
            
class EditUserProfileApiView(APIView):
    def put(self,request, *args, **kwargs):
        try:
            user = request.user
            data = request.data
            user_info = data.get('user')
            profile_info = data.get('profile')
            user_serializer = UserSerializer(data= user_info, instance = user,partial= True)
            user_serializer.is_valid(raise_exception = True)
            user_serializer.save()
            profile = Profile.objects.get(user = user)
            profile_serializer = ProfileSerializer(data = profile_info, instance = profile,partial=True)
            profile_serializer.is_valid(raise_exception = True)
            profile_serializer.save()
            return Response({
                'message':'Profile Updated Succesfully',
                'data':profile_serializer.data
            },status = status.HTTP_200_OK)
        except Exception as e:
            print(e)
            return Response({
                'error':'something went wrong'
            }, status = status.HTTP_400_BAD_REQUEST)