from django.test import TestCase
from rest_framework.test import APITestCase
from django.urls import reverse
from rest_framework import status
import json

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

class TestUserRegistrationView(APITestCase):
    def setUp(self):
        self.client.credentials(HTTP_ACCEPT='application/json')

    def test_user_creation_successfully(self):

        # Hitting the registration view endpoint with the necessary credentials 

        response = self.client.post(reverse('register'), json.dumps({'first_name':'Peter', 'last_name':'Erinfolami', 'username':'shady', 'password':'shady123','re_password':'shady123'}), content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        users = User.objects.all()
        self.assertEqual(users.count(), 1)

    
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
        self.client.post(reverse('register'), json.dumps({'first_name':'Peter', 'last_name':'Erinfolami', 'username':'shady', 'password':'shady123', 're_password':'shady123'}), content_type='application/json',HTTP_ACCEPT='application/json')
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
        respToken = self.client.post('/api/token/', json.dumps({'username':'shady','password':'shady123'}),content_type='application/json')
        self.assertEqual(respToken.status_code, status.HTTP_200_OK)
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + respToken.data.get('access'))
        response = self.client.get(reverse('user'))

        self.assertEqual(response.status_code,status.HTTP_200_OK )
        self.assertEqual(response.data.get('user').get('username'), 'shady')

    def test_get_new_access_token(self):
        respToken = self.client.post('/api/token/', json.dumps({'username':'shady','password':'shady123'}),content_type='application/json')
        refToken = respToken.data.get('refresh')
        response = self.client.post('/api/token/refresh/',json.dumps({'refresh':refToken}),content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, dict)
        self.assertIn('access', response.data.keys())
    
    def test_verify_access_token(self):
        respToken = self.client.post('/api/token/', json.dumps({'username':'shady','password':'shady123'}),content_type='application/json')
        accToken = respToken.data.get('access')
        response = self.client.post('/api/token/verify/',json.dumps({'token':accToken}),content_type='application/json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)






