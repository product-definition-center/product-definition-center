#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#

from pdc.apps.common import viewsets
from .models import UnreleasedVariant
from .serializers import UnreleasedVariantSerializer
from .filters import UnreleasedVariantFilter


class UnreleasedVariantViewSet(viewsets.PDCModelViewSet):
    """
    ##Overview##

    This page shows the usage of the **Module API**, please see the
    following for more details.

    ##Test tools##

    You can use ``curl`` in terminal, with -X _method_ (GET|POST|PUT|DELETE),
    -d _data_ (a json string). or GUI plugins for
    browsers, such as ``RESTClient``, ``RESTConsole``.

    ## Customize Output ##

    There are two query params that you can use to customize your output.

    `fields`:          string, can be set multiple times, to demand what fields you want to include;

    `exclude_fields`:  string, can be set multiple times, to demand what fields you do NOT want.

    __NOTE__: If both given, `exclude_fields` *rules* `fields`.

    """
    model = UnreleasedVariant
    queryset = UnreleasedVariant.objects.all().order_by('variant_uid')
    serializer_class = UnreleasedVariantSerializer
    filter_class = UnreleasedVariantFilter
    lookup_field = 'variant_uid'
    lookup_regex = '[^/]+'

    def list(self, request, *args, **kwargs):
        """
        __Method__:
        GET

        __URL__: $LINK:unreleasedvariant-list$

        __Query Params__:

        %(FILTERS)s

        __Response__:

            # paged lists
            {
                "count": int,
                "next": url,
                "previous": url,
                "results": [
                    {
                        "variant_id": string,
                        "variant_uid": string,
                        "variant_name": string,
                        "variant_type": string,
                        "variant_version": string,
                    },
                    ...
            }
        """
        return super(UnreleasedVariantViewSet, self).list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        """
        __Method__:
        GET

        __URL__: $LINK:unreleasedvariant-detail:variant_id$

        __Response__:

            {
                "variant_id": string,
                "variant_uid": string,
                "variant_name": string,
                "variant_type": string,
                "variant_version": string,
            }
        """
        return super(UnreleasedVariantViewSet, self).retrieve(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        """
        __Method__:
        POST

        __URL__: $LINK:unreleasedvariant-list$

        __Data__:

            {
                        "variant_id": string,     # required
                        "variant_uid": string,    # required
                        "variant_name": string,   # required
                        "variant_type": string,   # required
                        "variant_version": string,# version of this particular variant
                        "variant_release": string,# release of this particular variant
            }

        __Response__:

            {
                        "variant_id": string,   # required
                        "variant_uid": string,  # required
                        "variant_name": string, # required
                        "variant_type": string, # required
            }

        __Example__:

            curl -X POST -H "Content-Type: application/json" $URL:unreleasedvariant-list$ \\
                    -d '{ "variant_id": "core", "variant_uid": "Core", "variant_name": "Minimalistic Core", "variant_type": "module", }'
            # output
            {
                "variant_id": "core",   # required
                "variant_uid": "Core",  # required
                "variant_name": "Minimalistic Core", # required
                "variant_type": "module", # required
            }
        """
        return super(UnreleasedVariantViewSet, self).create(request, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """
        __Method__:
        DELETE

        __URL__: $LINK:unreleasedvariant-detail:variant_id$

        __Response__:

            STATUS: 204 NO CONTENT

        __Example__:

            curl -X DELETE -H "Content-Type: application/json" $URL:unreleasedvariant-detail:4181$
        """
        return super(UnreleasedVariantViewSet, self).destroy(request, **kwargs)
