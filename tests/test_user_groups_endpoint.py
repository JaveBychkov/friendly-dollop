from django.urls import reverse
from django.contrib.auth.models import Group

from rest_framework import status
from rest_framework.test import APIClient, APITestCase
from .utils import CreateUsersMixin, create_group

from profiles.models import User
from profiles.serializers import UserGroupsSerializer


class UserGroupsTestCase(CreateUsersMixin, APITestCase):
    """
    Test case to test that user groups renders correctly and admin user
    can successfully update user's groups.
    """

    def setUp(self):
        super().setUp()

        self.url = reverse('api:user-groups',
                           kwargs={'username': self.regular_user.username}
                          )

    def test_returns_correct_representation_on_get_request(self):
        """Test that view returns correct representation regardless of user
        status (eg. admin or not)
        """
        serialized_data = UserGroupsSerializer(self.admin_user).data
        # Test representation for admin user.
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.admin_user.auth_token.key
        )
        url = reverse('api:user-groups',
                      kwargs={'username': self.admin_user.username}
                     )

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serialized_data)
        # Test representation for regular user.
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.regular_user.auth_token.key
        )

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serialized_data)

    def test_admin_can_update_user_groups(self):
        """Test that admin can successfully update user's groups"""
        create_group(name='Managers')
        create_group(name='Sales')
        self.assertFalse(self.regular_user.groups.all())

        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.admin_user.auth_token.key
        )

        payload = {'groups': ['Managers', 'Sales']}

        response = self.client.put(self.url, data=payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # refetch user from db to reload relations.
        self.regular_user = User.objects.get(username='Lenka')

        self.assertCountEqual(
            self.regular_user.groups.all(),
            Group.objects.filter(name__in=('Managers', 'Sales'))
        )

        serialized_data = UserGroupsSerializer(self.regular_user).data
        self.assertEqual(response.data, serialized_data)

    def test_put_request_actually_overrides_user_groups(self):
        """
        Test that PUT request overrides user groups with groups that passed
        in request.
        """
        self.regular_user.groups.add(create_group(name='Managers'),
                                     create_group(name='Sales'))

        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.admin_user.auth_token.key
        )

        payload = {'groups': ['Managers']}

        response = self.client.put(self.url, data=payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # refetch user from db to reload relations.
        self.regular_user = User.objects.get(username='Lenka')
        self.assertEqual(self.regular_user.groups.count(), 1)
        self.assertTrue(self.regular_user.groups.filter(name='Managers').exists())

        serialized_data = UserGroupsSerializer(self.regular_user).data
        self.assertEqual(response.data, serialized_data)

    def test_patch_request_not_allowed(self):
        """Test that server will reject incoming PATCH requests"""
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.admin_user.auth_token.key
        )
        error = {'detail': 'Method "PATCH" not allowed.'}

        response = self.client.patch(self.url, data={}, format='json')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(response.data, error)

    def test_regular_user_cant_update_users_groups(self):
        """Test that no admin users can't update groups"""
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.regular_user.auth_token.key
        )

        url = reverse('api:user-groups',
                      kwargs={'username': self.admin_user.username}
                     )

        error = {
            'detail': 'You do not have permission to perform this action.'
        }

        response = self.client.put(url, data={'groups': []}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data, error)

    def test_update_with_nonexisting_groups_will_return_error(self):
        """
        Test that request with nonexisting groups will don't affect data and
        server return error
        """
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.admin_user.auth_token.key
        )

        self.assertFalse(self.regular_user.groups.all())

        payload = {'groups': ['Administrators', 'SuperAdministrators']}

        error = {'groups':
                 ['Object with name=SuperAdministrators does not exist.']
                }

        response = self.client.put(self.url, data=payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, error)

        self.regular_user = User.objects.get(username='Lenka')
        # Verify that existing group - Administrators didn't added to user
        self.assertFalse(self.regular_user.groups.all())

    def test_empty_groups_request_will_erase_user_groups(self):
        """
        Make sure that accidental empty put request will not delete user's
        groups
        """
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.admin_user.auth_token.key
        )
        self.regular_user.groups.add(create_group(name='Managers'),
                                     create_group(name='Sales'))
        response = self.client.put(self.url, data={'groups': []}, format='json')
        # refetch user

        user = User.objects.get(pk=self.regular_user.pk)
        self.assertFalse(user.groups.all().exists())
