#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
from django.utils import timezone
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin
import re

from . import models


class UsageMiddleware(MiddlewareMixin):
    """
    This middleware class updates tracking information in the database on each
    request to the API. The information stored is last access time for each
    user and last access details about each resource (user, time, resource
    name, method). Super users are excluded from resource tracking.
    """
    def process_view(self, request, view_func, *args, **kwargs):
        # If user authenticates with a token, the user identity can not be
        # known in middleware at this point. Only record time and resource and
        # do the actual logging after the request runs.
        if re.match(r'^/%s.*$' % settings.REST_API_URL, request.path):
            request._usage = {
                'resource': view_func.func_name,
                'now': timezone.now(),
            }

    def process_response(self, request, response):
        data = getattr(request, '_usage', None)
        if not data:
            return response

        user = None
        if request.user and request.user.is_authenticated():
            user = request.user
            user.last_connected = data['now']
            user.save()

            if request.user.is_superuser:
                # We don't want to log accesses by superusers
                return response

        models.ResourceUsage.objects.update_or_create(
            resource=data['resource'],
            method=request.method,
            defaults={'user': user, 'time': data['now']}
        )

        return response
