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

    def test_address_will_be_deleted_if_user_being_deleted_is_only_one(self):
        """Test that address wil be deleted if user being deleted is the only
        one user who belong to said address
        """
        self.third_user.delete()
        self.assertFalse(Address.objects.filter(
            pk=self.second_address.pk).exists())
        self.assertFalse(User.objects.filter(pk=self.third_user.pk).exists())

    def test_address_will_not_be_deleted_if_it_has_more_that_one_user(self):
        """Test that address will not be deleted along with user if user
        that being deleted is not the only one who belongs to said
        address
        """
        self.second_user.delete()
        qs = Address.objects.annotate(
            users_count=Count('user')).filter(pk=self.first_address.pk)
        self.assertTrue(qs.exists())
        self.assertTrue(qs[0].users_count, 1)
        self.assertFalse(User.objects.filter(pk=self.second_user.pk))
