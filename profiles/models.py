from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.validators import RegexValidator
from django.db import models


class Address(models.Model):
    """Model represents User's address"""
    # Should we create separate different models for each field in purpose of
    # normalization? Maybe, but i wouldn't do this.
    zip_code = models.CharField(max_length=6,
                                validators=[RegexValidator(r'^\d{6,6}$')])
    country = models.CharField(max_length=128)
    city = models.CharField(max_length=128)
    district = models.CharField(max_length=128)
    street = models.CharField(max_length=128)


class User(AbstractUser):
    """Extended User model"""
    birthday = models.DateField()
    address = models.ForeignKey(Address, related_name='users')
    last_update = models.DateTimeField(auto_now=True)

    class Meta:
        permissions = (
            ('view_full_info', "Can see full users info"),
        )

    def __str__(self):
        return self.username

