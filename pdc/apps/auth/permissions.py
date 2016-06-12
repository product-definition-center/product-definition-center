import re
from restfw_composed_permissions.base import BasePermissionComponent, BaseComposedPermision
from restfw_composed_permissions.generic.components import AllowAll
from django.conf import settings

from pdc.apps.auth.models import Resource, GroupResourcePermission
from pdc.apps.utils.utils import read_permission_for_all


class APIPermissionComponent(BasePermissionComponent):
    """
    Allow only anonymous requests.
    """

    def has_permission(self, permission, request, view):
        if request.user.is_superuser or (hasattr(settings, 'DISABLE_RESOURCE_PERMISSION_CHECK') and
                                         settings.DISABLE_RESOURCE_PERMISSION_CHECK):
            return True
        api_name = request.path.replace("%s%s/" % (settings.REST_API_URL, settings.REST_API_VERSION), '').strip('/')
        internal_permission = self._convert_permission(request.method)
        if not internal_permission or (read_permission_for_all() and internal_permission == 'read'):
            return True
        return self._has_permission(internal_permission, request.user, str(view.__class__), api_name)

    def _has_permission(self, internal_permission, user, view, api_name):
        resources = Resource.objects.filter(view=view).all()
        resource = None

        if len(resources) == 1:
            resource = resources[0]
        elif len(resources) > 1:
            # multiple api map to one view
            resources = [obj for obj in Resource.objects.filter(view=view, name=api_name).all()]
            if len(resources) == 1:
                resource = resources[0]
            else:
                # maybe resouce name is regexp
                resource = self._try_regexp_resource_match(api_name, resources)
        if not resource:
            # not restrict access to resource that is not in permission control
            result = True
        else:
            group_id_list = [group.id for group in user.groups.all()]
            result = GroupResourcePermission.objects.filter(
                group__id__in=group_id_list, resource_permission__resource=resource,
                resource_permission__permission__name=internal_permission).exists()

        return result

    @staticmethod
    def _try_regexp_resource_match(api_name, resources):
        result = None
        api_str_list = api_name.split('/')
        if len(api_str_list) > 1 and resources:
            for resource_obj in resources:
                if re.match(resource_obj.name, api_name):
                    result = resource_obj
                    break
        return result

    @staticmethod
    def _convert_permission(in_method):
        conversion_dict = {'patch': 'update',
                           'put': 'update',
                           'get': 'read',
                           'delete': 'delete',
                           'post': 'create'}
        return conversion_dict.get(in_method.lower())


class APIPermission(BaseComposedPermision):

    def global_permission_set(self):
        return APIPermissionComponent

    def object_permission_set(self):
        return AllowAll
