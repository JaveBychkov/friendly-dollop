from django.urls import reverse
from django.contrib.auth.models import Group
from django.db.models import Count

from rest_framework.test import APITestCase, APIRequestFactory
from rest_framework import status

from profiles.serializers import GroupSerializer
from .utils import CreateUsersMixin, create_group



class GroupListEndPoint(CreateUsersMixin, APITestCase):

    def setUp(self):
        super().setUp()

        self.safe_request = APIRequestFactory().get('/something')

    def test_return_correct_representation(self):
        """Test view returns expected group representation"""
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.admin_user.auth_token.key
        )
        # Manual "annotation":
        self.admin_group.users_count = 1
        serialized_data = GroupSerializer(
            [self.admin_group], context={'request': self.safe_request},
            many=True
        ).data

        response = self.client.get(reverse('api:group-list'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serialized_data)

    def test_admin_can_create_group(self):
        """Test admins can create new groups"""
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.admin_user.auth_token.key
        )

        payload = {'name': 'Managers'}

        response = self.client.post(
            reverse('api:group-list'), data=payload, format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Group.objects.filter(name='Managers').exists())

        group = Group.objects.get(name='Managers')
        # Manual "annotation":
        group.users_count = 0

        serialized_data = GroupSerializer(
            group, context={'request': self.safe_request}
        ).data

        self.assertEqual(response.data, serialized_data)

    def test_regular_users_cant_create_groups(self):
        """Test server returns error when not admins try to create group"""
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.regular_user.auth_token.key
        )
        payload = {'name': 'Managers'}

        response = self.client.post(
            reverse('api:group-list'), data=payload, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)