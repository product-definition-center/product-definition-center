#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
from rest_framework import mixins
from rest_framework import viewsets

from pdc.apps.common import viewsets as common_viewsets
from pdc.apps.auth.permissions import APIPermission
from . import filters
from . import models
from . import serializers


class OSBSViewSet(common_viewsets.NotificationMixin,
                  common_viewsets.StrictQueryParamMixin,
                  common_viewsets.ChangeSetUpdateModelMixin,
                  mixins.ListModelMixin,
                  common_viewsets.MultiLookupFieldMixin,
                  mixins.RetrieveModelMixin,
                  viewsets.GenericViewSet):
    """
    ## Metadata for OpenShift Build Service

    This viewset provides a list of all components relevant to OSBS. This
    connection is realized through the `has_osbs` flag on [release component
    types]($URL:releasecomponenttype-list$). The components appear in this API
    automatically when they are assigned the proper type. Records here can only
    be changed, they can't be created or deleted.

    Currently there is just one flag tracked here:

     * `autorebuild`: This flag indicates whether the component should be
       automatically rebuilt when its dependencies change. If the value in PDC
       is `null`, it indicates that the client should use its default value.
    """

    queryset = models.OSBSRecord.objects.filter(component__type__has_osbs=True).order_by('component__id')
    serializer_class = serializers.OSBSSerializer
    filter_class = filters.OSBSFilter
    permission_classes = (APIPermission,)
    lookup_fields = (('component__release__release_id', r'[^/]+'),
                     ('component__name', r'[^/]+'))

    doc_retrieve = """
        __Method__: `GET`

        __URL__: $LINK:osbs-detail:release_id}/{component_name$

        __Response__:

        %(SERIALIZER)s
    """

    doc_list = """
        __Method__: `GET`

        __URL__: $LINK:osbs-list$

        __Query params__:

        %(FILTERS)s

        __Response__:

        %(SERIALIZER)s
    """

    doc_update = """
        __Method__: `PUT`

        __URL__: $LINK:osbs-detail:release_id}/{component_name$

        __Data__:

        %(WRITABLE_SERIALIZER)s

        __Response__:

        %(SERIALIZER)s
    """

    doc_partial_update = """
        __Method__: `PATCH`

        __URL__: $LINK:osbs-detail:release_id}/{component_name$

        __Data__:

        %(WRITABLE_SERIALIZER)s

        __Response__:

        %(SERIALIZER)s
    """
