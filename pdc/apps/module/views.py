#
# Copyright (c) 2018 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#

from pdc.apps.common import viewsets
from pdc.apps.module.models import Module
from pdc.apps.module.serializers import ModuleSerializer
from pdc.apps.module.filters import ModuleFilter


class ModuleViewSet(viewsets.PDCModelViewSet):
    """
    ##Overview##

    This page shows the usage of the **Module API**, please see the following for more details.
    """
    model = Module
    # Only show the items in the database of type 'module'. The type in the "unreleasedvariants"
    # API is a freeform text field but in this API, the type field is not exposed and just defaults
    # to 'module' in the database for backwards-compatibility.
    queryset = Module.objects.filter(type='module').order_by('uid')
    filter_class = ModuleFilter
    serializer_class = ModuleSerializer
    lookup_field = 'uid'

    doc_list = """
        __Method__:
        GET

        __URL__: $LINK:modules-list$

        __Query Params__:

        %(FILTERS)s

        __Paged Response__:

        %(SERIALIZER)s
    """

    doc_retrieve = """
        __Method__:
        GET

        __URL__: $LINK:modules-detail:uid$

        __Response__:

        %(SERIALIZER)s
    """

    doc_create = """
        __Method__:
        POST

        __URL__: $LINK:modules-list$

        __Data__:

        %(WRITABLE_SERIALIZER)s

        __Response__:

        %(SERIALIZER)s

        __Example__:

            curl -X POST -H "Content-Type: application/json" $URL:modules-list$ \\
                -d '{ "name": "testmodule", "stream": "f28", "version": "20180123171544", "context": "2f345c78", "koji_tag": "module-ce2adf69caf0e1b5", "modulemd": "data here" }'
    """

    doc_destroy = """
        __Method__:
        DELETE

        __URL__: $LINK:modules-detail:uid$

        __Response__:

            STATUS: 204 NO CONTENT

        __Example__:

            curl -X DELETE -H "Content-Type: application/json" $URL:modules-detail:uid_here$
    """

    doc_update = """
        __Method__:
        PUT/PATCH

        __URL__: $LINK:modules-detail:uid$

        __Data__:

        %(WRITABLE_SERIALIZER)s

        __Response__:

        %(SERIALIZER)s

        __Example__:

            curl -X PATCH -d '{ "active": true }' -H "Content-Type: application/json" \\
                $URL:modules-detail:uid_here$
    """
