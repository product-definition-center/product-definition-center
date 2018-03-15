#
# Copyright (c) 2017 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#

from pdc.apps.common import viewsets
from pdc.apps.componentbranch.models import (
    ComponentBranch, SLA, SLAToComponentBranch)
from pdc.apps.componentbranch.serializers import (
    ComponentBranchSerializer, SLASerializer, SLAToComponentBranchSerializer)
from pdc.apps.componentbranch.filters import (
    ComponentBranchFilter, SLAFilter, SLAToComponentBranchFilter)
from pdc.settings import COMPONENT_BRANCH_NAME_BLACKLIST_REGEX


class ComponentBranchViewSet(viewsets.PDCModelViewSet):
    """
    #**Warning: This is an experimental API**#
    ##Overview##

    This page shows the usage of the **Component Branches API**, please see the
    following for more details.

    Please note that the following restrictions are applied to the branch name during creation: ``{regex_blacklist}``

    ##Test tools##

    You can use ``curl`` in terminal, with -X _method_ (GET|POST|PUT|DELETE),
    -d _data_ (a json string). or GUI plugins for
    browsers, such as ``RESTClient``, ``RESTConsole``.

    """
    model = ComponentBranch
    queryset = ComponentBranch.objects.order_by(
        'global_component__name', 'name', 'type__name')
    serializer_class = ComponentBranchSerializer
    filter_class = ComponentBranchFilter

    def __init__(self, *args, **kwargs):
        # Note the blacklist regex defined in the docstring
        self.__doc__ = self.__doc__.format(regex_blacklist=(
            COMPONENT_BRANCH_NAME_BLACKLIST_REGEX or 'none'))

        super(ComponentBranchViewSet, self).__init__(*args, **kwargs)

    doc_list = """
        __Method__:
        GET

        __URL__: $LINK:componentbranch-list$

        __Query Params__:

        %(FILTERS)s

        __Response__:

            {
                "count": int,
                "next": url,
                "previous": url,
                "results": [
                    {
                        "id": int,
                        "global_component": string,
                        "name": string,
                        "slas": list,
                        "type": string,
                        "active": boolean,
                        "critical_path": boolean
                    }
                    ...
                ]
            }
    """

    doc_retrieve = """
        __Method__:
        GET

        __URL__: $LINK:componentbranch-detail:id$

        __Response__:

            {
                "id": int,
                "global_component": string,
                "name": string,
                "slas": list,
                "type": string,
                "active": boolean,
                "critical_path": boolean
            }
    """

    doc_create = """
        __Method__: `POST`

        __URL__: $LINK:componentbranch-list$

        __Parameters__:

        * **name**: the name of the branch
        * **global_component**: the name of the global component this branch belongs to
        * **type**: the name of the branch's type (ReleaseComponentType)
        * **critical_path**: a boolean determining if the branch is "critical path". This defaults to false.

        __Data__:

            {
                "global_component": string,
                "name": string,
                "type": string,
                "critical_path": boolean
            }

        __Response__:

        %(SERIALIZER)s
    """

    doc_update = """
        __Method__:

        PUT/PATCH: for update

        __Parameters__:

        * **name**: the name of the branch. **This value is not modifiable**.
        * **global_component**: the name of the global component this branch belongs to
        * **type**: the name of the branch's type (ReleaseComponentType)
        * **critical_path**: a boolean determining if the branch is "critical path". This defaults to false.

        __Data__:

            {
                "global_component": string,
                "name": string,
                "type": string,
            }

        __URL__: $LINK:componentbranch-detail:id$

        __Response__:

            {
                "id": int,
                "global_component": string,
                "name": string,
                "slas": list,
                "type": string,
                "active": boolean,
                "critical_path": boolean
            }

        __Example__:

        PUT:

            curl -X PUT -H "Content-Type: application/json" $URL:componentbranch-detail:1$ \\
                    -d '{"name": "2.7", "global_component": "python", "type": "rpm"}'
            # Output
            {
                "id": 1,
                "global_component": "python",
                "name": "2.7",
                "slas": [],
                "type": "rpm",
                "active": true,
                "critical_path": false
            }

        PATCH:

            curl -X PATCH -H "Content-Type: application/json" $URL:componentbranch-detail:1$ -d '{"type": "container"}'
            # Output
            {
                "id": 1,
                "global_component": "python",
                "name": "2.7",
                "slas": [],
                "type": "rpm",
                "active": false,
                "critical_path": false
            }
    """

    doc_destroy = """
        __Method__:
        DELETE

        __URL__: $LINK:componentbranch-detail:id$

        __Response__:

            STATUS: 204 NO CONTENT

        __Example__:

            curl -X DELETE -H "Content-Type: application/json" $URL:componentbranch-detail:1$
    """


class SLAViewSet(viewsets.PDCModelViewSet):
    """
    #**Warning: This is an experimental API**#
    ##Overview##

    This page shows the usage of the **Component SLA Types API**, please see the
    following for more details.

    ##Test tools##

    You can use ``curl`` in terminal, with -X _method_ (GET|POST|PUT|DELETE),
    -d _data_ (a json string). or GUI plugins for
    browsers, such as ``RESTClient``, ``RESTConsole``.

    """
    model = SLA
    queryset = SLA.objects.order_by('name')
    serializer_class = SLASerializer
    filter_class = SLAFilter

    doc_list = """
        __Method__:
        GET

        __URL__: $LINK:sla-list$

        __Query Params__:

        %(FILTERS)s

        __Response__:

            {
                "count": int,
                "next": url,
                "previous": url,
                "results": [
                    {
                        "id": int,
                        "name": string,
                        "description": string
                    }
                    ...
                ]
            }
    """

    doc_retrieve = """
        __Method__:
        GET

        __URL__: $LINK:sla-detail:id$

        __Response__:

            {
                "id": int,
                "name": string,
                "description": string
            }
    """

    doc_create = """
        __Method__: `POST`

        __URL__: $LINK:sla-list$

        __Parameters__:

        * **name**: the name of the SLA
        * **description**: the optional description of the SLA

        __Data__:

            {
                "name": string,
                "description": string
            }

        __Response__:

        %(SERIALIZER)s
    """

    doc_update = """
        __Method__:

        PUT/PATCH: for update

        __Parameters__:

        * **name**: the name of the SLA. **This is not a modifiable value**.
        * **description**: the description of the SLA

        __Data__:

            {
                "name": string,
                "description": string
            }

        __URL__: $LINK:sla-detail:id$

        __Response__:

            {
                "id": int,
                "name": string,
                "description": string
            }

        __Example__:

        PUT:

            curl -X PUT -H "Content-Type: application/json" $URL:sla-detail:1$ \\
                    -d '{"name": "security_fixes", "description": "All upstream security fixes will be applied"}'
            # Output
            {
                "id": 1,
                "name": "security_fixes",
                "description": "All upstream security fixes will be applied"
            }

        PATCH:

            curl -X PATCH -H "Content-Type: application/json" $URL:sla-detail:1$ -d '{"description": "A new description"}'
            # Output
            {
                "id": 1,
                "name": "security_fixes",
                "description": "A new description"
            }
    """

    doc_destroy = """
        __Method__:
        DELETE

        __URL__: $LINK:sla-detail:id$

        __Response__:

            STATUS: 204 NO CONTENT

        __Example__:

            curl -X DELETE -H "Content-Type: application/json" $URL:sla-detail:1$
    """


class SLAToComponentBranchViewSet(viewsets.PDCModelViewSet):
    """
    #**Warning: This is an experimental API**#
    ##Overview##

    This page shows the usage of the **SLA To Component Branch API**, please see
    the following for more details.

    Please note that the following restrictions are applied to the branch name during creation: ``{regex_blacklist}``

    ##Test tools##

    You can use ``curl`` in terminal, with -X _method_ (GET|POST|PUT|DELETE),
    -d _data_ (a json string). or GUI plugins for
    browsers, such as ``RESTClient``, ``RESTConsole``.

    """
    model = SLAToComponentBranch
    queryset = SLAToComponentBranch.objects.all().order_by(
        'branch__global_component__name', 'branch__name')
    serializer_class = SLAToComponentBranchSerializer
    filter_class = SLAToComponentBranchFilter

    def __init__(self, *args, **kwargs):
        # Note the blacklist regex defined in the docstring
        self.__doc__ = self.__doc__.format(regex_blacklist=(
            COMPONENT_BRANCH_NAME_BLACKLIST_REGEX or 'none'))

        super(SLAToComponentBranchViewSet, self).__init__(*args, **kwargs)

    doc_list = """
        __Method__:
        GET

        __URL__: $LINK:slatocomponentbranch-list$

        __Query Params__:

        %(FILTERS)s

        __Response__:

            {
                "count": int,
                "next": url,
                "previous": url,
                "results": [
                    {
                        "id": int,
                        "sla": string,
                        "branch": {
                            "id": int,
                            "name": string,
                            "global_component": string,
                            "type": string,
                            "active": boolean,
                            "critical_path": boolean
                        },
                        "eol": date
                    },
                    ...
                ]
            }
    """

    doc_retrieve = """
        __Method__:
        GET

        __URL__: $LINK:slatocomponentbranch-detail:id$

        __Response__:

            {
                "id": int,
                "sla": string,
                "branch": {
                    "id": int,
                    "name": string,
                    "global_component": string,
                    "type": string,
                    "active": boolean,
                    "critical_path": boolean
                },
                "eol": date
            }
    """

    doc_create = """
        __Method__: `POST`

        __URL__: $LINK:slatocomponentbranch-list$

        __Parameters__:

        * **sla**: the name of the desired SLA
        * **eol**: an end of life date for the SLA in the format of "2020-01-01"
        * **branch**: a dictionary describing the branch to tie this SLA to. If the branch described does not exist, it will be created.
        * **branch.name**: the name of the branch
        * **branch.global_component**: the name of the global component this branch belongs to
        * **branch.type**: the name of the branch's type (ReleaseComponentType)
        * **branch.critical_path**: a boolean determining if the branch is "critical path". This defaults to false.

        __Data__:

            {
                "sla": string,
                "eol": date,
                "branch": {
                    "name": string,
                    "global_component": string,
                    "type": string,
                    "critical_path": boolean
                }
            }

        __Response__:

        %(SERIALIZER)s
    """

    doc_update = """
        __Method__:

        PUT/PATCH: for update

        __Parameters__:

        * **sla**: the name of the SLA
        * **eol**: an end of life date for the SLA in the format of "2020-01-01"
        * **branch**: a dictionary describing the branch the SLA is tied to. **The branch cannot be modified using this API**
        * **branch.name**: the name of the branch
        * **branch.global_component**: the name of the global component this branch belongs to
        * **branch.type**: the name of the branch's type (ReleaseComponentType)
        * **branch.critical_path**: an optional boolean determining if the branch is "critical path".

        __Data__:

            {
                "sla": string,
                "eol": date,
                "branch": {
                    "name": string,
                    "global_component": string,
                    "type": string,
                    "critical_path": boolean
                }
            }

        __URL__: $LINK:slatocomponentbranch-detail:id$

        __Response__:

            {
                "sla": string,
                "eol": date,
                "branch": {
                    "name": string,
                    "global_component": string,
                    "type": string,
                    "active": boolean,
                    "critical_path": boolean
                }
            }

        __Example__:

        PUT:

            curl -X PUT -H "Content-Type: application/json" $URL:slatocomponentbranch-detail:1$ \\
                    -d '{"sla": "security_fixes", "eol": "2020-01-01", "branch": {"name": "2.7", "global_component": "python", "type": "rpm"}}'
            # Output
            {
                "id": 1,
                "sla": "security_fixes",
                "branch": {
                    "id": 2,
                    "name": "2.7",
                    "global_component": "python",
                    "type": "rpm",
                    "active": true,
                    "critical_path": false
                },
                "eol": "2022-01-01"
            }

        PATCH:

            curl -X PATCH -H "Content-Type: application/json" $URL:slatocomponentbranch-detail:1$ -d '{"eol": "2020-01-31"}'
            # Output
            {
                "id": 1,
                "sla": "security_fixes",
                "branch": {
                    "id": 2,
                    "name": "2.7",
                    "global_component": "python",
                    "type": "rpm",
                    "active": true,
                    "critical_path": false
                },
                "eol": "2022-01-31"
            }
    """

    doc_destroy = """
        __Method__:
        DELETE

        __URL__: $LINK:slatocomponentbranch-detail:id$

        __Response__:

            STATUS: 204 NO CONTENT

        __Example__:

            curl -X DELETE -H "Content-Type: application/json" $URL:slatocomponentbranch-detail:1$
    """
