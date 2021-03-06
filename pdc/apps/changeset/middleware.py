#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
import sys
import logging

from django.db import transaction
from . import models

# trap wrong HTTP methods
from django.http import HttpResponse
from django.conf import settings
from django.core.mail import mail_admins
from django.urls import reverse
from django.utils import timezone
from django.utils.deprecation import MiddlewareMixin
from rest_framework import status
import json

logger = logging.getLogger(__name__)


class ChangesetMiddleware(MiddlewareMixin):
    """
    Create a new changeset for each request. It is accessible via
    `request.changeset`. If the view function ends sucessfully, the changeset
    is commited if there are any changes associated with it.
    """

    def _may_announce_big_change(self, changeset, request):
        if (not hasattr(settings, 'CHANGESET_SIZE_ANNOUNCE') or
                not isinstance(settings.CHANGESET_SIZE_ANNOUNCE, int) or
                len(changeset.tmp_changes) < settings.CHANGESET_SIZE_ANNOUNCE):
            return

        author = str(changeset.author)
        whitelist = getattr(settings, 'BIG_CHANGE_AUTHORS_WHITELIST', set())

        # Skip whitelisted authors.
        if author in whitelist:
            return

        end_point = request.path.replace("%s%s/" % (settings.REST_API_URL, settings.REST_API_VERSION), '').strip('/')
        params_dict = {
            'author': author,
            'author_email': changeset.author.email if changeset.author else '',
            'end_point': end_point,
            'url': request.build_absolute_uri(reverse('changeset/detail', kwargs={'id': changeset.id})),
            'change_number': len(changeset.tmp_changes),
            'domain': request.build_absolute_uri('/')[:-1]
        }
        print params_dict
        mail_title = """Big change happened in PDC (%(domain)s) DB""" % params_dict
        mail_body = """
        <html>
        <p><b>Author</b>:        %(author)s </p>
        <p><b>Author Email</b>:  %(author_email)s </p>
        <p><b>Change Number</b>: %(change_number)s </p>
        <p><b>Change Link</b>:   <a href="%(url)s">%(url)s</a>
        </html>
        """ % params_dict
        mail_admins(mail_title, None, html_message=mail_body)

    def process_view(self, request, view_func, view_args, view_kwargs):
        user = None
        if request.user.is_authenticated:
            user = request.user

        if request.method == "GET":
            logger.debug("Start query request on the view %s." % view_func.__name__)
            # NOTE: We do not need create a changeset when we just SELECT somw records.
            response = view_func(request, *view_args, **view_kwargs)
        else:
            # trap the request and give response when the method is not defined in HTTP/1.1
            if request.method not in ["HEAD", "POST", "PUT", "DELETE", "TRACE", "CONNECT", "PATCH", "OPTIONS"]:
                logger.error('Wrong method %s specified when calling %s', request.method.decode("utf-8"), request.path)
                response_data = json.dumps({"detail": 'Method "{method}" not allowed.'.format(method=request.method)},
                                           ensure_ascii=False)
                response = HttpResponse(response_data, content_type='application/json')
                response.status_code = status.HTTP_405_METHOD_NOT_ALLOWED
                return response

            logger.debug("Start write request on the view %s." % view_func.__name__)
            try:
                with transaction.atomic():
                    comment = request.META.get("HTTP_PDC_CHANGE_COMMENT", None)
                    request.changeset = models.Changeset(author=user, comment=comment)
                    request.changeset.requested_on = timezone.now()
                    response = view_func(request, *view_args, **view_kwargs)
                    # response.exception=True means there is an error occurs.
                    if getattr(response, 'exception', 0) or (
                        hasattr(response, 'status_code') and response.status_code >= 400
                    ):
                        # avoid recording changeset on server error, also
                        # abort the transaction so that no modifications are
                        # done to database
                        request.changeset.reset()
                        transaction.set_rollback(True)
                    else:
                        request.changeset.commit()
                        self._may_announce_big_change(request.changeset, request)
            except Exception:
                # NOTE: catch all errors that were raised by view.
                # And log the trace back to the file.
                logger.error('View Function Error: %s', request.path,
                             exc_info=sys.exc_info())
                # we do not want to break the default exception processing chains,
                # so re-raise the exception to the upper level.
                raise

        return response
