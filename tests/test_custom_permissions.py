from rest_framework.test import APITestCase, APIRequestFactory

from profiles.permissions import (ActivateFirstIfInactive,
                                  CantEditSuperuserIfNotSuperuser,
                                  DissallowAdminGroupDeletion)

from .utils import (CreateUsersMixin, create_user, create_admin_group,
                    create_group)


class TestActivateFirstIfInactivePermission(CreateUsersMixin, APITestCase):

    def setUp(self):
        super().setUp()
        self.permission = ActivateFirstIfInactive()
        self.safe_request = APIRequestFactory().get('/something/')
        self.request = APIRequestFactory().patch('/something/')
        self.request.data = {}
        self.inactive_user = create_user('Robert', 'robert@email.com',
                                         is_active=False)
        self.view = 'Dummy'

    def test_return_false_if_user_is_inactive_and_method_is_not_safe(self):
        self.assertFalse(self.permission.has_object_permission(
            self.request, self.view, self.inactive_user
        ))

    def test_return_true_if_user_is_inactive_and_method_is_safe(self):
        self.assertTrue(self.permission.has_object_permission(
            self.safe_request, self.view, self.inactive_user
        ))

    def test_return_true_if_data_in_request_has_is_active_set_to_true(self):
        self.request.data = {'is_active': True}
        self.assertTrue(self.permission.has_object_permission(
            self.request, self.view, self.inactive_user
        ))

    def test_return_true_if_user_is_active(self):
        self.assertTrue(self.permission.has_object_permission(
            self.safe_request, self.view, self.regular_user
        ))

class TestDissallowAdminGroupDeletionPermission(CreateUsersMixin, APITestCase):

    def setUp(self):
        super().setUp()
        self.permission = DissallowAdminGroupDeletion()
        self.delete_request = APIRequestFactory().delete('/something/')
        self.safe_request = APIRequestFactory().get('/something/')
        self.group = create_group(name='Managers')
        self.view = 'Dummy'

    def test_return_false_if_group_is_admin_group(self):
        self.delete_request.user = self.admin_user
        self.assertFalse(self.permission.has_object_permission(
            self.delete_request, self.view, self.admin_group
        ))

    def test_return_true_for_superusers_even_if_group_is_admin_group(self):
        superuser = create_user('Robert', 'robert@email.com',
                                is_staff=True, is_superuser=True)

        self.delete_request.user = superuser

        self.assertTrue(self.permission.has_object_permission(
            self.delete_request, self.view, self.admin_group
        ))

    def test_return_true_if_group_is_regular_group(self):
        self.delete_request.user = self.admin_user
        self.assertTrue(self.permission.has_object_permission(
            self.delete_request, self.view, self.group
        ))

    def test_return_true_if_request_method_is_safe(self):
        self.safe_request.user = self.admin_user
        self.assertTrue(self.permission.has_object_permission(
            self.delete_request, self.view, self.group
        ))



class TestCantEditSuperUserIfNotSuperuser(CreateUsersMixin, APITestCase):
    
    def setUp(self):
        super().setUp()
        self.permission = CantEditSuperuserIfNotSuperuser()
        self.safe_request = APIRequestFactory().get('/something/')
        self.request = APIRequestFactory().patch('/something/')
        self.superuser = create_user('Robert', 'robert@email.com',
                                is_staff=True, is_superuser=True)
        self.superuser_2 = create_user('Roberto', 'roberto@email.com',
                                  is_staff=True, is_superuser=True)
        self.editor = create_user('Veronika', 'veronika@email.com',
                             is_staff=True, is_superuser=False)
        self.admin_group.user_set.add(self.superuser, self.editor)
        self.view = 'Dummy'

    def test_return_false_if_not_superuser_editing_superuser(self):
        self.request.user = self.editor
        self.assertFalse(self.permission.has_object_permission(
            self.request, self.view, self.superuser
        ))

    def test_return_true_if_request_method_is_safe(self):
        self.assertTrue(self.permission.has_object_permission(
            self.safe_request, self.view, self.superuser
        ))

    def test_return_true_if_superuser_editing_superuser(self):
        self.request.user = self.superuser_2
        self.assertTrue(self.permission.has_object_permission(
            self.request, self.view, self.superuser
        ))