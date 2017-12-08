from distutils.util import strtobool

from django.contrib.auth.models import Group
from django.db.models import Count, Q
from rest_framework import generics, viewsets
from rest_framework import permissions

from .models import User
from .permissions import (ActivateFirstIfInactive,
                          CantEditSuperuserIfNotSuperuser)
from .serializers import (GroupDetailSerializer, GroupSerializer,
                          UserGroupsSerializer, UserSerializer)
from .utils import convert_date

# Need to set permissions explicitly, because docs says:
# Note: when you set new permission classes through class attribute or
# decorators you're telling the view to ignore the default list set
# over the settings.py file.

class UserViewSet(viewsets.ModelViewSet):
    """
    retrieve:
    Return requested user.
    
    list:
    Return a list of all existing users.

    create:
    Create a new user.

    update:
    Updates desired user.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    lookup_field = 'username'
    permission_classes = (permissions.IsAuthenticated,
                          permissions.DjangoModelPermissions,
                          ActivateFirstIfInactive,
                          CantEditSuperuserIfNotSuperuser)


class GroupViewSet(viewsets.ModelViewSet):
    """
    retrieve:
    Return requested group.
    
    list:
    Return a list of all existing groups.

    create:
    Create a new group.

    update:
    Updates desired group.

    partial_update:
    Updates desired group.
    
    When using PATCH request to manage group's users you must provide 'action'
    field which can be either 'add' or 'remove'
    """
    queryset = Group.objects.annotate(users_count=Count('user'))
    serializer_class = GroupSerializer
    lookup_field = 'name'

    def get_serializer_class(self):
        if self.action in ['retrieve', 'update', 'partial_update']:
            return GroupDetailSerializer
        else:
            return super().get_serializer_class()


class UserGroupsView(generics.RetrieveUpdateAPIView):
    """
    get:
    Returns user's groups

    update:
    Updates user groups.
    """
    queryset = User.objects.all()
    serializer_class = UserGroupsSerializer
    # disabling PATCH method
    http_method_names = ['get', 'put', 'options', 'head']
    lookup_field = 'username'
    lookup_url_kwarg = 'username'


class SearchView(generics.ListAPIView):
    """View allow users to perform user search either entering part of user's
    name or by entering full birth date or full email.
    """

    serializer_class = UserSerializer

    def get_queryset(self):
        """Filtering Query against user provided params.

        If Search query is empty whole queryset are returned.
        Additional filter by 'is_active' field allowed only for admins,
        no success if not admin user try to apply this filter.
        """
        queryset = User.objects.all()
        active_filter = self.request.query_params.get('is_active')
        if active_filter is not None:
            # using permission for view full info here because it's meant that
            # user is admin and can access is_active_filter
            if self.request.user.has_perm('profiles.view_full_info'):
                # We need to convert provided active_filter to boolean,
                # built-in function from distutils.util is used in convertion.
                # If active_filter is neither True nor False, nothing will happen.
                try:
                    active_filter = bool(strtobool(active_filter))
                    queryset = queryset.filter(is_active=active_filter)
                except ValueError:
                    pass
        query = self.request.query_params.get('q')
        if query is not None:
            # If we chain birthday as another Q object filter we will keep
            # getting erorrs that passed query does not correspond to db date
            # format if passed param isn't date in format '%Y-%m-%d' thus every
            # request that meant to search by either part of the name or by
            # email will raise error.
            # To avoid this, we try to convert query string to date explicitly
            # if everything is ok, we just filter query against date object we
            # got after converting.
            # Otherwise we just chain other filters.

            input_formats = ['%Y-%m-%d', '%d-%m-%Y', '%d-%m-%y']
            date = convert_date(input_formats, query)

            if date is not None:
                queryset = queryset.filter(birthday=date)
            else:
                queryset = queryset.filter(
                    Q(first_name__icontains=query) |
                    Q(last_name__icontains=query) |
                    Q(email=query)
                )
        return queryset
