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

        __URL__:
        /labels/

        __Data__:

            {
                'name':             string,         # required
                'description':      string,         # required
            }
        __Response__:

            {
                "url": url,
                "name": string,
                "description": string
            }

        __Example__:

            curl -H "Content-Type: application/json"  -X POST -d '{"name": "label1", "description": "label1 description"}' %(HOST_NAME)s/%(API_PATH)s/labels/
            # output
            {"url": "%(HOST_NAME)s/%(API_PATH)s/labels/1/", "name": "label1", "description": "label1 description"}
        """
        return super(LabelViewSet, self).create(request, *args, **kwargs)

    def list(self, request, *args, **kwargs):
        """
        ### LIST

        __Method__:
        GET

        __URL__:
        /labels/

        __QUERY Params__:

            name    # optional

        __Response__:

            # paged lists
            {
                "count": 284,
                "next": "%(HOST_NAME)s/%(API_PATH)s/labels/?page=2",
                "previous": null,
                "results": [
                    {
                        "url": "%(HOST_NAME)s/%(API_PATH)s/labels/1/",
                        "name": "label1",
                        "description": "label1 description"
                    },
                    ...
            }

        __Example__:

            curl -H "Content-Type: application/json"  -X GET %(HOST_NAME)s/%(API_PATH)s/labels/
            # output
            {
                "count": 284,
                "next": "%(HOST_NAME)s/%(API_PATH)s/labels/?page=2",
                "previous": null,
                "results": [
                    {
                        "url": "%(HOST_NAME)s/%(API_PATH)s/labels/1/",
                        "name": "label1",
                        "description": "label1 description"
                    },
                    {
                        "url": "%(HOST_NAME)s/%(API_PATH)s/labels/2/",
                        "name": "label2",
                        "description": "label2 description"
                    },
                    ...
                ]
            }

        With query params:

            curl -H "Content-Type: application/json"  -G %(HOST_NAME)s/%(API_PATH)s/labels/ -d name=label1
            {
                "count": 1,
                "next": null,
                "previous": null,
                "results": [
                    {
                       "url": "%(HOST_NAME)s/%(API_PATH)s/labels/1/",
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

        __URL__:
        /labels/{instance_pk}

        __Response__:

            {
                "url": url,
                "name": string,
                "description": string
            }

        __Example__:

            curl -H "Content-Type: application/json" %(HOST_NAME)s/%(API_PATH)s/labels/1/
            # output
            {"url": "%(HOST_NAME)s/%(API_PATH)s/labels/1/", "name": "label1", "description": "label1 description"}
        """
        return super(LabelViewSet, self).retrieve(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        """
        ### UPDATE

        __Method__:

        PUT: for full fields update
            {'name': 'new_name', 'description': 'new_description'}

        PATCH: for partial update
            {'name': 'new_name'}
            or
            {'description': 'new_description'}
            or
            {'name': 'new_name', 'description': 'new_description'}

        __URL__:
        /labels/{instance_pk}

        __Response__:

            {
                "url": url,
                "name": string,
                "description": string
            }

        __Example__:

        PUT:

            curl -X PUT -d '{"name": "new_name", "description": "new_description"}' -H "Content-Type: application/json" %(HOST_NAME)s/%(API_PATH)s/labels/1/
            # output
            {"url": "%(HOST_NAME)s/%(API_PATH)s/labels/1/", "name": "new_name", "description": "new_description"}

        PATCH:

            curl -X PATCH -d '{"description": "new_description"}' -H "Content-Type: application/json" %(HOST_NAME)s/%(API_PATH)s/labels/1/
            # output
            {"url": "%(HOST_NAME)s/%(API_PATH)s/labels/1/", "name": "label1", "description": "new_description"}
        """
        return super(LabelViewSet, self).update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """
        ### DELETE

        __Method__:
        DELETE

        __URL__:
        /labels/{instance_pk}

        __Response__:

            STATUS: 204 NO CONTENT

        __Example__:

            curl -X DELETE -H "Content-Type: application/json" %(HOST_NAME)s/%(API_PATH)s/labels/1/
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

        __URL__:
        /arches/

        __Response__:

            # paged lists
            {
                "count": int,
                "next": url,
                "previous": url,
                "results": [
                    {
                        "name": string
                    },
                    ...
            }

        __Example__:

            curl -H "Content-Type: application/json"  -X GET %(HOST_NAME)s/%(API_PATH)s/arches/
            # output
            {
                "count": 47,
                "next": "%(HOST_NAME)s/%(API_PATH)s/arches/?page=2",
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

        __URL__:
        /arches/

        __Data__:

            {
                'name':             string,         # required
            }
        __Response__:

            {
                "name": string
            }

        __Example__:

            curl -H "Content-Type: application/json" -X POST -d '{"name": "arm"}' %(HOST_NAME)s/%(API_PATH)s/arches/
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

        __URL__:
        /sigkeys/

        __QUERY Params__:

            key_id
            name
            description(icontains match)

        __Response__:

            # paged lists
            {
                "count": int,
                "next": url,
                "previous": url,
                "results": [
                    {
                        "url": url,
                        "name": string,
                        "key_id": string,
                        "description": string
                    },
                    ...
            }
        """
        return super(SigKeyViewSet, self).list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        """
        ### RETRIEVE

        __Method__:
        GET

        __URL__:
        /sigkeys/{key_id}/

        __Response__:

            {
                "url": url,
                "key_id": string,
                "name": string,
                "description": string
            }
        """
        return super(SigKeyViewSet, self).retrieve(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        """
        ### UPDATE

        __Method__:

        PATCH: for partial update
            {'name': 'new_name'}
            or
            {'description': 'new_description'}
            or
            {'name': 'new_name', 'description': 'new_description'}

        __URL__:
        /sigkeys/{key_id}/

        __Response__:

            {
                "url": url,
                "name": string,
                "description": string
            }
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

        __URL__:
        /sigkeys/

        __Response__:

        The response will again include a mapping from `key_id` to objects
        representing the keys. Each key will be shown as follows:

            {
                "url": url,
                "name": string,
                "description": string
            }
        """
        return bulk_operations.bulk_update_impl(self, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        """
        ### CREATE

        __Method__:
        POST

        __URL__:
        /sigkeys/

        __Data__:

            {
                "key_id":           string(hexdigits,8),         # required
                "name":             string,                      # optional
                "description":      string,                      # optional
            }
        __Response__:

            {
                "url": url,
                "key_id": string,
                "name": string,
                "description": string
            }
        """
        return super(SigKeyViewSet, self).create(request, *args, **kwargs)


def home(request):
    return render(request, "home/index.html")
