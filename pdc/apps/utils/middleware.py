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

from . import messenger


logger = logging.getLogger(__name__)


class MessagingMiddleware(MiddlewareMixin):
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


class RestrictAdminMiddleware(MiddlewareMixin):
    """
    Restricts access to the admin page to only logged-in users with a certain user-level.
    """
    def process_request(self, request):
        if request.user.is_authenticated() and request.path.startswith(reverse('admin:index')):
            if not (request.user.is_active and request.user.is_superuser):
                return HttpResponseRedirect("/%s%s/" % (settings.REST_API_URL, settings.REST_API_VERSION))
