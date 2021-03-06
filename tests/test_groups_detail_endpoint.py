from django.urls import reverse
from django.contrib.auth.models import Group

from rest_framework import status
from rest_framework.test import APITestCase, APIRequestFactory

from profiles.serializers import GroupDetailSerializer
from .utils import CreateUsersMixin, create_group, create_user


class GroupDetailEndpointTestCase(CreateUsersMixin, APITestCase):

    def setUp(self):
        super().setUp()

        self.safe_request = APIRequestFactory().get('/something/')
        self.put_request = APIRequestFactory().put('/something/')
        self.patch_request = APIRequestFactory().patch('/something/')

    def test_returns_correct_representation(self):
        """Test view returns correct group details representation"""
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.admin_user.auth_token.key
        )
        self.admin_group.users_count = 1
        serialized_data = GroupDetailSerializer(
            self.admin_group, context={'request': self.safe_request}
        ).data

        response = self.client.get(
            reverse('api:group-detail', args=[self.admin_group.name])
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serialized_data)

    def test_admin_can_update_group_using_PUT_request(self):
        """Test admins can perform full group update using PUT request"""
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.admin_user.auth_token.key
        )
        group = create_group(name='Managers')
        payload = {'name': 'Sales', 'users': [self.regular_user.username,
                                              self.admin_user.username]
                  }
        response = self.client.put(
            reverse('api:group-detail', args=[group.name]), data=payload,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # refetching updated group
        group = Group.objects.get(name='Sales')

        # manual annotation
        group.users_count = 2
        serialized_data = GroupDetailSerializer(
            group, context={'request': self.put_request}
        ).data
        self.assertEqual(response.data, serialized_data)

        self.assertEqual(group.user_set.all().count(), 2)
        users = group.user_set.all()
        self.assertIn(self.admin_user, users)
        self.assertIn(self.regular_user, users)

        payload = {'name': 'Staff', 'users': [self.regular_user.username]}

        response = self.client.put(
            reverse('api:group-detail', args=[group.name]), data=payload,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # refetching updated group
        group = Group.objects.get(name='Staff')
        group.users_count = 1
        serialized_data = GroupDetailSerializer(
            group, context={'request': self.put_request}
        ).data

        self.assertEqual(response.data, serialized_data)
        self.assertEqual(group.user_set.all().count(), 1)
        self.assertTrue(
            group.user_set.filter(username=self.regular_user.username).exists()
            )

    def test_admin_can_add_members_to_group_using_PATCH_request(self):
        """Test admins can perform partial updates using PATCH request"""
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.admin_user.auth_token.key
        )
        group = create_group(name='Managers')

        payload = {'users': [self.admin_user.username,
                             self.regular_user.username]}

        response = self.client.patch(
            reverse('api:group-detail', args=[group.name]), data=payload,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # refetching updated group
        group = Group.objects.get(name='Managers')
        group.users_count = 2
        serialized_data = GroupDetailSerializer(
            group, context={'request': self.patch_request}
        ).data
        self.assertEqual(response.data, serialized_data)

        users = group.user_set.all()
        self.assertEqual(users.count(), 2)

        self.assertIn(self.admin_user, users)
        self.assertIn(self.regular_user, users)

        # Test adding another user
        user = create_user('John', 'john@email.com')

        payload = {'users': [user.username,
                             self.admin_user.username,
                             self.regular_user.username]}

        response = self.client.patch(
            reverse('api:group-detail', args=[group.name]), data=payload,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # refetching updated group
        group = Group.objects.get(name='Managers')
        group.users_count = 3
        serialized_data = GroupDetailSerializer(
            group, context={'request': self.patch_request}
        ).data
        self.assertEqual(response.data, serialized_data)

        self.assertEqual(group.user_set.all().count(), 3)
        self.assertTrue(group.user_set.filter(username='John').exists())

    def test_admin_can_remove_users_from_group_using_PATCH_request(self):
        """Test admins can remove users from group using PATCH request"""
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.admin_user.auth_token.key
        )
        self.admin_group.user_set.add(self.regular_user)
        # except to regular user to no longer be in administrators group
        payload = {'users': [self.admin_user.username]}

        response = self.client.patch(
            reverse('api:group-detail', args=[self.admin_group.name]),
            data=payload, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
         # refetching updated group
        group = Group.objects.get(name='Administrators')
        group.users_count = 1
        serialized_data = GroupDetailSerializer(
            group, context={'request': self.patch_request}
        ).data
        self.assertEqual(response.data, serialized_data)
        self.assertFalse(
            group.user_set.filter(username=self.regular_user.username).exists()
        )

    def test_return_error_if_admin_trying_to_add_non_existing_users(self):
        """Test that admin can't add nonexisting users to groups"""
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.admin_user.auth_token.key
        )

        payload = {'users': ['Samuel']}
        response = self.client.patch(
            reverse('api:group-detail', args=[self.admin_group.name]),
            data=payload, format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        response = self.client.put(
            reverse('api:group-detail', args=[self.admin_group.name]),
            data=payload, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_non_admins_cant_edit_groups(self):
        """Test regular users can't edit groups information"""
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.regular_user.auth_token.key
        )
        payload = {'doesn\'t matter'}

        response = self.client.patch(
            reverse('api:group-detail', args=[self.admin_group.name]),
            data=payload, format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        response = self.client.put(
            reverse('api:group-detail', args=[self.admin_group.name]),
            data=payload, format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admins_can_delete_groups(self):
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.admin_user.auth_token.key
        )
        group = create_group(name='Managers')

        response = self.client.delete(
            reverse('api:group-detail', args=[group.name]),
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_admins_cant_delete_admin_group(self):
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.admin_user.auth_token.key
        )
        response = self.client.delete(
            reverse('api:group-detail', args=[self.admin_group.name]),
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_superuser_can_delete_admin_group(self):
        self.admin_user.is_superuser = True
        self.admin_user.save()
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.admin_user.auth_token.key
        )
        response = self.client.delete(
            reverse('api:group-detail', args=[self.admin_group.name]),
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_admins_cant_remove_all_users_from_admin_group(self):
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.admin_user.auth_token.key
        )

        response = self.client.patch(
            reverse('api:group-detail', args=[self.admin_group.name]),
            data={'users': []}, format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
