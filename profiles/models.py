from django.contrib.auth.models import User
from django.db import models


class Profile(models.Model):
    ADMIN = 1
    ORDINARY = 0
    PROFILE_TYPES = (
        (ADMIN, 'Administrator'),
        (ORDINARY, 'Ordinary')
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_type = models.IntegerField(choices=PROFILE_TYPES)
    birthday = models.DateField()
    address = models.CharField(max_length=128)
    last_update = models.DateTimeField(auto_now=True)


