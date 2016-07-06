#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#

from pdc.apps.common import viewsets
from .models import (Tree, UnreleasedVariant,)
from .serializers import (TreeSerializer, UnreleasedVariantSerializer)
from .filters import (TreeFilter, UnreleasedVariantFilter)


class TreeViewSet(viewsets.PDCModelViewSet):
    """
    ##Overview##

    This page shows the usage of the **Tree API**, please see the
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
    model = Tree
    queryset = Tree.objects.all().order_by('tree_id')
    serializer_class = TreeSerializer
    filter_class = TreeFilter

    def list(self, request, *args, **kwargs):
        """
        __Method__:
        GET

        __URL__: $LINK:tree-list$

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
                        "tree_id": string,
                        "tree_date": date,
                        "variant": string
                        "arch": string,
                        "deleted": bool,
                        "content": json_data,
                        "content_format": [string, ...],
                        'url':                    string,
                    },
                    ...
            }
        """
        return super(TreeViewSet, self).list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        """
        __Method__:
        GET

        __URL__: $LINK:tree-detail:instance_pk$

        __Response__:

            {
                "tree_id": string,
                "tree_date": date,
                "variant": string
                "arch": string,
                "content": json_data,
                "content_format": [string, ...],
                "url": string
                "deleted": bool,
                "dt_imported": date
            }
        """
        return super(TreeViewSet, self).retrieve(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        """
        __Method__:
        POST

        __URL__: $LINK:tree-list$

        __Data__:

            {
                'tree_id':                string,         # required
                'tree_date':              string,         # required
                'variant':                string,         # required
                'arch':                   string,         # required
                'content':                json_data,      # required
                'content_format':       [string, ],     # required
                'url':                    string,         # required
                'deleted':                bool            # optional
            }

        __Response__:

            {
                "tree_id": string,
                "tree_date": date,
                "variant": string,
                "arch": string,
                "content": json_data,
                "content_format": [string, ],
                "deleted": bool
                "dt_imported": date
            }

        __Example__:

            curl -X POST -H "Content-Type: application/json" $URL:tree-list$ \\
                    -d '{ "tree_id": "core-x86_64-20160610", "tree_date": "20160526", "variant": "Core", "arch": "x86_64",}'
            # output
            {
                "tree_id": "core-x86_64-20160610",
                "tree_date": "20160526",
                "variant": "Core"
                "arch": "x86_64",
                'content': {'rpms' : [], 'images': [], ...}
                'content_format' : ['rpms, 'images', ...]
                "deleted": False,
                "dt_imported": 20160526,
            }
        """
        #print request.data
        return super(TreeViewSet, self).create(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """
        __Method__:
        DELETE

        __URL__: $LINK:tree-detail:instance_pk$

        __Response__:

            STATUS: 204 NO CONTENT

        __Example__:

            curl -X DELETE -H "Content-Type: application/json" $URL:tree-detail:4181$
        """
        return super(TreeViewSet, self).destroy(request, *args, **kwargs)

class UnreleasedVariantViewSet(viewsets.PDCModelViewSet):
    """
    ##Overview##

    This page shows the usage of the **Tree API**, please see the
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

        __URL__: $LINK:unreleasedvariant-detail:instance_pk$

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
                        "variant_version": string,# variant-version
            }

        __Response__:

            {
                        "variant_id": string,   # required
                        "variant_uid": string,  # required
                        "variant_name": string, # required
                        "variant_type": string, # required
            }

        __Example__:

            curl -X POST -H "Content-Type: application/json" $URL:tree-list$ \\
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

        __URL__: $LINK:unreleasedvariant-detail:instance_pk$

        __Response__:

            STATUS: 204 NO CONTENT

        __Example__:

            curl -X DELETE -H "Content-Type: application/json" $URL:tree-detail:4181$
        """
        return super(UnreleasedVariantViewSet, self).destroy(request, **kwargs)
