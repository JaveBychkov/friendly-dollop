from django.conf.urls import url

from rest_framework import routers
from rest_framework.urlpatterns import format_suffix_patterns

from . import views


router = routers.SimpleRouter()
router.register(r'users', views.UserViewSet)
router.register(r'groups', views.GroupViewSet)

urlpatterns = [
    url(r'^users/search$', views.SearchView.as_view(), name='search'),
    url(r'^users/(?P<username>[\w-]+)/groups/$',
        views.UserGroupsView.as_view(),
        name='user-groups')
]

urlpatterns += router.urls

urlpatterns = format_suffix_patterns(urlpatterns, allowed=['json', 'html'])
