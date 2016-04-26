#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
import logging
import django
import inspect
from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect

from . import messenger
from pdc.apps.utils.SortedRouter import router
from pdc.apps.auth.models import ResourcePermission, ActionPermission, Resource

logger = logging.getLogger(__name__)


class MessagingMiddleware(object):
    """
    Create a messaging list for each request. It is accessible via
    `request._messagings`. If the request ends sucessfully, the messager
    could send all the messages in it.
    """

    def process_request(self, request):
        request._messagings = []

    def process_response(self, request, response):
        if not getattr(response, 'exception', 0) and response.status_code < 400:
            if hasattr(request, '_messagings'):
                for topic, msg in request._messagings:
                    messenger.send_message(topic=topic, msg=msg)
        request._messagings = None
        return response


class ResourceCollectingMiddleware(object):
    API_WITH_NO_PERMISSION_CONTROL = set(['changesets', 'rpc/where-to-file-bugs', 'images', 'release-types',
                                          'variant-types', 'release-variant-types', 'content-delivery-repo-families',
                                          'content-delivery-content-categories', 'content-delivery-content-formats',
                                          'content-delivery-services', 'auth/permissions', 'auth/current-user'])

    def __init__(self):
        action_to_obj_dict = {}

        for action in ('update', 'create', 'delete', 'read'):
            action_to_obj_dict[action] = ActionPermission.objects.get(name=action)

        for prefix, view_set, basename in router.registry:
            if prefix in self.API_WITH_NO_PERMISSION_CONTROL:
                continue
            resource_obj, created = Resource.objects.get_or_create(name=prefix, view=str(view_set))
            if created:
                logger.info("Created resource %s" % prefix)
            for name, method in inspect.getmembers(view_set, predicate=inspect.ismethod):
                if name.lower() in ['update', 'create', 'destroy', 'list', 'partial_update', 'retrieve']:
                    action_permission = action_to_obj_dict[self._convert_method_to_action(name.lower())]
                    _, created = ResourcePermission.objects.get_or_create(resource=resource_obj,
                                                                          permission=action_permission)
                    if created:
                        logger.info("Created resource permission item with resource '%s' and action '%s" %
                                    (prefix, action_permission.name))
        raise django.core.exceptions.MiddlewareNotUsed

    def _convert_method_to_action(self, method):
        return {'update': 'update',
                'partial_update': 'update',
                'list': 'read',
                'retrieve': 'read',
                'create': 'create',
                'destroy': 'delete'}.get(method)


class RestrictAdminMiddleware(object):
    """
    Restricts access to the admin page to only logged-in users with a certain user-level.
    """
    def process_request(self, request):
        if request.user.is_authenticated() and request.path.startswith(reverse('admin:index')):
            if not (request.user.is_active and request.user.is_superuser):
                return HttpResponseRedirect("/%s%s/" % (settings.REST_API_URL, settings.REST_API_VERSION))
