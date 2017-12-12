
from rest_framework.test import APITestCase, APIRequestFactory

from profiles.permissions import (ActivateFirstIfInactive,
                                  CantEditSuperuserIfNotSuperuser)

from .utils import CreateUsersMixin, create_user


class CustomPermissionsTestCase(CreateUsersMixin, APITestCase):
    """Test Case to test that custom permissions works as expected"""

    def setUp(self):
        super().setUp()
        self.safe_request = APIRequestFactory().get('/something/')
        self.request = APIRequestFactory().patch('/something/')
        self.request.data = {}
        self.view = 'Dummy'

    def test_admin_cant_change_user_data_if_user_is_not_active(self):
        """Check that permission acts correctly in different occasions"""
        permission = ActivateFirstIfInactive()
        inactive_user = create_user('Robert', 'robert@email.com', is_active=False)

        # Check that permission will be denied if request method is not safe
        # and user is inactive.
        self.assertFalse(permission.has_object_permission(
            self.request, self.view, inactive_user
        ))

        # Check that permission will be allowed if user is inactive but request
        # method is safe.
        self.assertTrue(permission.has_object_permission(
            self.safe_request, self.view, inactive_user
        ))

        # Check that permission will be allowed if user is inactive and request
        # method is not safe but request.data has is_active set to True.
        self.request.data = {'is_active': True}
        self.assertTrue(permission.has_object_permission(
            self.request, self.view, inactive_user
        ))

    def test_admin_cant_change_superuser_data(self):
        """Test that noone except superusers can change superuser data"""
        permission = CantEditSuperuserIfNotSuperuser()
        superuser = create_user('Robert', 'robert@email.com',
                                is_staff=True, is_superuser=True)
        superuser_2 = create_user('Roberto', 'roberto@email.com',
                                  is_staff=True, is_superuser=True)
        editor = create_user('Veronika', 'veronika@email.com',
                             is_staff=True, is_superuser=False)
        self.admin_group.user_set.add(superuser, editor)

        self.request.user = editor

        # Check that permission will be denied if admin who attempts to change
        # superuser is not superuser
        self.assertFalse(permission.has_object_permission(
            self.request, self.view, superuser
        ))
        
        # Check that permission will be allowed if request method is safe
        self.assertTrue(permission.has_object_permission(
            self.safe_request, self.view, superuser
        ))

        # Check that permission will be allowed if user who attempts to change
        # superuser is also superuser
        self.request.user = superuser_2
        self.assertTrue(permission.has_object_permission(
            self.request, self.view, superuser
        ))



