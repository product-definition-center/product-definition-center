#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
from rest_framework import mixins
from rest_framework import viewsets

from pdc.apps.common import viewsets as common_viewsets
from . import filters
from . import models
from . import serializers


class OSBSViewSet(common_viewsets.StrictQueryParamMixin,
                  common_viewsets.ChangeSetUpdateModelMixin,
                  mixins.ListModelMixin,
                  common_viewsets.MultiLookupFieldMixin,
                  mixins.RetrieveModelMixin,
                  viewsets.GenericViewSet):
    queryset = models.OSBSRecord.objects.filter(component__type__has_osbs=True)
    serializer_class = serializers.OSBSSerializer
    filter_class = filters.OSBSFilter
    lookup_fields = (('component__release__release_id', r'[^/]+'),
                     ('component__name', r'[^/]+'))

    def retrieve(self, request, **kwargs):
        """
        __Method__: `GET`

        __URL__: $LINK:osbs-detail:release_id}/{component_name$

        __Response__:

        %(SERIALIZER)s
        """
        return super(OSBSViewSet, self).retrieve(request, **kwargs)

    def list(self, request, **kwargs):
        """
        __Method__: `GET`

        __URL__: $LINK:osbs-list$

        __Query params__:

        %(FILTERS)s

        __Response__:

        %(SERIALIZER)s
        """
        return super(OSBSViewSet, self).list(request, **kwargs)

    def update(self, request, **kwargs):
        """
        __Method__: `PUT`

        __URL__: $LINK:osbs-detail:release_id}/{component_name$

        __Data__:

        %(WRITABLE_SERIALIZER)s

        __Response__:

        %(SERIALIZER)s
        """
        return super(OSBSViewSet, self).update(request, **kwargs)

    def partial_update(self, request, **kwargs):
        """
        __Method__: `PATCH`

        __URL__: $LINK:osbs-detail:release_id}/{component_name$

        __Data__:

        %(WRITABLE_SERIALIZER)s

        __Response__:

        %(SERIALIZER)s
        """
        return super(OSBSViewSet, self).partial_update(request, **kwargs)
