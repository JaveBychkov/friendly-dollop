from django.db.models import Count
from django.test import TestCase


from profiles.models import Address, User
from .utils import create_address, create_user


class UserDeletionTestCase(TestCase):

    def setUp(self):
        self.user = create_user('Javedimka', 'sumsum@gmail.com')
        self.second_user = create_user('Elenka', 'elele@gmail.com')
        self.first_address = self.user.address
        self.second_address = create_address(country='Germany')
        self.third_user = create_user('Vasiliy', 'vasya22@gmail.com',
                                      address=self.second_address)

    def test_address_also_will_be_deleted_if_user_being_deleted_is_only_one_who_belongs_to_this_address(self):
        self.third_user.delete()
        self.assertFalse(Address.objects.filter(
            pk=self.second_address.pk).exists())
        self.assertFalse(User.objects.filter(pk=self.third_user.pk).exists())

    def test_address_will_not_be_deleted_if_user_being_deleted_is_not_the_only_one_who_belongs_to_this_address(self):
        self.second_user.delete()
        qs = Address.objects.annotate(
            users_count=Count('user')).filter(pk=self.first_address.pk)
        self.assertTrue(qs.exists())
        self.assertTrue(qs[0].users_count, 1)
        self.assertFalse(User.objects.filter(pk=self.second_user.pk))
