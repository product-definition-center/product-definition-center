#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
import logging
from django.conf import settings
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.utils.deprecation import MiddlewareMixin


logger = logging.getLogger(__name__)


class RestrictAdminMiddleware(MiddlewareMixin):
    """
    Restricts access to the admin page to only logged-in users with a certain user-level.
    """
    def process_request(self, request):
        if request.user.is_authenticated and request.path.startswith(reverse('admin:index')):
            if not (request.user.is_active and request.user.is_superuser):
                return HttpResponseRedirect("/%s%s/" % (settings.REST_API_URL, settings.REST_API_VERSION))
