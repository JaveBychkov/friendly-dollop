from datetime import date

from django.db.models import Q
from django.contrib.auth.models import Group, Permission

from rest_framework.authtoken.models import Token

from profiles.models import User, Address


def create_group(name):
    """Function to create group"""
    return Group.objects.create(name=name)

def create_admin_group():
    """Function to create admin group with some permissions"""
    group = Group.objects.create(name='Administrators')
    # Retriving permission that was specified in our User model Meta class.
    perms = Permission.objects.filter(
        Q(content_type__app_label='profiles') | Q(content_type__model='group')
    )
    group.permissions.add(*perms)
    return group

def create_address(**kwargs):
    """Factory to create Address objects"""
    defaults = {
        'zip_code': '654321',
        'country': 'Россия',
        'city': 'Нижний Новгород',
        'district': 'Нижегородский район',
        'street': 'Родионова'
    }
    defaults.update(kwargs)
    return Address.objects.create(**defaults)


def create_user(username, email, **kwargs):
    """Factory to create User objects"""
    defaults = {
        'username': username,
        'email': email,
        'password': 'userpassword',
        'first_name': 'user_first_name',
        'last_name': 'user_last_name',
        'birthday': date(1995, 7, 4),
        'is_staff': False,
        'is_superuser': False,
    }
    defaults.update(kwargs)
    if 'address' not in kwargs:
        defaults['address'] = create_address()
    # Calling .create_user(**defaults) here to avoid setting
    # password manualy.
    return User.objects.create_user(**defaults)


class CreateUsersMixin:
    """Mixin to reduce code duplication.

    Creates 2 users, one is admin and one is regular user.
    We're not login user here to keep tests explicit.
    """

    def setUp(self):
        self.admin_user = create_user('Dimka', 'admin@email.com')
        self.admin_group = create_admin_group()
        self.admin_group.user_set.add(self.admin_user)
        Token.objects.create(user=self.admin_user)
        self.regular_user = create_user('Lenka', 'regular@email.com')
        Token.objects.create(user=self.regular_user)
