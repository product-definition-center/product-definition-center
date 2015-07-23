#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
import logging

from . import messenger

logger = logging.getLogger(__name__)


class MessagingMiddleware(object):
    """
    Create a messaging list for each request. It is accessible via
    `request.messagings`. If the request ends sucessfully, the messager
    could send all the messages in it.
    """

    def process_request(self, request):
        request.messagings = []

    def process_response(self, request, response):
        if not getattr(response, 'exception', 0) and response.status_code < 400:
            if hasattr(request, 'messagings'):
                for topic, msg in request.messagings:
                    messenger.send_message(topic=topic, msg=msg)
        request.messagings = None
        return response
