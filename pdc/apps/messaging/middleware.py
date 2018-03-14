#
# Copyright (c) 2018 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
from django.utils.deprecation import MiddlewareMixin
from django.apps import apps


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
                extra_fields = {
                    'author': request.user.username,
                    'comment': request.META.get("HTTP_PDC_CHANGE_COMMENT", None),
                }
                if hasattr(request, 'changeset') and request.changeset.pk:
                    extra_fields.update({
                        'changeset_id': request.changeset.pk,
                        'committed_on': str(request.changeset.committed_on),
                    })
                for topic, msg in request._messagings:
                    msg.update(extra_fields)

                config = apps.get_app_config('messaging')
                config.messenger.send_messages(request._messagings)
        request._messagings = None
        return response
