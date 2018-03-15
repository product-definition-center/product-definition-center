#
# Copyright (c) 2018 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
from pdc.apps.common import viewsets
from pdc.apps.module.models import Module
from pdc.apps.unreleasedvariant.serializers import UnreleasedVariantSerializer
from pdc.apps.unreleasedvariant.filters import UnreleasedVariantFilter


class UnreleasedVariantViewSet(viewsets.PDCModelViewSet):
    """
    # This API is deprecated. Please use $LINK:modules-list$.#
    ##Overview##

    This page shows the usage of the **Module API**, please see the following for more details.
    """
    model = Module
    queryset = Module.objects.all().order_by('uid')
    filter_class = UnreleasedVariantFilter
    serializer_class = UnreleasedVariantSerializer
    lookup_field = 'uid'

    doc_list = """
        __Method__:
        GET

        __URL__: $LINK:unreleasedvariants-list$

        __Query Params__:

        %(FILTERS)s

        __Paged Response__:

        %(SERIALIZER)s
    """

    doc_retrieve = """
        __Method__:
        GET

        __URL__: $LINK:unreleasedvariants-detail:variant_uid$

        __Response__:

        %(SERIALIZER)s
    """

    doc_create = """
        __Method__:
        POST

        __URL__: $LINK:unreleasedvariants-list$

        __Data__:

        %(WRITABLE_SERIALIZER)s

        __Response__:

        %(SERIALIZER)s

        __Example__:

            curl -X POST -H "Content-Type: application/json" $URL:unreleasedvariants-list$ \\
                    -d '{ "variant_id": "core", "variant_uid": "Core", "variant_name": "Minimalistic Core", "variant_type": "module", "variant_version": "master", "variant_release": "20170101", "variant_context": "2f345c78", "koji_tag": "foobar", "active": false }'
    """

    doc_destroy = """
        __Method__:
        DELETE

        __URL__: $LINK:unreleasedvariants-detail:variant_uid$

        __Response__:

            STATUS: 204 NO CONTENT

        __Example__:

            curl -X DELETE -H "Content-Type: application/json" $URL:unreleasedvariants-detail:variant_uid$
    """

    doc_update = """
        __Method__:
        PUT/PATCH

        __URL__: $LINK:unreleasedvariants-detail:variant_uid$

        __Data__:

        %(WRITABLE_SERIALIZER)s

        __Response__:

        %(SERIALIZER)s

        __Example__:

            curl -X PATCH -d '{ "active": true}' -H "Content-Type: application/json" \\
                $URL:unreleasedvariants-detail:testmodule-master-20170301215520$
    """
