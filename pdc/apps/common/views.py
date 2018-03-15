#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
import json
import sys

from distutils.version import LooseVersion

from django import get_version
from django.shortcuts import render
from django.views import defaults
from django.http import HttpResponse

from pdc.apps.auth.permissions import APIPermission
from pdc.apps.common.constants import PUT_OPTIONAL_PARAM_WARNING

from rest_framework import viewsets, mixins, status

from .models import Arch, SigKey, Label
from . import viewsets as pdc_viewsets
from .serializers import LabelSerializer, ArchSerializer, SigKeySerializer
from .filters import LabelFilter, SigKeyFilter
from . import handlers

django_version = LooseVersion(get_version())


class LabelViewSet(pdc_viewsets.PDCModelViewSet):
    """
    ##Overview##

    This page shows the usage of the **Label API**, please see the
    following for more details.

    ##Test tools##

    You can use ``curl`` in terminal, with -X _method_ (GET|POST|PUT|PATCH|DELETE),
    -d _data_ (a json string). or GUI plugins for
    browsers, such as ``RESTClient``, ``RESTConsole``.
    """
    serializer_class = LabelSerializer
    queryset = Label.objects.all().order_by('id')
    filter_class = LabelFilter

    doc_create = """
        ### CREATE

        __Method__:
        POST

        __URL__: $LINK:label-list$

        __Data__:

        %(WRITABLE_SERIALIZER)s

        __Response__:

        %(SERIALIZER)s

        __Example__:

            curl -H "Content-Type: application/json"  -X POST -d '{"name": "label1", "description": "label1 description"}' $URL:label-list$
            # output
            {"url": "$URL:label-detail:1$", "name": "label1", "description": "label1 description"}
    """

    doc_list = """
        ### LIST

        __Method__:
        GET

        __URL__: $LINK:label-list$

        __Query Params__:

        %(FILTERS)s

        __Response__: a paged list of following objects

        %(SERIALIZER)s

        __Example__:

            curl -H "Content-Type: application/json"  -X GET $URL:label-list$
            # output
            {
                "count": 284,
                "next": "$URL:label-list$?page=2",
                "previous": null,
                "results": [
                    {
                        "url": "$URL:label-detail:1$",
                        "name": "label1",
                        "description": "label1 description"
                    },
                    {
                        "url": "$URL:label-detail:2$",
                        "name": "label2",
                        "description": "label2 description"
                    },
                    ...
                ]
            }

        With query params:

            curl -H "Content-Type: application/json"  -G $URL:label-list$ -d name=label1
            {
                "count": 1,
                "next": null,
                "previous": null,
                "results": [
                    {
                        "url": "$URL:label-list:1$",
                        "name": "label1",
                        "description": "label1 description"
                    }
                ]
            }
    """

    doc_retrieve = """
        ### RETRIEVE

        __Method__:
        GET

        __URL__: $LINK:label-detail:instance_pk$

        __Response__:

        %(SERIALIZER)s

        __Example__:

            curl -H "Content-Type: application/json" $URL:label-detail:1$
            # output
            {"url": "$URL:label-detail:1$", "name": "label1", "description": "label1 description"}
    """

    doc_update = """
        ### UPDATE

        __Method__: `PUT`, `PATCH`

        __URL__: $LINK:label-detail:instance_pk$

        __Data__:

        %(WRITABLE_SERIALIZER)s

        __Response__:

        %(SERIALIZER)s

        __Example__:

        PUT:

            curl -X PUT -d '{"name": "new_name", "description": "new_description"}' -H "Content-Type: application/json" $URL:label-detail:1$
            # output
            {"url": "$URL:label-detail:1$", "name": "new_name", "description": "new_description"}

        PATCH:

            curl -X PATCH -d '{"description": "new_description"}' -H "Content-Type: application/json" $URL:label-detail:1$
            # output
            {"url": "$URL:label-detail:1$", "name": "label1", "description": "new_description"}
    """

    doc_destroy = """
        ### DELETE

        __Method__: `DELETE`

        __URL__: $LINK:label-detail:instance_pk$

        __Response__:

            STATUS: 204 NO CONTENT

        __Example__:

            curl -X DELETE -H "Content-Type: application/json" $URL:label-detail:1$
    """


class ArchViewSet(pdc_viewsets.ChangeSetCreateModelMixin,
                  pdc_viewsets.ConditionalProcessingMixin,
                  pdc_viewsets.StrictQueryParamMixin,
                  mixins.ListModelMixin,
                  viewsets.GenericViewSet):
    """
    ##Overview##

    This page shows the usage of the **Arch API**, please see the
    following for more details.

    ##Test tools##

    You can use ``curl`` in terminal, with -X _method_ (GET|POST|PUT|PATCH|DELETE),
    -d _data_ (a json string). or GUI plugins for
    browsers, such as ``RESTClient``, ``RESTConsole``.
    """
    serializer_class = ArchSerializer
    queryset = Arch.objects.all().order_by('id')
    lookup_field = 'name'
    permission_classes = (APIPermission,)

    doc_list = """
        ### LIST

        __Method__:
        GET

        __URL__: $LINK:arch-list$

        __Response__: a paged list of following objects

        %(SERIALIZER)s

        __Example__:

            curl -H "Content-Type: application/json"  -X GET $URL:arch-list$
            # output
            {
                "count": 47,
                "next": "$URL:arch-list$?page=2",
                "previous": null,
                "results": [
                    {
                        "name": "alpha"
                    },
                    {
                        "name": "alphaev4",
                    },
                    ...
                ]
            }
    """

    doc_create = """
        ### CREATE

        __Method__:
        POST

        __URL__: $LINK:arch-list$

        __Data__:

        %(WRITABLE_SERIALIZER)s

        __Response__:

        %(SERIALIZER)s

        __Example__:

            curl -H "Content-Type: application/json" -X POST -d '{"name": "arm"}' $URL:arch-list$
            # output
            {"name": "arm"}
    """


class SigKeyViewSet(pdc_viewsets.StrictQueryParamMixin,
                    pdc_viewsets.NotificationMixin,
                    mixins.ListModelMixin,
                    mixins.RetrieveModelMixin,
                    pdc_viewsets.ChangeSetCreateModelMixin,
                    pdc_viewsets.ChangeSetUpdateModelMixin,
                    viewsets.GenericViewSet):
    """
    ##Overview##

    This page shows the usage of the **SigKey API**, please see the
    following for more details.

    ##Test tools##

    You can use ``curl`` in terminal, with -X _method_ (GET|POST|PUT|PATCH|DELETE),
    -d _data_ (a json string). or GUI plugins for
    browsers, such as ``RESTClient``, ``RESTConsole``.
    """
    serializer_class = SigKeySerializer
    queryset = SigKey.objects.all().order_by('id')
    filter_class = SigKeyFilter
    lookup_field = 'key_id'
    docstring_macros = PUT_OPTIONAL_PARAM_WARNING
    permission_classes = (APIPermission,)

    doc_list = """
        ### LIST

        __Method__:
        GET

        __URL__: $LINK:sigkey-list$

        __Query Params__:

        %(FILTERS)s

        __Response__: a paged list of following objects

        %(SERIALIZER)s
    """

    doc_retrieve = """
        ### RETRIEVE

        __Method__:
        GET

        __URL__: $LINK:sigkey-detail:key_id$

        __Response__:

        %(SERIALIZER)s
    """

    doc_update = """
        ### UPDATE
        %(PUT_OPTIONAL_PARAM_WARNING)s

        __Method__: `PUT`, `PATCH`

        %(WRITABLE_SERIALIZER)s

        All keys are optional for `PATCH` request, but at least one must be
        specified.

        __URL__: $LINK:sigkey-detail:key_id$

        __Response__:

        %(SERIALIZER)s
    """

    doc_create = """
        ### CREATE

        __Method__:
        POST

        __URL__: $LINK:sigkey-list$

        __Data__:

        %(WRITABLE_SERIALIZER)s

        __Response__:

        %(SERIALIZER)s
    """


def home(request):
    return render(request, "home/index.html")


def handle404(request):
    if 'application/json' in request.META.get('HTTP_ACCEPT', ''):
        return HttpResponse(json.dumps(handlers.NOT_FOUND_JSON_RESPONSE),
                            status=status.HTTP_404_NOT_FOUND,
                            content_type='application/json')

    if django_version < LooseVersion('1.9'):
        return defaults.page_not_found(request)
    else:
        exc_class, exc, tb = sys.exc_info()
        return defaults.page_not_found(request, exc)
