#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
import sys
import logging

from datetime import datetime
from django.db import transaction
from . import models

# trap wrong HTTP methods
from django.http import HttpResponse
from rest_framework import status
import json

logger = logging.getLogger(__name__)


class ChangesetMiddleware(object):
    """
    Create a new changeset for each request. It is accessible via
    `request.changeset`. If the view function ends sucessfully, the changeset
    is commited iff there are any changes associated with it.
    """

    def process_view(self, request, view_func, view_args, view_kwargs):
        user = None
        if request.user.is_authenticated():
            user = request.user

        if request.method == "GET":
            logger.debug("Start query request on the view %s." % view_func.__name__)
            # NOTE: We do not need create a changeset when we just SELECT somw records.
            response = view_func(request, *view_args, **view_kwargs)
        else:
            # trap the request and give response when the method is not defined in HTTP/1.1
            if request.method not in ["HEAD", "POST", "PUT", "DELETE", "TRACE", "CONNECT", "PATCH", "OPTIONS"]:
                logger.error('Wrong method %s specified when calling %s', request.method.decode("utf-8"), request.path,
                             exc_info=sys.exc_info())
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
                    request.changeset.requested_on = datetime.now()
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
            except:
                # NOTE: catch all errors that were raised by view.
                # And log the trace back to the file.
                logger.error('View Function Error: %s', request.path,
                             exc_info=sys.exc_info())
                # we do not want to break the default exception processing chains,
                # so re-raise the exception to the upper level.
                raise

        return response
