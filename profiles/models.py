from django.contrib.auth.models import AbstractUser
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
    "Extended User model"""

    birthday = models.DateField(help_text='User\'s birthday.')
    address = models.ForeignKey(Address, help_text='User\'s address.')
    last_update = models.DateTimeField(
        auto_now=True, help_text='Date of last information update.'
    )

    # Redifine some existing fields here to reduce visual noise in serializers.

    first_name = models.CharField(max_length=128,
                                  help_text='User\'s first name')
    last_name = models.CharField(max_length=128,
                                 help_text='User\'s last name')
    email = models.EmailField(help_text='User\'s email address')

    class Meta:
        permissions = (
            ('view_full_info', "Can see full users info"),
        )

    def __str__(self):
        return self.username
