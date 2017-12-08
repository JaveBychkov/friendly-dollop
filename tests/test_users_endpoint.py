from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase, APIRequestFactory, force_authenticate

from profiles.serializers import UserSerializer
from profiles.models import User

from .utils import CreateUsersMixin


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


    # Because we successfully tested out serializers to return data in
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

        try:
            sarah = User.objects.get(username='Sarah1234')
        except User.DoesNotExist:
            msg = 'Can\'t retrive user with username Sarah1234'
            self.fail(msg=msg)

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
