from django.forms.models import model_to_dict

from rest_framework.test import APITestCase

from profiles.serializers import UserSerializer
from profiles.models import User, Address
from .utils import create_address, create_user


class TestAddressCreationAndUpdating(APITestCase):

    def setUp(self):
        self.data = {'zip_code': '543211', 'country': 'Germany',
                    'city': 'Berlin', 'district': 'West', 'street': 'Big Low'}
        self.address = create_address(**self.data)
        self.user = create_user('Dmitriy', 'dmitriy@mail.com', address=self.address)

    def test_do_nothing_if_submitted_data_is_exact_as_it_was(self):
        self.assertEqual(Address.objects.count(), 1)

        payload = {'address': self.data}

        serializer = UserSerializer(self.user, data=payload, partial=True)
        self.assertTrue(serializer.is_valid())
        saved_obj = serializer.save()
        self.assertEqual(self.address, saved_obj.address)
        address_data = model_to_dict(saved_obj.address)
        address_data.pop('id')
        self.assertEqual(self.data, address_data)
        self.assertEqual(Address.objects.count(), 1)

    def test_on_creating_assign_user_to_existing_address_if_submitted_address_data_already_exists(self):
        payload = {'first_name': 'Sarah',
                   'last_name': 'Chalke', 'username': 'Sarah1234',
                   'password': 'iamsarah',
                   'email': 'sarah@email.com', 'birthday': '1974-08-27',
                   'address': self.data
                  }
        serializer = UserSerializer(data=payload)
        self.assertTrue(serializer.is_valid())
        created_obj = serializer.save()
        self.assertEqual(self.address, created_obj.address)

        self.assertEqual(Address.objects.count(), 1)

        self.assertCountEqual(self.address.user_set.all(),
                              [created_obj, self.user])

    def test_on_update_assign_user_to_existing_address_if_submitted_address_data_already_exists(self):
        # Also test that previous address will be deleted if it has no other users
        self.data.update({'street': 'High Low'})
        user = create_user('Olga', 'olga@mail.com',
                           address=create_address(**self.data))
        self.assertEqual(Address.objects.count(), 2)

        serializer = UserSerializer(user,
                                    data={'address': {'street': 'Big Low'}},
                                    partial=True)
        self.assertTrue(serializer.is_valid())
        saved_obj = serializer.save()
        self.assertEqual(saved_obj.address, self.address)
        self.assertEqual(Address.objects.count(), 1)

    def test_on_update_previous_address_will_not_be_deleted_if_it_has_more_than_one_user_new_one_will_be_created_instead(self):
        self.data.update({'street': 'High Low'})
        address = create_address(**self.data)
        user1 = create_user('Olga', 'olga@mail.com',
                            address=address)
        self.assertEqual(Address.objects.count(), 2)

        user2 = create_user('Sergei', 'sergei@mail.com', address=address)

        self.assertEqual(Address.objects.count(), 2)

        serializer = UserSerializer(user2,
                                    data={'address': {'street': 'Different'}},
                                    partial=True)
        self.assertTrue(serializer.is_valid())

        saved_obj = serializer.save()
        self.assertNotEqual(saved_obj.address, self.address)
        self.assertNotEqual(saved_obj.address, address)
        self.assertEqual(Address.objects.count(), 3)
        self.assertEqual(user1.address.street, 'High Low')
        self.assertEqual(saved_obj.address.street, 'Different')
        self.assertEqual(user2, saved_obj)
        self.assertEqual(user2.address.street, 'Different')

    def test_on_update_change_address_data_if_similar_address_not_exists_and_address_have_only_one_user(self):
        payload = {'address': {'city': 'Кстово', 'country': 'Россия'}}
        
        serializer = UserSerializer(self.user, data=payload, partial=True)

        self.assertTrue(serializer.is_valid())
        saved_obj = serializer.save()

        self.assertEqual(saved_obj.address, self.address)
        self.assertEqual(Address.objects.count(), 1)
        self.assertEqual(saved_obj.address.city, 'Кстово')
        self.assertEqual(saved_obj.address.country, 'Россия')

