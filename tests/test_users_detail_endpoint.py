import json
from functools import partial

from django.urls import reverse

from rest_framework import status
from rest_framework.renderers import JSONRenderer
from rest_framework.test import APIRequestFactory, APITestCase

from profiles.models import User
from profiles.serializers import UserSerializer

from .utils import CreateUsersMixin, create_user


class TestUserDetailEndPoint(CreateUsersMixin, APITestCase):
    """Test that user details endpoint acts as expected"""

    def setUp(self):
        super().setUp()

        # Dummy requests that needed for our UserSerializer.
        self.request = APIRequestFactory().post('/something/')
        self.safe_request = APIRequestFactory().get('/something/')
        self.url = partial(reverse, 'api:user-detail') 

    def test_get_request_returns_full_user_details_for_admin(self):
        """Test that view returns full user data for admin user"""
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.admin_user.auth_token.key
        )

        self.safe_request.user = self.admin_user
        serializer = UserSerializer(self.admin_user,
                                    context={'request': self.safe_request})

        response = self.client.get(self.url(args=[self.admin_user.username]))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_get_request_returns_partial_user_details_for_regular_user(self):
        """Test that view returns partial user data for regular user"""
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.regular_user.auth_token.key
        )

        self.safe_request.user = self.regular_user
        serializer = UserSerializer(self.admin_user,
                                    context={'request': self.safe_request})

        response = self.client.get(self.url(args=[self.admin_user.username]))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_put_request_replaces_user(self):
        """Test that PUT request will completely replace user"""
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.admin_user.auth_token.key
        )
        # To easily create payload we render existing user to json and parse
        # it to Python types, then we will modify it.
        # Serialized Fields using UserSerializer as basic user:
        # first_name, last_name, username, email, birthday, address
        # We need to add is_active, password, fields and modify
        # some existing fields.
        # Using regular user as context to reduce ammount of fields to override.
        self.request.user = self.regular_user
        serialized_data = UserSerializer(
            self.regular_user, context={'request': self.request}
        ).data

        json_data = JSONRenderer().render(serialized_data)

        payload = json.loads(json_data.decode('utf-8'))
        payload.update({'is_active': True, 'password': 'mynewpassword',
                        'username': 'Elena', 'email': 'some@some.com'})

        response = self.client.put(self.url(args=[self.regular_user.username]),
                                   data=payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Reloading user from database to check if changes was applied to user.
        self.regular_user.refresh_from_db()

        # Replacing user on request because after PUT request view should
        # return data that serialzied for admin user. 
        self.request.user = self.admin_user
        serializer = UserSerializer(
            self.regular_user, context={'request': self.request}
        )
        self.assertEqual(response.data, serializer.data)
        # Check that password was successfully hashed.
        self.assertTrue(self.regular_user.check_password('mynewpassword'))

    def test_patch_request_allows_partialy_update_user(self):
        """Test partial update works as expected"""
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.admin_user.auth_token.key
        )
        payload = {'email': 'some@some.com', 'address': {'city': 'Кстово'}}
        # Saving original data here to check presence of all fields after
        # update.
        self.request.user = self.admin_user
        original_data = UserSerializer(
            self.regular_user, context={'request': self.request}
        ).data

        response = self.client.patch(self.url(args=[self.regular_user.username]),
                                     data=payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Reloading user from database to check if changes was applied to user.
        # Not using .refresh_from_db() method because we have changed
        # related object that will not be refreshed using this method.
        updated_user = User.objects.get(pk=self.regular_user.pk)
        serializer = UserSerializer(updated_user,
                                    context={'request': self.request})
        self.assertEqual(response.data, serializer.data)
        # Change original data to expected data after update and
        # check that all other fields is still presist on model.
        original_data['address']['city'] = 'Кстово'
        original_data['email'] = 'some@some.com'
        self.assertEqual(original_data, response.data)

    def test_admin_cant_change_inactive_user_state(self):
        """Test that admins can't edit user if user is inactive"""
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.admin_user.auth_token.key
        )
        user = create_user('Dmitriy', 'dmitriy@email.com', is_active=False)
        error = {
            'detail':
            'Editing inactive user state is not allowed. Activate user first'
        }
        payload = {'email': 'newemail@mail.com'}
        response = self.client.patch(self.url(args=[user.username]),
                                     data=payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data, error)

    def test_admin_can_change_inactive_user_status_to_active(self):
        """Test that admin can change inactive user status to active"""
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.admin_user.auth_token.key
        )
        user = create_user('Dmitriy', 'dmitriy@email.com', is_active=False)
        payload = {'is_active': True, 'email': 'newemail@mail.com'}
        response = self.client.patch(self.url(args=[user.username]),
                                     data=payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user.refresh_from_db()
        self.assertEqual(user.is_active, True)
        self.assertEqual(user.email, 'newemail@mail.com')

    def test_admins_cant_change_superuser_state(self):
        """Test that only superusers can edit superusers data"""
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.admin_user.auth_token.key
        )
        user = create_user('Dmitriy', 'dmitriy@email.com', is_superuser=True)
        payload = {'password': 'newpassword'}
        error = {'detail': 'You can\'t edit this user data'}
        response = self.client.patch(self.url(args=[user.username]),
                                     data=payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data, error)

    def test_invalid_address_data_will_cause_error_on_updating(self):
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.admin_user.auth_token.key
        )
        payload = {'address': {'city': 'i' * 129}, 'username': 'NewName'}
        error = {
            'address': {
                'city': [
                    'Ensure this field has no more than 128 characters.'
                ]
            }
        }
        response = self.client.patch(self.url(args=[self.regular_user.username]),
                                     data=payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, error)
        # Refecth user to make sure address and other data didn't changed
        user = User.objects.get(pk=self.regular_user.pk)
        self.assertNotEqual(user.username, 'NewName')
        self.assertNotEqual(user.address.city, 'i' * 129)

