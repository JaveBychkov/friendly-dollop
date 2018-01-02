from django.contrib.auth.models import Group
from django.db.models import Count
from django.urls import reverse

from rest_framework.test import APIRequestFactory, APITestCase

from profiles.serializers import (AddressSerializer, GroupDetailSerializer,
                                  GroupSerializer, UserGroupsSerializer,
                                  UserSerializer)
from .utils import (CreateUsersMixin, create_address, create_admin_group,
                    create_group, create_user)


class GroupDetailSerializerTestCase(CreateUsersMixin, APITestCase):
    """Test that group detail serializer work as expected and return data in
    expected format
    """
    def setUp(self):
        super().setUp()
        self.group = create_group('Managers')
        self.request = APIRequestFactory().get('something')
        self.build_url = self.request.build_absolute_uri

    def test_returns_data_in_expected_format(self):
        """Test serializer return user data in expected format"""
        url = self.build_url(reverse('api:group-detail',
                                     args=[self.group.name])
                            )
        group_data = {'url': url, 'name': 'Managers', 'users_count': 0,
                      'users': []}
        # Little hack to set field that normaly will be annotated in view.
        self.group.users_count = 0
        serializer = GroupDetailSerializer(self.group,
                                           context={'request': self.request})
        self.assertEqual(serializer.data, group_data)

    def test_update_method_adds_users(self):
        """Test that update method with provided "action": "add" will add user
        to group.
        """
        self.request.method = 'PATCH'
        u1 = create_user('user1', 'user1@email.com')
        u2 = create_user('user2', 'user2@email.com')
        self.group.user_set.add(u1, u2)

        # PATCH should act like PUT on group's users update
        payload = {'users': [self.regular_user.username,
                             self.admin_user.username,
                             u1.username,
                             u2.username]}
        serializer = GroupDetailSerializer(self.group, data=payload,
                                           context={'request': self.request},
                                           partial=True)
        serializer.is_valid()
        instance = serializer.save()
        self.assertEqual(instance.user_set.all().count(), 4)

    def test_update_method_removes_users(self):
        """Test that update method with provided "action": "remove" will remove
        user from group.
        """
        self.request.method = 'PATCH'
        user1 = create_user('user1', 'user1@email.com')
        user2 = create_user('user2', 'user2@email.com')
        self.group.user_set.add(user1, user2)
        payload = {'users': [user2.username],}
        serializer = GroupDetailSerializer(self.group, data=payload,
                                           context={'request': self.request},
                                           partial=True)
        serializer.is_valid()
        instance = serializer.save()
        self.assertEqual(instance.user_set.all().count(), 1)
        self.assertTrue(instance.user_set.filter(username='user2').exists())

    def test_name_update(self):
        self.request.method = 'PATCH'
        """Test that update method will override group name"""
        payload = {'name': 'NotManagers'}
        serializer = GroupDetailSerializer(self.group, data=payload,
                                           context={'request': self.request},
                                           partial=True)
        serializer.is_valid()
        instance = serializer.save()
        self.assertEqual(instance.name, 'NotManagers')


class UserGroupsSerializerTestCase(APITestCase):
    """
    Test that user's group serializer works as expected and return data in
    expected format.
    """
    def setUp(self):
        self.user = create_user('Daniel', 'daniel@email.com')
        self.user.groups.add(create_group('Staff'), create_group('Managers'))

    def test_return_data_in_expected_format(self):
        user_groups_data = {'groups': ['Staff', 'Managers']}
        serializer = UserGroupsSerializer(self.user)
        self.assertEqual(serializer.data, user_groups_data)

    # Serialzier .update method designed to act as PUT request and meant to
    # replace groups completely.

    def test_serializer_method_updates_user_groups(self):
        """Test that .update method updates groups as expected
        In this case: add one group to user, new total of groups is 3.
        """
        create_group('DevOps')
        payload = {'groups': ['Staff', 'Managers', 'DevOps']}
        serializer = UserGroupsSerializer(self.user, data=payload)
        self.assertTrue(serializer.is_valid())
        instance = serializer.save()
        self.user.refresh_from_db()
        self.assertTrue(instance.groups.filter(name='DevOps').exists())
        self.assertEqual(instance.groups.all().count(), 3)

    def test_serializer_method_overrides_user_groups(self):
        """Test that .update method updates groups as expected
        In this case: removes two existing groups and assign one new. 
        """
        create_group('DevOps')
        payload = {'groups': ['DevOps']}
        serializer = UserGroupsSerializer(self.user, data=payload)
        self.assertTrue(serializer.is_valid())
        instance = serializer.save()
        self.assertTrue(instance.groups.filter(name='DevOps').exists())
        self.assertEqual(instance.groups.all().count(), 1)

class GroupSerializerTestCase(APITestCase):
    """
    Test that group serialzier works as expected and return data in
    expected format.
    """
    def setUp(self):
        self.request = APIRequestFactory().get('something')
        self.build_url = self.request.build_absolute_uri

    def test_returns_data_in_expected_format(self):
        """Test serializer return user data in expected format"""
        managers = create_group('Managers')
        staff = create_group('Staff')
        query = Group.objects.annotate(users_count=Count('user'))
        group_data = [
            {'name': 'Managers', 'users_count': 0,
             'url': self.build_url(
                 reverse('api:group-detail', args=[managers.name])
             )},
            {'name': 'Staff', 'users_count': 0,
             'url': self.build_url(
                 reverse('api:group-detail', args=[staff.name])
             )}
        ]
        serializer = GroupSerializer(query, many=True,
                                     context={'request': self.request})
        self.assertCountEqual(serializer.data, group_data)


class AddressSerializerTestCase(APITestCase):
    """
    Test that address serialzier works as expected and returns data in
    expected format.
    """
    def test_returns_data_in_expected_format(self):
        """Test serializer return user data in expected format"""
        address = create_address()
        address_data = {'zip_code': '654321', 'country': 'Россия',
                        'city': 'Нижний Новгород',
                        'district': 'Нижегородский район',
                        'street': 'Родионова'
                       }
        serializer = AddressSerializer(address)
        self.assertEqual(serializer.data, address_data)


class UserSerializerTestCase(CreateUsersMixin, APITestCase):
    """
    Test that user serialzier works as expected and returns data in
    expected format for both: admin and regular users.
    """
    def setUp(self):
        # After super() call we get 2 users: self.admin_user, self.regular_user
        super().setUp()

        # Macking dummy request
        self.request = APIRequestFactory().get('something')
        self.build_url = self.request.build_absolute_uri

    def set_user_to_request(self, user):
        """Utility method to set provided user on dummy WSGIRequest obj"""
        self.request.user = user

    def test_provides_subset_of_fields_if_user_doesnt_have_permission(self):
        """
        Testing serializer __init__ method that will check whether user
        have 'view_full_info' permission or not and return subset of fields
        if user don't have mentioned permission
        """
        self.set_user_to_request(self.regular_user)
        basic_user_fields = ('first_name', 'url', 'last_name', 'username',
                             'email', 'birthday', 'address', 'groups')
        # Generic views will pass context kwarg with request in it
        # to serialzier themselves but here we need to do it by ourselves.
        serializer = UserSerializer(self.admin_user,
                                    context={'request': self.request})
        self.assertCountEqual(serializer.data.keys(), basic_user_fields)

    def test_provides_full_set_of_fields_if_user_have_permission(self):
        """
        Testing serializer __init__ method that will check whether user
        have 'view_full_info' permission or not and return all fields if user
        have mentioned permission
        """
        self.set_user_to_request(self.admin_user)
        full_user_fields = ('id', 'first_name', 'url', 'last_name', 'username',
                            'email', 'birthday', 'address', 'groups',
                            'is_active', 'date_joined', 'last_update')
        # Generic views will pass context kwarg with request in it
        # to serialzier themselves but here we need to do it by ourselves.
        serializer = UserSerializer(self.admin_user,
                                    context={'request': self.request})
        self.assertCountEqual(serializer.data.keys(), full_user_fields)

    def test_serializer_provides_right_data_representation_for_admins(self):
        """Test serializer return user data in expected format"""

        self.set_user_to_request(self.admin_user)

        user = create_user('user1', 'user@email.com')
        last_update = user.last_update.strftime('%Y-%m-%d %H:%M:%S')
        date_joined = user.date_joined.strftime('%Y-%m-%d %H:%M:%S')
        birthday = user.birthday.isoformat()
        url = self.build_url(reverse('api:user-detail', args=[user.username]))
        data = {'id': user.pk, 'url': url, 'first_name': 'user_first_name',
                'last_name': 'user_last_name', 'username': 'user1',
                'email': 'user@email.com', 'birthday': birthday,
                'address':
                    {'zip_code': '654321', 'country': 'Россия',
                     'city': 'Нижний Новгород',
                     'district': 'Нижегородский район',
                     'street': 'Родионова'
                    },
                'groups': [],
                'is_active': True,
                'date_joined': date_joined,
                'last_update': last_update
               }
        serializer = UserSerializer(user, context={'request': self.request})
        self.assertEqual(serializer.data, data)

    def test_serializer_provides_right_data_representation_for_not_admin(self):
        """Test serializer return user data in expected format"""


        self.set_user_to_request(self.regular_user)
        user = create_user('user1', 'user@email.com')
        birthday = user.birthday.isoformat()
        url = self.build_url(reverse('api:user-detail', args=[user.username]))
        data = {'url': url, 'first_name': 'user_first_name',
                'last_name': 'user_last_name', 'username': 'user1',
                'email': 'user@email.com', 'birthday': birthday,
                'address':
                    {'zip_code': '654321', 'country': 'Россия',
                     'city': 'Нижний Новгород',
                     'district': 'Нижегородский район',
                     'street': 'Родионова'
                    },
                'groups': [],
               }
        serializer = UserSerializer(user, context={'request': self.request})
        self.assertEqual(serializer.data, data)

    def test_create_user(self):
        self.skipTest(reason="We will test create method in endpoint tests")

    def test_update_user(self):
        self.skipTest(reason="We will test update method in endpoint tests")
