from django.contrib.auth.models import Group
from django.db import transaction
from django.forms.models import model_to_dict

from rest_framework import serializers
from rest_framework import status

from .models import User, Address


class UserGroupsSerializer(serializers.Serializer):
    """Serializer for user's group, used in /users/username/groups endpoint"""

    groups = serializers.SlugRelatedField(many=True, slug_field='name',
                                          queryset=Group.objects.all())

    @transaction.atomic
    def update(self, instance, validated_data):
        """
        Method will clear user groups and then add new.
        """
        groups = validated_data.pop('groups', None)
        if groups is not None:
            instance.groups.set(groups)
            return instance

class GroupDetailSerializer(serializers.ModelSerializer):

    """
    Serializer for group's details.
    """

    url = serializers.HyperlinkedIdentityField(view_name='api:group-detail',
                                               lookup_field='name',
                                               read_only=True)
    users_count = serializers.IntegerField(read_only=True)
    users = serializers.SlugRelatedField(many=True, slug_field='username',
                                         queryset=User.objects.all(),
                                         source='user_set')
    class Meta:
        model = Group
        fields = ('url', 'name', 'users_count', 'users')

    @transaction.atomic
    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.save()
        users = validated_data.get('user_set', None)
        if users is not None:
            instance.user_set.set(users)
            # Handle annotation:
            instance.users_count = len(users)
        return instance


class GroupSerializer(serializers.ModelSerializer):
    """
    Group list serializer.

    users_count - field that represents ammount of users in group, passed from
    view as annotation.
    """
    url = serializers.HyperlinkedIdentityField(view_name='api:group-detail',
                                               lookup_field='name')
    users_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Group
        fields = ('url', 'name', 'users_count',)

    def create(self, validated_data):
        # we need to override create method to handle annotation
        instance = Group.objects.create(**validated_data)
        instance.users_count = 0
        return instance


class AddressSerializer(serializers.ModelSerializer):

    class Meta:
        model = Address
        fields = ('zip_code', 'country', 'city', 'district', 'street')


class UserSerializer(serializers.ModelSerializer):
    """
    User status aware serializer, if user is not admin - will return
    basic fields representation.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        basic_user_fields = {'first_name', 'url', 'last_name', 'username',
                             'email', 'birthday', 'address', 'groups'}

        request = self.context.get('request')
        # Permission to check.
        permission = 'profiles.view_full_info'
        if request is None or not request.user.has_perm(permission):
            restricted_fields = set(self.fields) - basic_user_fields
            for field in restricted_fields:
                self.fields.pop(field)


    url = serializers.HyperlinkedIdentityField(view_name='api:user-detail',
                                               lookup_field='username')
    address = AddressSerializer()
    groups = serializers.SlugRelatedField(
        read_only=True,
        slug_field='name',
        many=True
    )

    class Meta:
        model = User
        depth = 1
        fields = ('id', 'url', 'first_name', 'last_name', 'username',
                  'password', 'email', 'birthday', 'is_active',
                  'address', 'groups', 'date_joined', 'last_update')

        extra_kwargs = {'password': {'write_only': True},
                        'date_joined': {'read_only': True,
                                        'format': '%Y-%m-%d %H:%M:%S'},
                        'last_update': {'read_only': True,
                                        'format': '%Y-%m-%d %H:%M:%S'},
                        'is_active': {'default': True}
                       }

    # Defining create and update method because we have customized the way
    # nested address object looks and placed it as nested serialzier, so
    # we can't use default implementation for objects with fk.

    @transaction.atomic
    def create(self, validated_data):
        """Method to create user instance with coresponding address"""

        address_data = validated_data.pop('address')
        address, _ = Address.objects.get_or_create(**address_data)

        user = User.objects.create_user(**validated_data, address=address)
        return user

    @transaction.atomic
    def update(self, instance, validated_data):
        """Method to update user instance and address"""

        address_data = validated_data.pop('address', None)

        if address_data is not None:
            # look if updated address already exists in database
            address = instance.address
            existing_data = model_to_dict(address)
            existing_data.pop('id')
            existing_data.update(address_data)
            try:
                obj = Address.objects.get(**existing_data)
                if not obj == address:
                    if address.user_set.count() == 1:
                        address.delete()
                    instance.address = obj
            except Address.DoesNotExist:
                if address.user_set.count() == 1:
                    for attr, value in address_data.items():
                        setattr(address, attr, value)
                    address.save()
                else:
                    instance.address = Address.objects.create(**existing_data)

        password = validated_data.pop('password', None)

        if password is not None:
            instance.set_password(password)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance
