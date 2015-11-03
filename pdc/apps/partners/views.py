# -*- coding: utf-8 -*-
#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
from rest_framework import viewsets, mixins

from pdc.apps.common.viewsets import (StrictQueryParamMixin,
                                      ChangeSetCreateModelMixin,
                                      ChangeSetDestroyModelMixin,
                                      MultiLookupFieldMixin,
                                      PDCModelViewSet)

from . import filters
from . import models
from . import serializers


class PartnerTypeViewSet(StrictQueryParamMixin,
                         mixins.ListModelMixin,
                         viewsets.GenericViewSet):
    queryset = models.PartnerType.objects.all().order_by('id')
    serializer_class = serializers.PartnerTypeSerializer

    def list(self, request, *args, **kwargs):
        """
        __Method__: `GET`

        __URL__: $LINK:partnertype-list$

        __Response__: a paged list of following objects

        %(SERIALIZER)s
        """
        return super(PartnerTypeViewSet, self).list(request, *args, **kwargs)


class PartnerViewSet(PDCModelViewSet):
    queryset = models.Partner.objects.all().order_by('id')
    lookup_field = 'short'
    serializer_class = serializers.PartnerSerializer
    filter_class = filters.PartnerFilterSet

    def create(self, *args, **kwargs):
        """
        __Method__: `POST`

        __URL__: $LINK:partner-list$

        __Data__:

        %(WRITABLE_SERIALIZER)s

        See list of [available partner types]($URL:partnertype-list$).

        __Response__:

        %(SERIALIZER)s
        """
        return super(PartnerViewSet, self).create(*args, **kwargs)

    def retrieve(self, *args, **kwargs):
        """
        __Method__: `GET`

        __URL__: $LINK:partner-detail:short$

        __Response__:

        %(SERIALIZER)s
        """
        return super(PartnerViewSet, self).retrieve(*args, **kwargs)

    def list(self, *args, **kwargs):
        """
        __Method__: `GET`

        __URL__: $LINK:partner-list$

        __Query params__:

        %(FILTERS)s

        __Response__: a paged list of following objects

        %(SERIALIZER)s
        """
        return super(PartnerViewSet, self).list(*args, **kwargs)

    def destroy(self, *args, **kwargs):
        """
        __Method__: `DELETE`

        __URL__: $LINK:partner-detail:short$
        """
        return super(PartnerViewSet, self).destroy(*args, **kwargs)

    def update(self, *args, **kwargs):
        """
        __Method__: `PUT`, `PATCH`

        __URL__: $LINK:partner-detail:short$

        __Data__:

        %(WRITABLE_SERIALIZER)s

        __Response__:

        %(SERIALIZER)s
        """
        return super(PartnerViewSet, self).update(*args, **kwargs)


class PartnerMappingViewSet(StrictQueryParamMixin,
                            MultiLookupFieldMixin,
                            mixins.ListModelMixin,
                            ChangeSetCreateModelMixin,
                            ChangeSetDestroyModelMixin,
                            viewsets.GenericViewSet):
    queryset = models.PartnerMapping.objects.all().select_related(
        'partner',
        'variant_arch__arch',
        'variant_arch__variant__release'
    ).order_by('id')
    serializer_class = serializers.PartnerMappingSerializer
    lookup_fields = (
        ('partner__short', r'[^/]+'),
        ('variant_arch__variant__release__release_id', r'[^/]+'),
        ('variant_arch__variant__variant_uid', r'[^/]+'),
        ('variant_arch__arch__name', r'[^/]+'),
    )
    filter_class = filters.PartnerMappingFilterSet

    def list(self, *args, **kwargs):
        """Get mappings between partner and releases.

        __Method__: `GET`

        __Query params__:

        %(FILTERS)s

        __Response__: a paged list of following objects

        %(SERIALIZER)s
        """
        return super(PartnerMappingViewSet, self).list(*args, **kwargs)

    def create(self, *args, **kwargs):
        """Create mapping between partner and specified Variant.Arch on a given release.

        __Method__: `POST`

        __Data__:

        %(WRITABLE_SERIALIZER)s

        __Response__:

        %(SERIALIZER)s
        """
        return super(PartnerMappingViewSet, self).create(*args, **kwargs)

    def destroy(self, *args, **kwargs):
        """Delete mapping between partner and specified Variant.Arch on a given release.

        __Method__: `DELETE`

        __URL__: $LINK:partnermapping-detail:partner}/{release_id}/{variant}/{arch$
        """
        return super(PartnerMappingViewSet, self).destroy(*args, **kwargs)
