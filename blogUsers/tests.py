from django.test import TestCase
from rest_framework.test import APITestCase
from django.urls import reverse
from rest_framework import status
import json
from django.db import IntegrityError
from .models import Profile
from django.contrib.auth.models import User 
# Create your tests here.


class TestUserModel(APITestCase):
    def setUp(self):
        # Setting up test users 
        user1 = User.objects.create_user(username='ceejay', email='ceejay@yahoo.com', password='test123')
        user2 = User.objects.create_user(username='shady', email='shady@yahoo.com', password='test123')
    
    def test_user_model(self):
        # Testing to check if the users created in the setup functions were created
        qs = User.objects.all()
        self.assertEqual(qs.count(), 2)
        self.assertTrue(qs.filter(username='shady').exists())
    def test_user_model_integrity(self):
        with self.assertRaises(IntegrityError) as E:
            user3 = User.objects.create_user(username='ceejay',email='haha@gmail.com',password='jajfhg')

class TestProfileModel(APITestCase):
    def setUp(self):
        # Setting up test users and profile 
        self.user1 = User.objects.create_user(username='ceejay', email='ceejay@yahoo.com', password='test123')
        self.user2 = User.objects.create_user(username='shady', email='shady@yahoo.com', password='test123')

    def test_profile_was_created_for_each_user(self):
        # Checking if a profile was created for users that were created
        profile1 = Profile.objects.filter(user = self.user1)
        profile2 = Profile.objects.filter(user= self.user2)
        self.assertEqual(Profile.objects.all().count(),User.objects.all().count())
        self.assertTrue(profile1.exists())
        self.assertTrue(profile2.exists())
    def test_if_default_profile_picture_was_created(self):
        profile1 = Profile.objects.get(user= self.user1)
        self.assertTrue(bool(profile1.profile_picture))
    
class TestUserRegistrationView(APITestCase):
    def setUp(self):
        self.client.credentials(HTTP_ACCEPT='application/json')

    def test_user_creation_successfully(self):

        # Hitting the registration view endpoint with the necessary credentials but without username 

        response = self.client.post(reverse('register'), json.dumps({'first_name':'Peter', 'last_name':'Erinfolami', 'password':'shady123','re_password':'shady123'}), content_type='application/json')
        # expecting to get "Peter" as my username

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        users = User.objects.all()
        self.assertEqual(users.count(), 1)
        self.assertEqual(users.first().username, 'Peter')

    def test_users_creation_with_same_first_name(self):
        user1 =self.client.post(reverse('register'), json.dumps({'first_name':'Peter', 'last_name':'Erinfolami', 'password':'shady123','re_password':'shady123'}), content_type='application/json')
        user2 = self.client.post(reverse('register'), json.dumps({'first_name':'Peter', 'last_name':'Ceejay', 'password':'shady123','re_password':'shady123'}), content_type='application/json')
        user3 = self.client.post(reverse('register'), json.dumps({'first_name':'Peter', 'last_name':'Jon', 'password':'shady123','re_password':'shady123'}), content_type='application/json')

        self.assertEqual(user1.status_code, status.HTTP_201_CREATED)
        self.assertEqual(user2.status_code, status.HTTP_201_CREATED)
        self.assertEqual(user3.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.all().count(), 3)
        self.assertEqual(User.objects.filter(first_name='Peter').count(), 3)
        self.assertNotEqual(User.objects.filter(first_name='Peter').first().username, User.objects.filter(first_name='Peter').last().username)
        
    
    def test_user_creation_fail_due_to_inconsistent_password(self):
        # Hitting the registration endpoint with passwords that does not match
        response = self.client.post(reverse('register'), json.dumps({'first_name':'Peter', 'last_name':'Erinfolami', 'username':'shady', 'password':'shady123', 're_password':'shady11'}), content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_creation_fail_due_to_short_password(self):
        # Hitting the registration endpoint with passwords length that is less than 8 characters
        response = self.client.post(reverse('register'), json.dumps({'first_name':'Peter', 'last_name':'Erinfolami', 'username':'shady', 'password':'shady', 're_password':'shady'}), content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data.get('error'), 'Password must be at least 8 characters in length')


class TestLoadUser(APITestCase):

    def setUp(self):
        self.client.post(reverse('register'), json.dumps({'first_name':'Peter', 'last_name':'Erinfolami','password':'shady123', 're_password':'shady123'}), content_type='application/json',HTTP_ACCEPT='application/json')
    def test_load_user_with_no_authorization(self):

        # Hitting the load user endpoint with no token authorization
        response = self.client.get(reverse('user'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_load_user_without_providing_credentials_while_retrieving_access_token(self):
        # User tries to receive access token without credentials
        resp = self.client.post('/api/token/',{},content_type='application/json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_load_user_with_necessary_credentials(self):
        # User retrieves access token with the necessary credentials and also retrieve the user information data
        # Also the username by default should be the first name of the user 
        respToken = self.client.post('/api/token/', json.dumps({'username':'Peter','password':'shady123'}),content_type='application/json')
        self.assertEqual(respToken.status_code, status.HTTP_200_OK)
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + respToken.data.get('access'))
        response = self.client.get(reverse('user'))

        self.assertEqual(response.status_code,status.HTTP_200_OK )
        self.assertEqual(response.data['user'].get('user').get('username'), 'Peter')

    def test_get_new_access_token(self):
        respToken = self.client.post('/api/token/', json.dumps({'username':'Peter','password':'shady123'}),content_type='application/json')
        refToken = respToken.data.get('refresh')
        response = self.client.post('/api/token/refresh/',json.dumps({'refresh':refToken}),content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, dict)
        self.assertIn('access', response.data.keys())
    
    def test_verify_access_token(self):
        respToken = self.client.post('/api/token/', json.dumps({'username':'Peter','password':'shady123'}),content_type='application/json')
        accToken = respToken.data.get('access')
        response = self.client.post('/api/token/verify/',json.dumps({'token':accToken}),content_type='application/json')
    
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class TestUserFollowInfoRoute(APITestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username='ceejay', email='ceejay@yahoo.com', password='test123')
        self.user2 = User.objects.create_user(username='shady', email='shady@yahoo.com', password='test123')
    
    def test_following_users_route(self):
        # Obtaining access token 
        respToken = self.client.post('/api/token/', json.dumps({'username':'shady','password':'test123'}),content_type='application/json')
        # Setting header credentials 
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + respToken.data.get('access'),HTTP_ACCEPT='application/json',content_type='application/json' )

        p = Profile.objects.get(user = self.user1)
        p.following.add(self.user2)
        resp = self.client.get(reverse('follow_info',args=(self.user1.username,'following')))

        
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data.get('data').get('following')),1)
        self.assertEqual(resp.data.get('data').get('following')[0].get('username'), self.user2.username)
        
    def test_followers_users_route(self):
        respToken = self.client.post('/api/token/', json.dumps({'username':'shady','password':'test123'}),content_type='application/json')
        # Setting header credentials 
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + respToken.data.get('access'),HTTP_ACCEPT='application/json',content_type='application/json' )

        p = Profile.objects.get(user = self.user1)
        p.following.add(self.user2)
        resp = self.client.get(reverse('follow_info',args=(self.user2.username,'followers')))

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data.get('data').get('followers')),1)
        self.assertEqual(resp.data.get('data').get('followers')[0].get('username'), self.user1.username)
        

class TestProfileEdit(APITestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username='ceejay', email='ceejay@yahoo.com', password='test123')
    def test_profile_update_without_authentication(self):
        res = self.client.put(reverse('update_profile'), json.dumps({'user':{}, 'profile':{}}),content_type='application/json')
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)
    def test_profile_update_with_authentication(self):
        respToken = self.client.post('/api/token/', json.dumps({'username':'ceejay','password':'test123'}),content_type='application/json')
        # Setting header credentials 
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + respToken.data.get('access'),HTTP_ACCEPT='application/json',content_type='application/json' )
        res = self.client.put(reverse('update_profile'), json.dumps({'user':{'username':'shady','first_name':'Peter','last_name':'Erinfolami'}, 'profile':{}}),content_type='application/json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        user = User.objects.get(id = self.user1.id)
        self.assertEqual(user.username, 'shady')
        self.assertEqual(user.first_name, 'Peter')
        self.assertEqual(user.last_name, 'Erinfolami')
        
