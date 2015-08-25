#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
from django.shortcuts import render

from kobo.django.views.generic import ListView

from rest_framework import viewsets, mixins

from contrib.bulk_operations import bulk_operations

from .models import Arch, SigKey, Label
from . import viewsets as pdc_viewsets
from .serializers import LabelSerializer, ArchSerializer, SigKeySerializer
from .filters import LabelFilter, SigKeyFilter


class ArchListView(ListView):
    model = Arch
    queryset = Arch.objects.all()
    allow_empty = True
    template_name = "arch_list.html"
    context_object_name = "arch_list"


class SigKeyListView(ListView):
    model = SigKey
    queryset = SigKey.objects.all()
    allow_empty = True
    template_name = "sigkey_list.html"
    context_object_name = "sigkey_list"


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
    queryset = Label.objects.all()
    filter_class = LabelFilter

    def create(self, request, *args, **kwargs):
        """
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
        return super(LabelViewSet, self).create(request, *args, **kwargs)

    def list(self, request, *args, **kwargs):
        """
        ### LIST

        __Method__:
        GET

        __URL__: $LINK:label-list$

        __QUERY Params__:

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
        return super(LabelViewSet, self).list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        """
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
        return super(LabelViewSet, self).retrieve(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        """
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
        return super(LabelViewSet, self).update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """
        ### DELETE

        __Method__: `DELETE`

        __URL__: $LINK:label-detail:instance_pk$

        __Response__:

            STATUS: 204 NO CONTENT

        __Example__:

            curl -X DELETE -H "Content-Type: application/json" $URL:label-detail:1$
        """
        return super(LabelViewSet, self).destroy(request, *args, **kwargs)


class ArchViewSet(pdc_viewsets.ChangeSetCreateModelMixin,
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
    queryset = Arch.objects.all()
    lookup_field = 'name'

    def list(self, request, *args, **kwargs):
        """
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
        return super(ArchViewSet, self).list(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        """
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
        return super(ArchViewSet, self).create(request, *args, **kwargs)


class SigKeyViewSet(pdc_viewsets.StrictQueryParamMixin,
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
    queryset = SigKey.objects.all()
    filter_class = SigKeyFilter
    lookup_field = 'key_id'

    def list(self, request, *args, **kwargs):
        """
        ### LIST

        __Method__:
        GET

        __URL__: $LINK:sigkey-list$

        __QUERY Params__:

        %(FILTERS)s

        __Response__: a paged list of following objects

        %(SERIALIZER)s
        """
        return super(SigKeyViewSet, self).list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        """
        ### RETRIEVE

        __Method__:
        GET

        __URL__: $LINK:sigkey-detail:key_id$

        __Response__:

        %(SERIALIZER)s
        """
        return super(SigKeyViewSet, self).retrieve(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        """
        ### UPDATE

        __Method__: `PUT`, `PATCH`

        PATCH: for partial update

        __URL__: $LINK:sigkey-detail:key_id$

        __Data__:

        %(WRITABLE_SERIALIZER)s

        __Response__:

        %(SERIALIZER)s
        """

        # NOTE: key_id is a read only field and do not allow to update to
        # another value, so PATCH is better to take this behavior as the same
        # as the XMLRPC API.
        if not kwargs.get('partial', False):
            return self.http_method_not_allowed(request, *args, **kwargs)
        else:
            return super(SigKeyViewSet, self).update(request, *args, **kwargs)

    def bulk_update(self, *args, **kwargs):
        """
        ### BULK UPDATE

        Only partial updating is allowed.

        __Method__: PATCH

        The data should include a mapping from `key_id` to a change
        description. Possible changes are below:

            {"name": "new_name"}
            or
            {"description": "new_description"}
            or
            {"name": "new_name", "description": "new_description"}

        __URL__: $LINK:sigkey-list$

        __Response__:

        The response will again include a mapping from `key_id` to objects
        representing the keys. Each key will be shown as follows:

        %(SERIALIZER)s
        """
        return bulk_operations.bulk_update_impl(self, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        """
        ### CREATE

        __Method__:
        POST

        __URL__: $LINK:sigkey-list$

        __Data__:

        %(SERIALIZER)s

        __Response__:

        %(SERIALIZER)s
        """
        return super(SigKeyViewSet, self).create(request, *args, **kwargs)


def home(request):
    return render(request, "home/index.html")
