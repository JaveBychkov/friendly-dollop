from django.contrib.auth.models import Group
from django.db import transaction

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
        Method will clear user groups and then add new, provided groups.
        """
        groups = validated_data.pop('groups', None)
        if groups is not None:
            instance.groups.clear()
            for group in groups:
                instance.groups.add(group)
            return instance
        raise serializers.ValidationError(detail='Bad Request')

class GroupDetailSerializer(serializers.ModelSerializer):

    """
    Serializer for group's details, provides different actions for PATCH
    and PUT requests

    If PATCH request is used serializer will check for presistance of action
    field in case of updating group's members, if there is no users to update
    presistance check of action field is ommited
    """

    url = serializers.HyperlinkedIdentityField(view_name='api:group-detail',
                                               lookup_field='name',
                                               read_only=True)
    users_count = serializers.IntegerField(read_only=True)
    users = serializers.SlugRelatedField(many=True, slug_field='username',
                                         queryset=User.objects.all(),
                                         source='user_set')
    action = serializers.CharField(write_only=True, default='')

    def validate(self, data):
        """Validate that admin passed 'action' if he want to update users"""
        if self.partial:
            if data.get('user_set') is not None and not data.get('action', ''):
                raise serializers.ValidationError(
                    detail='You must provide "action" value if you want to \
                    update users using "PATCH" request'
                )
        return data

    def validate_action(self, value):
        """
        Validated that provided action is one of the following : add, remove or
        blank
        """
        if self.partial:
            if value.lower() not in ['add', 'remove', '']:
                raise serializers.ValidationError(
                    detail='Action must be either "add" or "remove"'
                )
        return value

    class Meta:
        model = Group
        fields = ('url', 'name', 'users_count', 'users', 'action')

    def update_on_put(self, instance, users):
        """Update strategy used on PUT request"""
        instance.user_set.clear()
        for user in users:
            instance.user_set.add(user)
        # Can avoid hitting database on PUT request.
        instance.users_count = len(users)

    def update_on_patch(self, instance, users, action):
        """Update strategy used on PATCH request"""
        method = getattr(instance.user_set, action)
        for user in users:
            method(user)
        # Counting new ammount of users, because annotation will not be updated.
        instance.users_count = instance.user_set.count()

    @transaction.atomic
    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        users = validated_data.get('user_set', [])
        action = validated_data.get('action', '')
        if self.partial and action:
            self.update_on_patch(instance, users, action)
        elif not self.partial:
            self.update_on_put(instance, users)
        instance.save()
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
        exclude = ('id',)


class UserSerializer(serializers.ModelSerializer):
    """
    User status aware serializer, if user is not admin - will return
    basic fields representation.
    """

    basic_user_fields = {'first_name', 'url', 'last_name', 'username',
                         'email', 'birthday', 'address', 'groups'}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        request = self.context.get('request')
        # Permission to check.
        permission = 'profiles.view_full_info'
        # because of lazy if's statements evaluation request.user will not
        # raise KeyError if Request object is not provided.
        if request is None or not request.user.has_perm(permission):
            restricted_fields = set(self.fields) - self.basic_user_fields
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
                  'password', 'email', 'birthday', 'address', 'groups',
                  'is_active', 'date_joined', 'last_update')

        extra_kwargs = {'password': {'write_only': True},
                        'date_joined': {'read_only': True,
                                        'format': '%Y-%m-%d %H:%M:%S'},
                        'last_update': {'read_only': True,
                                        'format': '%Y-%m-%d %H:%M:%S'},
                        'email': {'allow_blank': False, 'required': True},
                        'first_name': {'allow_blank': False, 'required': True},
                        'last_name': {'allow_blank': False, 'required': True},
                       }

    # TODO: Find a way to use existing Address serializer to create new address
    # or update existing. Some implementations i've already tried raises drf
    # exceptions.

    @transaction.atomic
    def create(self, validated_data):
        address = validated_data.pop('address')
        address = Address.objects.create(**address)
        user = User.objects.create_user(**validated_data, address=address)
        return user

    @transaction.atomic
    def update(self, instance, validated_data):
        address_data = validated_data.pop('address', None)

        if address_data is not None:
            address = instance.address
            address.zip_code = address_data.get('zip_code', address.zip_code)
            address.country = address_data.get('country', address.country)
            address.city = address_data.get('city', address.city)
            address.district = address_data.get('district', address.district)
            address.street = address_data.get('street', address.street)
            address.save()

        instance.first_name = validated_data.get('first_name',
                                                 instance.first_name)
        instance.last_name = validated_data.get('last_name',
                                                instance.last_name)
        instance.username = validated_data.get('username', instance.username)
        instance.email = validated_data.get('email', instance.email)
        instance.birthday = validated_data.get('birthday', instance.birthday)
        instance.is_active = validated_data.get('is_active',
                                                instance.is_active)

        password = validated_data.get('password')

        if password is not None:
            instance.set_password(password)

        instance.save()
        return instance
