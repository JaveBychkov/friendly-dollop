from datetime import date

from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase, APIRequestFactory

from profiles.models import User
from profiles.serializers import UserSerializer

from .utils import create_user, CreateUsersMixin

class TestAPISearch(CreateUsersMixin, APITestCase):
    """Test case to test that provided search params return correct data"""

    def setUp(self):
        super().setUp()

        create_user('Robz', 'robz@email.com', first_name='Robin',
                    last_name='Sparkles')
        create_user('John', 'jackkennedy@usgov.com')
        create_user('Lily', 'lily@email.com', birthday=date(1990, 2, 21))
        create_user('Something', 'some1@email.com', is_active=False)
        create_user('Somethin2', 'some2@email.com', is_active=False)

        # Dummy request
        self.safe_request = APIRequestFactory().get('/something/')
        self.safe_request.user = self.admin_user
        self.search_url = reverse('api:search') + '?q={}'
        self.search_active_filter = reverse('api:search') + '?is_active={}'
        self.context = {'request': self.safe_request}

    def test_users_can_search_for_users_by_part_of_their_name(self):
        """
        Test that users can search other users by part of their name,
        whether it theirs first name or last name.
        """
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.admin_user.auth_token.key
        )
        # Filtering instead of .get to avoid error while trying to serialize
        # user object with many=True.
        # Or if we want to use .get we can just wrap user in list:
        # UserSerializer([user], many=True)
        user = User.objects.filter(username='Robz')
        serializer = UserSerializer(user, many=True,
                                    context=self.context)
        # Searching by first_name.
        search_param = 'Robin'

        response = self.client.get(self.search_url.format(search_param))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

        # Searching by last_name.
        search_param = 'sparkles'
        response = self.client.get(self.search_url.format(search_param))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_users_can_search_for_users_by_exact_email(self):
        """Test that users can search for others user by their exact email"""
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.admin_user.auth_token.key
        )
        user = User.objects.filter(username='John')
        serializer = UserSerializer(user, many=True,
                                    context=self.context)

        search_param = 'jackkennedy@usgov.com'

        response = self.client.get(self.search_url.format(search_param))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

        # Test that user will not be found by part of email
        # Note: Users that have part being searched in their first_name or
        # last_name will be returned in QuerySet
        search_param = 'jackkennedy@'
        response = self.client.get(self.search_url.format(search_param))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotEqual(response.data, serializer.data)

    def test_users_can_search_for_users_by_exact_birth_date(self):
        """
        Test users can search users by their exact birth date, by 3
        different formats.
        """
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.admin_user.auth_token.key
        )
        user = User.objects.filter(username='Lily')
        serializer = UserSerializer(user, many=True,
                                    context=self.context)
        # Trying different date formats:
        search_params = ['1990-02-21', '21-02-1990', '21-02-90']


        # subTest is really handy here
        for param in search_params:
            with self.subTest(param=param):
                response = self.client.get(self.search_url.format(param))
                self.assertEqual(response.status_code, status.HTTP_200_OK)
                self.assertEqual(response.data, serializer.data)

    def test_is_active_filter_returns_users_according_to_provided_value(self):
        """Test that admin can filter users by their is_active status"""
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.admin_user.auth_token.key
        )
        # Filtering by active users
        queryset = User.objects.filter(is_active=True)
        serializer = UserSerializer(queryset, many=True,
                                    context=self.context)

        allowed_values = ['y', 'yes', 't', 'true', 'on', '1']
        for param in allowed_values:
            with self.subTest(param=param):

                response = self.client.get(
                    self.search_active_filter.format(param)
                )
                self.assertEqual(response.status_code, status.HTTP_200_OK)
                self.assertEqual(response.data, serializer.data)

        # Filtering by inactive users
        queryset = User.objects.filter(is_active=False)
        serializer = UserSerializer(queryset, many=True,
                                    context={'request': self.safe_request})
        allowed_values = ['n', 'no', 'f', 'false', 'off', '0']
        for param in allowed_values:
            with self.subTest(param=param):

                response = self.client.get(
                    self.search_active_filter.format(param)
                )
                self.assertEqual(response.status_code, status.HTTP_200_OK)
                self.assertEqual(response.data, serializer.data)

        # Check that whole queryset returned if is_active is not allowed value
        serializer = UserSerializer(User.objects.all(), many=True,
                                    context={'request': self.safe_request})
        response = self.client.get(self.search_active_filter.format('wrong'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_is_active_filter_doesnt_change_queryset_for_not_admins(self):
        """
        Test that is_active filter doesn't impact queryset if non admin
        try to apply that filter
        """
        self.safe_request.user = self.regular_user
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.regular_user.auth_token.key
        )
        serializer = UserSerializer(User.objects.all(), many=True,
                                    context={'request': self.safe_request})
        param = 'false'
        response = self.client.get(self.search_active_filter.format(param))


        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_search_returns_empty_query_set_if_it_cant_find_users(self):
        """Test that empty queryset will be returned if there is no matches"""
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.admin_user.auth_token.key
        )
        response = self.client.get('/api/users/search?is_active=False&q=Robin')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])
