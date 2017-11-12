from django.test import TestCase
from django.contrib.auth.models import User


from .models import Profile


class ProfileModelTestCase(TestCase):

    def setUp(self):
        self.user = User.objects.create_user('testuser',
                                             email='test@email.com',
                                             password='testpassword')

    def test_can_create_profile_instances_when_user_created(self):
        self.assertEqual(Profile.objects.count(), 1)
        profile = Profile.objects.all().first()
        self.assertEqual(profile, self.user.profile)
        User.objects.create_user('testuser2',
                                 email='test@email2.com',
                                 password='testpassword2')
        self.assertEqual(Profile.objects.count(), 2)



