#
# Copyright (c) 2017 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
from pdc.apps.auth.permissions import APIPermission
from pdc.apps.common import viewsets
from pdc.apps.common.constants import PUT_OPTIONAL_PARAM_WARNING
from pdc.apps.release.models import Release
from pdc.apps.componentbranch.models import SLA
from .models import ReleaseSchedule
from .serializers import ReleaseScheduleSerializer
from .filters import ReleaseScheduleFilter


class ReleaseScheduleViewSet(viewsets.PDCModelViewSet):
    """
    #**Warning: This is an experimental API**#
    ##Overview##

    This page shows the usage of the **Release Schedule API**, please see the
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
    model = ReleaseSchedule
    queryset = model.objects.all().order_by('date')
    serializer_class = ReleaseScheduleSerializer
    filter_class = ReleaseScheduleFilter
    permission_classes = (APIPermission,)
    docstring_macros = PUT_OPTIONAL_PARAM_WARNING
    related_model_classes = (ReleaseSchedule, Release, SLA)

    def list(self, request, *args, **kwargs):
        """
        __Method__:
        GET

        __URL__: $LINK:releaseschedule-list$

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
                        "active": bool,
                        "date": date,
                        "id": int,
                        "release": string,
                        "release_url": string,
                        "sla": string,
                        "sla_url": string,
                    }
                    ...
            }
        """
        return super(ReleaseScheduleViewSet, self).list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        """
        __Method__:
        GET

        __URL__: $LINK:releaseschedule-detail:pk$

        __Response__:

            {
                "active": bool,
                "date": date,
                "id": int,
                "release": string,
                "release_url": string,
                "sla": string,
                "sla_url": string,
            }

        """

        return super(ReleaseScheduleViewSet, self).retrieve(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        """
        %(PUT_OPTIONAL_PARAM_WARNING)s

        __Method__:

        PUT:


        PATCH:


        __URL__: $LINK:releaseschedule-detail:pk$

        __Response__:

            {
                "active": bool,
                "date": date,
                "id": int,
                "release": string,
                "release_url": string,
                "sla": string,
                "sla_url": string,
            }
        """
        return super(ReleaseScheduleViewSet, self).update(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        """
        __Method__:
        POST

        __URL__: $LINK:releaseschedule-list$

        __Data__:

            {
                'release': string,  # required
                'sla':     string,  # required
                'date':    date,    # required
            }

        *type*: $LINK:releaseschedule-list$

        __Response__:

            {
                "active": bool,
                "date": date,
                "id": int,
                "release": string,
                "release_url": string,
                "sla": string,
                "sla_url": string,
            }

        """
        return super(ReleaseScheduleViewSet, self).create(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """
        __Method__:
        DELETE

        __URL__: $LINK:releaseschedule-detail:pk$

        __Response__:

            STATUS: 204 NO CONTENT

        __Example__:

            curl -X DELETE -H "Content-Type: application/json" $URL:releaseschedule-detail:1$
        """
        return super(ReleaseScheduleViewSet, self).destroy(request, *args, **kwargs)
