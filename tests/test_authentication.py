from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase

from .utils import create_user


class TestAuthentication(APITestCase):

    def test_unauthenticated_user_cant_access_api(self):
        """
        Test that every endpoint will raise HTTP 401 UNAUTHORIZED
        if user is not authenticated.
        """

        error = {'detail': 'Authentication credentials were not provided.'}

        # will reverse to /api/users/
        response = self.client.get(reverse('api:user-list'))
        self.assertEqual(response.data, error)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # will reverse to /api/users/username
        response = self.client.get(
            reverse('api:user-detail', args=['username'])
        )
        self.assertEqual(response.data, error)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # will reverse to /api/users/
        response = self.client.post(reverse('api:user-list'),
                                    data={'something': 'something'})
        self.assertEqual(response.data, error)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

         # will reverse to /api/users/username
        response = self.client.patch(
            reverse('api:user-detail', args=['username']),
            data={'is_active': False}
        )
        self.assertEqual(response.data, error)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # will reverse to /api/users/username/groups
        response = self.client.get(
            reverse('api:user-groups', kwargs={'username': 'username'})
        )
        self.assertEqual(response.data, error)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # will reverse to /api/users/search
        response = self.client.get(reverse('api:search'))
        self.assertEqual(response.data, error)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # will reverse to /api/groups/
        response = self.client.get(reverse('api:group-list'))
        self.assertEqual(response.data, error)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # will reverse to /api/groups/group-name/
        response = self.client.get(
            reverse('api:group-detail', args=['group-name'])
        )
        self.assertEqual(response.data, error)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


    def test_user_can_obtain_auth_keys_using_get_request_to_auth_view(self):
        """
        Test that user can get Token accessing built-in view if existing
        credentials provided.
        """
        username = 'JohnSuper'
        password = 'John1234567890'  # Weak password, John.
        john = create_user(username=username, password=password)
        response = self.client.post('/api-auth/',
                                    data={'username': username,
                                          'password': password}
                                   )
        token = response.data.get('token')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotEqual(token, None)
        self.assertEqual(token, john.auth_token.key)
        response = self.client.post('/api-auth/',
                                    data={'username': username,
                                          'password': 'somewrongpass'}
                                   )
        error = {
            'non_field_errors': ['Unable to log in with provided credentials.']
        }
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, error)
        print(hello)
