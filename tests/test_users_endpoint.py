from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase, APIRequestFactory, force_authenticate

from profiles.serializers import UserSerializer
from profiles.models import User

from .utils import CreateUsersMixin, create_user


class TestUserListEndPoint(CreateUsersMixin, APITestCase):

    def setUp(self):
        super().setUp()

        self.payload = {'first_name': 'Sarah',
                        'last_name': 'Chalke', 'username': 'Sarah1234',
                        'password': 'iamsarah',
                        'email': 'sarah@email.com', 'birthday': '1974-08-27',
                        'address':
                            {'zip_code': '782132', 'country': 'Canada',
                             'city': 'Ottawa',
                             'district': 'Ontario',
                             'street': 'LongStreet'
                            },
                       }
        # Dummy requests that needed for our UserSerializer.
        self.request = APIRequestFactory().post('/something/')
        self.safe_request = APIRequestFactory().get('/something/')


    # Because we successfully tested our serializers to return data in
    # format we want, we can rely on it and use it in test assertions

    def test_returns_list_of_users_with_full_data_for_admin(self):
        """Test admin get full serialization of information"""
        # Assign user on request
        self.safe_request.user = self.admin_user

        queryset = User.objects.all()
        serialized_data = UserSerializer(queryset, many=True,
                                         context={'request': self.safe_request})

        # loging in as admin user
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.admin_user.auth_token.key
        )
        response = self.client.get(reverse('api:user-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serialized_data.data)
        # Just little additional check,
        # we actualy tested it in test_serializers.
        # Using index here, because serializer have many=True agrument, and our
        # response.data will be wrapped in list.
        self.assertIn('id', response.data[0])

    def test_returns_list_of_user_with_partial_data_for_basic_users(self):
        """Test regular users get basic serialization of information"""
        # Assign user on request
        self.safe_request.user = self.regular_user

        queryset = User.objects.all()
        serialized_data = UserSerializer(queryset, many=True,
                                         context={'request': self.safe_request})
        # loging in as regular user
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.regular_user.auth_token.key
            )
        response = self.client.get(reverse('api:user-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serialized_data.data)
        # Just little additional check,
        # we actualy tested it in test_serializers.
        # Using index here, because serializer have many=True agrument, and our
        # response.data will be wrapped in list.
        self.assertNotIn('id', response.data[0])

    def test_post_request_creates_new_user_and_returns_created_user(self):
        """
        Test that admins can successfully create new users and after
        creating server returns created user
        """
        # Assign user on request
        self.request.user = self.admin_user

        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.admin_user.auth_token.key
        )

        response = self.client.post(reverse('api:user-list'),
                                    data=self.payload, format='json')

        # if User.DoesNotExist is not raised - means test passed and user
        # was created.
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        sarah = User.objects.get(username='Sarah1234')

        # Checking that view returns created user.
        # Removing password from payload and updating it to use it
        # as a data that should be returned by the view
        self.payload.pop('password')
        url = self.request.build_absolute_uri(
            reverse('api:user-detail', args=[sarah.username]))
        self.payload.update(
            {'id': sarah.pk,
             'url': url,
             'is_active': sarah.is_active,
             'groups': [],
             'last_update': sarah.last_update.strftime('%Y-%m-%d %H:%M:%S'),
             'date_joined': sarah.date_joined.strftime('%Y-%m-%d %H:%M:%S')
            }
        )
        self.assertEqual(response.data, self.payload)

    def test_post_request_returns_403_status_code_for_not_admins(self):
        """Test that regular users can't create new users"""
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.regular_user.auth_token.key
        )
        error = {
            'detail': 'You do not have permission to perform this action.'
        }
        response = self.client.post(reverse('api:user-list'),
                                    data=self.payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data, error)

    def test_creation_fails_if_admin_provides_not_valid_address(self):
        """
        Test that our create user method actualy verify data using address
        serialzier
        """
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.admin_user.auth_token.key
        )
        error = {
            'address': {
                'zip_code': [
                    'Enter a valid value.',
                    'Ensure this field has no more than 6 characters.'
                ]
            }
        }
        # Update payload with invalid data.
        self.payload['address'].update({'zip_code': '1234567'})
        response = self.client.post(reverse('api:user-list'),
                                    data=self.payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, error)
        # Try to fetch user to make sure user itself wasn't created.
        self.assertFalse(User.objects.filter(username='Sarah1234').exists())

    def test_creation_of_user_with_already_existing_username(self):
        """
        Test that user can't create user if user with given username already
        exists.
        """
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.admin_user.auth_token.key
        )
        error = {'username': ['A user with that username already exists.']}
        create_user('Sarah1234', 'some@mail.com')
        response = self.client.post(reverse('api:user-list'),
                                    data=self.payload, format='json')

        self.assertEqual(response.data, error)

    def test_creation_of_user_with_already_existing_email(self):
        """
        Test that user can't create user if user with given email already
        exists.
        """
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.admin_user.auth_token.key
        )
        error = {'email': ['user with this email already exists.']}
        create_user('NoSarah1234', 'sarah@email.com')
        response = self.client.post(reverse('api:user-list'),
                                    data=self.payload, format='json')

        self.assertEqual(response.data, error)