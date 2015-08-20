#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
import json
import types

from django.contrib.contenttypes.models import ContentType
from django.shortcuts import get_object_or_404

from mptt.exceptions import InvalidMove

from rest_framework import status, mixins
from rest_framework import viewsets as drf_viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from pdc.apps.common import viewsets
from pdc.apps.common.models import Label
from pdc.apps.contact.models import RoleContact, ContactRole
from pdc.apps.common.serializers import LabelSerializer, StrictSerializerMixin
from pdc.apps.common.filters import LabelFilter
from .models import (GlobalComponent,
                     ReleaseComponent,
                     BugzillaComponent,
                     ReleaseComponentGroup,
                     GroupType,
                     ReleaseComponentRelationship,
                     ReleaseComponentType,
                     ReleaseComponentRelationshipType)
from .serializers import (GlobalComponentSerializer,
                          ReleaseComponentSerializer,
                          HackedContactSerializer,
                          BugzillaComponentSerializer,
                          GroupSerializer,
                          GroupTypeSerializer,
                          ReleaseComponentRelationshipSerializer,
                          ReleaseComponentTypeSerializer,
                          RCRelationshipTypeSerializer)
from .filters import (ComponentFilter,
                      ReleaseComponentFilter,
                      RoleContactFilter,
                      BugzillaComponentFilter,
                      GroupFilter,
                      GroupTypeFilter,
                      ReleaseComponentRelationshipFilter)
from . import signals


class HackedComponentContactMixin(object):

    def perform_create(self, serializer):
        # NOTE(xchu): The Creation of ComponentContact is a UPDATE to
        #             Component instance, the changes about contact have
        #             been recorded by `serializer.to_internal_value`, so we
        #             need to record the change about Component itself instead of
        #             the creation of serializer's object as defined in the
        #             `ChangeSetCreateModelMixin`.
        pk = self.kwargs.get("instance_pk", None)
        component = get_object_or_404(self.model, id=pk)
        old_value = json.dumps(component.export())

        serializer.save()

        request = self.get_serializer_context().get('request', None)
        if request and request.changeset:
            request.changeset.add(self.model.__name__.lower(), component.pk,
                                  old_value, json.dumps(component.export()))


class GlobalComponentViewSet(viewsets.PDCModelViewSet):
    """
    ##Overview##

    This page shows the usage of the **Global Component API**, please see the
    following for more details.

    ##Test tools##

    You can use ``curl`` in terminal, with -X _method_ (GET|POST|PUT|DELETE),
    -d _data_ (a json string). or GUI plugins for
    browsers, such as ``RESTClient``, ``RESTConsole``.

    ## Customize Output ##

    There are two `QUERY_PARAMS` that you can use to customize your output.

    `fields`:          string, can be set multiple times, to demand what fields you want to include;

    `exclude_fields`:  string, can be set multiple times, to demand what fields you do NOT want.

    __NOTE__: If both given, `exclude_fields` *rules* `fields`.

    """
    model = GlobalComponent
    queryset = GlobalComponent.objects.all()
    serializer_class = GlobalComponentSerializer
    filter_class = ComponentFilter

    def list(self, request, *args, **kwargs):
        """
        __Method__:
        GET

        __URL__: $LINK:globalcomponent-list$

        __QUERY Params__:

        %(FILTERS)s

        The `contact_role` filter must be used together with `email`.

        __Response__:

            # paged lists
            {
                "count": int,
                "next": url,
                "previous": url,
                "results": [
                    {
                        "id": int,
                        "name": string,
                        "dist_git_path": <string|null>,
                        "dist_git_web_url": string,
                        "contacts": [
                            {
                                "url": string,
                                "contact_role": string,
                                "contact": {
                                    "mail_name": string,
                                    "email": string
                                }
                            },
                            ......
                        ],
                        "labels": [
                            string, ......
                        ],
                        "upstream": null | {
                                        "homepage": string,
                                        "scm_type": string,
                                        "scm_url": string
                                    }
                    },
                    ...
            }
        """
        return super(GlobalComponentViewSet, self).list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        """
        __Method__:
        GET

        __URL__: $LINK:globalcomponent-detail:instance_pk$

        __Response__:

            {
                "id": int,
                "name": string,
                "dist_git_path": <string|null>,
                "dist_git_web_url": string,
                "contacts": [
                    {
                        "url": string,
                        "contact_role": string,
                        "contact": {
                            "mail_name": string,
                            "email": string
                        }
                    },
                    ......
                ],
                "labels": [
                    string, ......
                ],
                "upstream": null | {
                            "homepage": string,
                            "scm_type": string,
                            "scm_url": string
                        }
            }
        """
        return super(GlobalComponentViewSet, self).retrieve(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        """
        __Method__:
        POST

        __URL__: $LINK:globalcomponent-list$

        __Data__:

            {
                'name':                string,         # required
                'dist_git_path':       string,         # optional
                'upstream':            dict,           # optional
            }
        __Response__:

            {
                "id": int,
                "name": string,
                "dist_git_path": string,
                "dist_git_web_url": string,
                "contacts": array,
                "labels": array,
                "upstream": dict
            }

        __Example__:

            curl -X POST -H "Content-Type: application/json" $URL:globalcomponent-list$ \\
                    -d '{ "name": "Demo", "dist_git_path": "rpm/Demo"}'
            # output
            {
                "id": 4181,
                "name": "Demo",
                "dist_git_path": "rpm/Demo",
                "dist_git_web_url": "http://pkgs.example.com/cgit/rpms/rpm/Demo"
                "contacts": [],
                "labels": [],
                "upstream": null | {
                                "homepage": string,
                                "scm_type": string,
                                "scm_url": string
                            }
            }
        """
        return super(GlobalComponentViewSet, self).create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        """
        __Method__:

        PUT: for full fields update
            {'name': 'new_name', 'dist_git_path': 'new_dist_git_path'}

        PATCH: for partial update
            {'name': 'new_name'}
            or
            {'dist_git_path': 'new_dist_git_path'}
            or
            {'name': 'new_name', 'dist_git_path': 'new_dist_git_path'}

        __URL__: $LINK:globalcomponent-detail:instance_pk$

        __Response__:

            {
                "id": int,
                "name": string,
                "dist_git_path": string,
                "dist_git_web_url": string,
                "contacts": array,
                "labels": array,
                "upstream": null | {
                                "homepage": string,
                                "scm_type": string,
                                "scm_url": string
                            }
            }

        __Example__:

        PUT:

            curl -X PUT -H "Content-Type: application/json" $URL:globalcomponent-detail:4181$ \\
                    -d '{"name": "Demo1", "dist_git_path": "rpm/Demo1"}'
            # output
            {
                "id": 4181,
                "name": "Demo",
                "dist_git_path": "rpm/Demo1",
                "dist_git_web_url": "http://pkgs.example.com/cgit/rpms/rpm/Demo1"
                "contacts": [],
                "labels": [],
                "upstream": null
            }

        PATCH:

            curl -X PATCH -H "Content-Type: application/json" $URL:globalcomponent-detail:4181$ -d '{"dist_git_path": "rpm/Demo1"}'
            # output
            {
                "id": 4181,
                "name": "Demo",
                "dist_git_path": "rpm/Demo1",
                "dist_git_web_url": "http://pkgs.example.com/cgit/rpms/rpm/Demo1"
                "contacts": [],
                "labels": [],
                "upstream": null
            }
        """
        return super(GlobalComponentViewSet, self).update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """
        __Method__:
        DELETE

        __URL__: $LINK:globalcomponent-detail:instance_pk$

        __Response__:

            STATUS: 204 NO CONTENT

        __Example__:

            curl -X DELETE -H "Content-Type: application/json" $URL:globalcomponent-detail:4181$
        """
        return super(GlobalComponentViewSet, self).destroy(request, *args, **kwargs)


class GlobalComponentContactViewSet(HackedComponentContactMixin,
                                    viewsets.PDCModelViewSet):
    """
    ##Overview##

    This page shows the usage of the **Global Component Contact API**, please
    see the following for more details.

    ##Test tools##

    You can use ``curl`` in terminal, with -X _method_ (GET|POST|PUT|DELETE),
    -d _data_ (a json string). or GUI plugins for
    browsers, such as ``RESTClient``, ``RESTConsole``.
    """

    model = GlobalComponent
    queryset = GlobalComponent.objects.all()
    serializer_class = HackedContactSerializer
    filter_class = RoleContactFilter

    def get_queryset(self):
        gc_id = self.kwargs.get('instance_pk')
        gc = get_object_or_404(GlobalComponent, id=gc_id)
        return gc.contacts.all()

    def list(self, request, *args, **kwargs):
        """
        __Method__:
        GET

        __URL__: $LINK:globalcomponentcontact-list:gc_instance_pk$

        __QUERY Params__:

        %(FILTERS)s

        The `contact_role` filter must be used together with `email`.

        __Response__:

            [
                {
                    "url": url,
                    "contact_role": string,
                    "contact": {
                        <"mail_name"|"username">: string,
                        "email": string
                    }
                },
                ......
            ]
        """
        # NOTE: we disable pagination because release component contact could
        #       not do the things like this, and we must keep the outputs same.
        #       it is a very very dirty hack for current version. we will use
        #       database view to refactor release component in next sprint.
        #       then we could enable pagination.
        self.object_list = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(self.object_list, many=True)
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        """
        __Method__:
        GET

        __URL__: $LINK:globalcomponentcontact-detail:gc_instance_pk:relation_pk$

        __Response__:

            {
                "url": url,
                "contact_role": string,
                "contact": {
                    <"mail_name"|"username">: string,
                    "email": string
                }
            }
        """
        return super(GlobalComponentContactViewSet, self).retrieve(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        return self.http_method_not_allowed(request, *args, **kwargs)

    def bulk_update(self, request, *args, **kwargs):
        return self.http_method_not_allowed(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """
        __Method__:
        DELETE

        __URL__: $LINK:globalcomponentcontact-detail:gc_instance_pk:relation_pk$

        __Response__:

            STATUS: 204 NO CONTENT

        __Example__:

            curl -X DELETE -H "Content-Type: application/json" $URL:globalcomponentcontact-detail:1:1$
        """
        pk = self.kwargs.get('pk')
        contact = get_object_or_404(RoleContact, id=pk)

        gc_id = self.kwargs.get('instance_pk')
        gc = get_object_or_404(GlobalComponent, id=gc_id)

        old_value = json.dumps(gc.export())
        if contact in gc.contacts.all():
            gc.contacts.remove(contact)
            request.changeset.add("globalcomponent", gc.pk, old_value, json.dumps(gc.export()))
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return Response(
                data={'detail': 'Can not be deleted since Contact[%s] is not in GlobalComponent[%s].' % (pk, gc_id)},
                status=status.HTTP_404_NOT_FOUND)

    def create(self, request, *args, **kwargs):
        """
        __Method__:
        POST

        __URL__: $LINK:globalcomponentcontact-list:gc_instance_pk$

        __Data__:

            {
                'contact_role':                       string,         # required
                'contact': {
                    <'username'|'mail_name'>:         string,         # required
                    'email:                           string,         # required
                }
            }
        __Response__:

            {
                "url": url,
                "contact_role": string,
                "contact": {
                    <"mail_name"|"username">: string,
                    "email": string
                }
            }
        """
        return super(GlobalComponentContactViewSet, self).create(request, *args, **kwargs)

    def get_serializer_context(self):
        super_class = super(GlobalComponentContactViewSet, self)
        ret = super_class.get_serializer_context()
        ret.update({
            'extra_kwargs': self.kwargs
        })
        return ret


class GlobalComponentLabelViewSet(viewsets.PDCModelViewSet):
    """
    ##Overview##

    This page shows the usage of the **Global Component Label API**, please
    see the following for more details.

    ##Test tools##

    You can use ``curl`` in terminal, with -X _method_ (GET|POST|PUT|DELETE),
    -d _data_ (a json string). or GUI plugins for
    browsers, such as ``RESTClient``, ``RESTConsole``.
    """
    model = Label
    queryset = Label.objects.all()
    serializer_class = LabelSerializer
    filter_class = LabelFilter

    def get_queryset(self):
        gc_id = self.kwargs.get('instance_pk')
        gc = get_object_or_404(GlobalComponent, id=gc_id)
        labels = gc.labels.all()
        return labels

    def list(self, request, *args, **kwargs):
        """
        Show the global component labels by pagination, 20 items per page by default, and you can pass some parameters
        to filter the result.

        ####__Request__####

            curl -X GET -H "Content-Type: application/json" $URL:globalcomponentlabel-list:1$

        Or search specified global component's label by label's name.

            curl -G -H "Content-Type: application/json" $URL:globalcomponentlabel-list:1$ -d name=label1

        Now it supports ``name`` to filter the result.

        ``name``: label's name

        ####__Response__####

        ``count``: total number of the global component labels

        ``next`` & ``previous``: pagination url for retrieving next or previous 20
        global component labels

        ``results``: global component labels list

            HTTP/1.0 200 OK
            Date: Mon, 20 Oct 2014 06:01:04 GMT
            Content-Type: application/json
            Allow: GET, POST, HEAD, OPTIONS
            {
                "count": 2,
                "next": null,
                "previous": null,
                "results": [
                    {
                        "url": "$URL:label-detail:1$",
                        "name": "label1",
                        "description": "label1 description"
                    },
                    {
                        "url": "$URL:label-detail:2$",
                        "name": "label1",
                        "description": "label1 description"
                    }

                ]
            }
        """
        return super(GlobalComponentLabelViewSet, self).list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        """
        Show the specified global component label instance.

        ####__Request__####

            curl -X GET -H "Content-Type: application/json" $URL:globalcomponentlabel-detail:1:1$

        ####__Response__####

            HTTP/1.0 200 OK
            Date: Mon, 20 Oct 2014 06:01:04 GMT
            Content-Type: application/json
            Allow: GET, POST, HEAD, OPTIONS

            {
                "url": "$URL:label-detail:1$",
                "name": "label1",
                "description": "label1 description"
            }
        """
        return super(GlobalComponentLabelViewSet, self).retrieve(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        self.http_method_not_allowed(request, *args, **kwargs)

    def bulk_update(self, request, *args, **kwargs):
        self.http_method_not_allowed(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """
        Delete a label from a specified global component, return an empty response if success.

        ####__Request__####

            curl -X DELETE -H "Content-Type: application/json" $URL:globalcomponentlabel-detail:1:1$

        ####__Response__####

            HTTP 204 NO CONTENT
            Date: Mon, 20 Oct 2014 06:21:21 GMT
            Content-Length: 0
            Allow: GET, PUT, PATCH, DELETE, HEAD, OPTIONS

        """
        pk = self.kwargs.get('pk')
        label = get_object_or_404(Label, id=pk)

        gc_id = self.kwargs.get('instance_pk')
        gc = get_object_or_404(GlobalComponent, id=gc_id)

        old_value = json.dumps(gc.export())
        if label in gc.labels.all():
            gc.labels.remove(label)
            request.changeset.add("globalcomponent", gc.pk, old_value, json.dumps(gc.export()))
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return Response(
                data={'detail': 'Can not be deleted since Label[%s] is not in GlobalComponent[%s].' % (pk, gc_id)},
                status=status.HTTP_404_NOT_FOUND)

    def create(self, request, *args, **kwargs):
        """
        Add a label instance to specified global component.

        **Note**:  label must exist before being assigned to a global_component.

        ####__Request__####

        ``name``: label's name, **REQUIRED**

        ``description``: label's description, **OPTIONAL**

            curl -X POST -H "Content-Type: application/json" $URL:globalcomponentlabel-list:1$ -d '{"name": "label1"}'

        ####__Response__####

            HTTP 201 CREATED
            Date: Mon, 20 Oct 2014 06:01:04 GMT
            Content-Type: application/json
            Allow: GET, POST, HEAD, OPTIONS
        """
        extra_keys = set(request.data.keys()) - self.serializer_class().get_allowed_keys()
        StrictSerializerMixin.maybe_raise_error(extra_keys)

        label_name = request.data.get('name')
        if not label_name:
            return Response(data={'name': ['This field is required.']},
                            status=status.HTTP_400_BAD_REQUEST)
        label = get_object_or_404(Label, name=label_name)

        gc_id = self.kwargs.get('instance_pk')
        gc = get_object_or_404(GlobalComponent, id=gc_id)

        old_value = json.dumps(gc.export())

        if label not in gc.labels.all():
            gc.labels.add(label)
            request.changeset.add("globalcomponent", gc.pk, old_value, json.dumps(gc.export()))
        return Response(
            status=status.HTTP_201_CREATED,
            data=LabelSerializer(instance=label, context={'request': request}).data
        )


class ReleaseComponentTypeViewSet(viewsets.StrictQueryParamMixin,
                                  mixins.ListModelMixin,
                                  drf_viewsets.GenericViewSet):
    """
    API endpoint that allows release_component_types to be viewed.
    """
    serializer_class = ReleaseComponentTypeSerializer
    queryset = ReleaseComponentType.objects.all()

    def list(self, request, *args, **kwargs):
        """
        __Method__: GET

        __URL__: $LINK:releasecomponenttype-list$

        __Response__:

            # paged list
            {
                "count": int,
                "next": url,
                "previous": url,
                "results": [
                    {
                        "name": string,
                    },
                    ...
                ]
            }
        """
        return super(ReleaseComponentTypeViewSet, self).list(request, *args, **kwargs)


class ReleaseComponentViewSet(viewsets.PDCModelViewSet):
    """
    ##Overview##

    This page shows the usage of the **Release Component API**, please see the
    following for more details.

    ##Test tools##

    You can use ``curl`` in terminal, with -X _method_ (GET|POST|PUT|DELETE),
    -d _data_ (a json string). or GUI plugins for
    browsers, such as ``RESTClient``, ``RESTConsole``.

    ## Customize Output ##

    There are two `QUERY_PARAMS` that you can use to customize your output.

    `fields`:          string, can be set multiple times, to demand what fields you want to include;

    `exclude_fields`:  string, can be set multiple times, to demand what fields you do NOT want.

    __NOTE__: If both given, `exclude_fields` *rules* `fields`.

    """
    model = ReleaseComponent
    queryset = model.objects.all()
    serializer_class = ReleaseComponentSerializer
    filter_class = ReleaseComponentFilter
    extra_query_params = ('include_inactive_release', )

    def get_queryset(self):
        qs = self.model.objects.all()
        query_params = self.request.query_params
        # include_inactive_release is not a field in model ReleaseComponent, so
        # it can not use django-filter to handle.
        if 'include_inactive_release' not in query_params:
            qs = qs.filter(release__active=True)
        return qs

    def list(self, request, *args, **kwargs):
        """
        __Method__:
        GET

        __URL__: $LINK:releasecomponent-list$

        __QUERY Params__:

        %(FILTERS)s

        Components for inactive releases are not shown by default. You can
        change this with `include_inactive_release` set to any non-empty value.

        The `contact_role` filter must be used together with `email`.

        __Response__:

            # paged lists
            {
                "count": int,
                "next": url,
                "previous": url,
                "results": [
                    {
                        "id": int,
                        "release": {
                            "release_id": string,
                            "active": bool
                        },
                        "global_component": string,
                        "bugzilla_component": {
                            "id": int,
                            "name": string,
                            "parent_component": string,
                            "subcomponents": [
                                ......
                            ]
                        },
                        "brew_package": string,
                        "name": string,
                        "dist_git_branch": <string|null>,
                        "dist_git_web_url": string,
                        "active": bool,
                        "contacts": [
                            ......
                        ],
                        "srpm": {
                            "name": string
                        } OR null,
                        "type": <string|null>
                    }
                    ...
            }
        """
        return super(ReleaseComponentViewSet, self).list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        """
        __Method__:
        GET

        __URL__: $LINK:releasecomponent-detail:instance_pk$

        __Response__:

            {
                "id": int,
                "release": {
                    "release_id": string,
                    "active": bool
                },
                "global_component": string,
                "bugzilla_component": {
                    "id": int,
                    "name": string,
                    "parent_component": string,
                    "subcomponents": [
                        ......
                    ]
                },
                "brew_package": string,
                "name": string,
                "dist_git_branch": <string|null>,
                "dist_git_web_url": string,
                "active": true,
                "contacts": [
                    ......
                ],
                "srpm": {
                    "name": string
                } OR null,
                "type": <string|null>
            }

        __NOTE__:

        ``contacts`` field will inherit from corresponding global component
        contacts(with ``"inherited": true``) if any.
        """

        return super(ReleaseComponentViewSet, self).retrieve(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        """
        __Method__:

        PUT:

        ``name``: new release component's name, **REQUIRED**

        ``dist_git_branch``: new release component dist git branch, **OPTIONAL**

        ``bugzilla_component``: bugzilla component name, **OPTIONAL**

        ``brew_package``: brew package name, **OPTIONAL**

        ``"active"``: status of release component, **OPTIONAL**

        ``"srpm"``:
            {
                "name": srpm name of release component
            } OR null, **OPTIONAL**

        ``"type"``: release component type, **OPTIONAL**

        PATCH:

        ``name``: new release component's name, **OPTIONAL**

        ``dist_git_branch``: new release component dist git branch, **OPTIONAL**

        ``bugzilla_component``: bugzilla component name, **OPTIONAL**

        ``brew_package``: brew package name, **OPTIONAL**

        ``"active"``: status of release component, **OPTIONAL**

        ``"srpm"``:
            {
                "name": srpm name of release component
            } OR null,  **OPTIONAL**

        ``"type"``: release component type, **OPTIONAL**

        __URL__: $LINK:releasecomponent-detail:instance_pk$

        __Response__:

            {
                "id": int,
                "release": {
                    "release_id": string,
                    "active": bool
                },
                "global_component": string,
                "bugzilla_component": {
                    ......
                },
                "brew_package": string,
                "name": string,
                "dist_git_branch": <string|null>,
                "dist_git_web_url": string,
                "active": true,
                "contacts": [
                    ......
                ],
                "srpm": {
                    "name": string
                } OR null
            }

        __NOTE__:

        bugzilla_component can be in format parent_component/bugzilla_component or bugzilla_component,
        for example, kernel/filesystem or kernel, single bugzilla_component means parent_component is null.
        {"bugzilla_component": null or "bugzilla_component": ""} is to set bugzilla_component to null,
        while bugzilla_component not given means not update bugzilla_component.
        """
        obj = self.get_object()
        signals.releasecomponent_pre_update.send(
            sender=obj.__class__,
            release_component=obj,
            request=request)
        response = super(ReleaseComponentViewSet, self).update(request, *args, **kwargs)
        signals.releasecomponent_post_update.send(
            sender=self.object.__class__,
            release_component=self.object,
            request=request)
        return response

    def create(self, request, *args, **kwargs):
        """
        __Method__:
        POST

        __URL__: $LINK:releasecomponent-list$

        __Data__:

            {
                'name':                          string,         # required
                'release':                       string,         # required
                'global_component':              string,         # required
                'dist_git_branch':               string,         # optional
                'bugzilla_component':            string,         # optional
                'brew_package':                  string,         # optional
                'active':                        bool,           # optional
                'srpm':
                    {
                        "name":                  string,
                    } OR null,                                   # optional
                'type':                          string,         # optional
            }

        *type*: $LINK:releasecomponenttype-list$

        __Response__:

            {
                "id": int,
                "release": {
                    "release_id": string,
                    "active": bool
                },
                "global_component": string,
                "brew_package": string,
                "name": string,
                "dist_git_branch": <string|null>,
                "dist_git_web_url": string,
                "active": true,
                "bugzilla_component": {
                    "id": int,
                    "name": string,
                    "parent_component": null,
                    "subcomponents": [
                        ......
                    ]
                },
                "contacts": [
                    ......
                ],
                "srpm": {
                    "name": string
                } OR null,
                "type": <string|null>
            }

        __NOTE__:

        bugzilla_component can be in format parent_component/bugzilla_component or bugzilla_component,
        for example, kernel/filesystem or kernel, single bugzilla_component means parent_component is null.
        """
        response = super(ReleaseComponentViewSet, self).create(request, *args, **kwargs)

        if response.status_code == status.HTTP_201_CREATED:
            signals.releasecomponent_post_update.send(
                sender=self.object.__class__,
                release_component=self.object,
                request=request)
        return response

    def destroy(self, request, *args, **kwargs):
        """
        __Method__:
        DELETE

        __URL__: $LINK:releasecomponent-detail:instance_pk$

        __Response__:

            STATUS: 204 NO CONTENT

        __Example__:

            curl -X DELETE -H "Content-Type: application/json" $URL:releasecomponent-detail:1$
        """
        return super(ReleaseComponentViewSet, self).destroy(request, *args, **kwargs)

    def bulk_update(self, request, *args, **kwargs):
        """
        __Method__:
        PUT

        __URL__: $LINK:releasecomponent-list$

        __Data__:

            {
                'releases':                                  array,          # optional
                'global_component':                          string,         # required
                'contacts': [
                    {
                        'contact_role':                      string,         # required
                        'contact': {
                            <'username'|'mail_name'>:        string,         # required
                            'email:                          string,         # required
                        }
                    },
                    ......
                ]
            }
        __Response__:

            [
                {
                    "id": int,
                    "release": {
                        "release_id": string,
                        "active": bool
                    },
                    "global_component": string,
                    "bugzilla_component": string,
                    "brew_package": string
                    "name": string,
                    "dist_git_branch": <string|null>,
                    "dist_git_web_url": string,
                    "active": true,
                    "contacts": [
                        ......
                    ],
                    "srpm": {
                        "name": string,
                    } OR null,
                    "type": <string|null>
                },
                ......
            ]
        """
        required_fields = set(("global_component", "contacts"))
        missing_fields = required_fields - set(request.data.keys())
        if missing_fields:
            return Response(status=status.HTTP_400_BAD_REQUEST,
                            data={'detail': 'Missing arguments: %s' % ', '.join(missing_fields)})

        global_component_name = request.data.get('global_component')
        releases = request.data.get('releases')
        contacts = request.data.get('contacts')

        if not global_component_name:
            return Response({"detail": "global_component is required."}, status=status.HTTP_400_BAD_REQUEST)

        qs = self.get_queryset().filter(global_component__name=global_component_name)

        if releases:
            release = (releases,) if not isinstance(releases, list) else releases
            qs = qs.filter(release__release_id__in=release)

        # iterate release component records
        for row in qs.iterator():
            context = self.get_serializer_context()
            context.update({'extra_kwargs': {'instance_pk': row.id}})
            contact_serializer = HackedContactSerializer(data=contacts,
                                                         many=True,
                                                         context=context)

            if not contact_serializer.is_valid():
                return Response(contact_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            # contact does not exist in this release component
            # dump release component before update
            pre_export = row.export()
            # iterate new contacts.
            for obj in contact_serializer.validated_data:
                if not row.contacts.filter(pk=obj.pk).exists():
                    overwrite_contact = row.contacts.filter(contact_role_id=obj.contact_role_id)
                    if overwrite_contact.exists():
                        # release component has the same contact type contact.
                        # drop it and insert new one.
                        overwrite_contact.delete()
                    # save new contact.
                    row.contacts.add(obj)
            request.changeset.add("releasecomponent",
                                  row.pk,
                                  json.dumps(pre_export),
                                  json.dumps(row.export()))
        serializer = ReleaseComponentSerializer(instance=qs, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def bulk_partial_update(self, request):
        # Without this definition, bulk_operations would pick up PATCH
        # requests, convert them to PUT with kwargs['partial'] = True and an
        # error about potentially missing keys would be returned. This way it
        # says PATCH is not allowed.
        return self.http_method_not_allowed(request)


class ReleaseComponentContactViewSet(HackedComponentContactMixin,
                                     viewsets.PDCModelViewSet):
    """
    ##Overview##

    This page shows the usage of the **Release Component Contact API**, please
    see the following for more details.

    ##Test tools##

    You can use ``curl`` in terminal, with -X _method_ (GET|POST|PUT|DELETE),
    -d _data_ (a json string). or GUI plugins for
    browsers, such as ``RESTClient``, ``RESTConsole``.
    """
    model = ReleaseComponent
    queryset = ReleaseComponent.objects.all()
    serializer_class = HackedContactSerializer
    gcc_serializer_class = HackedContactSerializer
    extra_query_params = ('contact_role', )

    def get_queryset(self):
        rc_id = self.kwargs.get("instance_pk", None)
        release_component = get_object_or_404(ReleaseComponent, pk=rc_id)
        return release_component.contacts.all()

    def get_serializer_context(self):
        super_class = super(ReleaseComponentContactViewSet, self)
        ret = super_class.get_serializer_context()
        ret.update({
            'extra_kwargs': self.kwargs
        })
        return ret

    def get_serializer(self, *args, **kwargs):
        serializer_class = self.get_serializer_class()
        kwargs['context'] = self.get_serializer_context()
        kwargs['view_name'] = 'releasecomponentcontact-detail'
        return serializer_class(*args, **kwargs)

    def list(self, request, *args, **kwargs):
        """
        __Method__:
        GET

        __URL__: $LINK:releasecomponentcontact-list:rc_instance_pk$

        __QUERY Params__:

        %(FILTERS)s

        __Response__:

            [
                {
                    "url": url,
                    "contact_role": string,
                    "contact": {
                        <"mail_name"|"username">: string,
                        "email": string
                    }
                },
                ......
            ]
        """
        # FIXME: Design issue here. Contact inheritance(PDC-184) requires access
        # of different resource under same url. e.g., could view global component
        # contact information under release component contact list.
        # This is not RESTful. To meet this needs, I have to hard code this
        # `ViewSet.list`, as I failed to find an elegant way. Unfortunately we
        # cannot benefit from DRF built-in features such as pagination.
        rc_id = kwargs.get("instance_pk", None)
        # Release Component object
        rc = get_object_or_404(ReleaseComponent, pk=rc_id)
        gcc_qs = GlobalComponent.objects.get(pk=rc.global_component_id).contacts.all()
        rcc_qs = rc.contacts.all()
        # Contact type based inheritance mechanisms(excerpted from JIRA PDC-184)
        # - Input without contact_role, output contacts including
        #   release_component's contacts and global_component's contacts which
        #   is not in self contacts.
        # - Input with specific contact_role which is only in global_component
        #   output contact will inherit from global_component's.
        # - Input with specific contact_role which is in release_component,
        #   output contact will be it's own contact
        rcc_types = map(lambda s: s.contact_role.name, rcc_qs)
        # excluded_types: existing contact types for release component
        excluded_types = ContactRole.objects.filter(name__in=rcc_types)
        # exclude co-exists(same contact type) contacts from global component.
        gcc_qs = gcc_qs.exclude(contact_role__in=excluded_types)

        query_params = request.query_params
        contact_role = query_params.getlist('contact_role')
        # FIXME: add more options in query parameter.
        # username = query_params.getlist('username')
        # mail_name = query_params.getlist('mail_name')
        # email = query_params.getlist('email')
        if contact_role:
            c_types = ContactRole.objects.filter(name__in=contact_role)
            gcc_qs = gcc_qs.filter(contact_role__in=c_types)
            rcc_qs = rcc_qs.filter(contact_role__in=c_types)

        context = self.get_serializer_context()
        view_name = 'releasecomponentcontact-detail'
        serializer = self.serializer_class(rcc_qs, many=True,
                                           context=context,
                                           view_name=view_name)
        ret = serializer.data
        # FIXME: We need to add identity `inherited=True` for global component
        # contacts in the resulting release component contacts(PDC-166).
        # Since the attribute `inherited` only makes sense for release component
        # contacts, it's not appropriate to hack this `inherited=True` stuff from
        # within the GlobalComponentContactSerializer.
        # Below is an ugly hack over GlobalComponentContactSerializer.data.
        # Note that with this change, the resulting contact representations will
        # be in-consistent accross global/release component contacts.
        # We need to access inconsistent resources under a specific URL,
        # in our case, we need to access release component contacts as well as
        # global component contact (if any) under the same url.
        # This is non-semantic URL design [1] and needs a better approach.
        # [1] http://en.wikipedia.org/wiki/Semantic_URL
        gcc_serializer = self.gcc_serializer_class(
            gcc_qs,
            many=True,
            inherited=True,
            # NOTE(xchu): The `HackedContactSerializer` used here need `instance_pk`
            #             in the context `extra_kwargs` to build the 'url' in response.
            #             For the inherited contacts, we need to pass
            #             `global_component_id` as `instance_pk`.
            context={'request': request,
                     'extra_kwargs': {'instance_pk': rc.global_component_id}})
        gc_contacts = gcc_serializer.data
        ret.extend(gc_contacts)

        return Response(ret)

    def retrieve(self, request, *args, **kwargs):
        """
        __Method__:
        GET

        __URL__: $LINK:releasecomponentcontact-detail:rc_instance_pk:relation_pk$

        __Response__:

            {
                "url": url,
                "contact_role": string,
                "contact": {
                    <"mail_name"|"username">: string,
                    "email": string
                }
            }
        """
        return super(ReleaseComponentContactViewSet, self).retrieve(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        """
        __Method__:
        POST

        __URL__: $LINK:releasecomponentcontact-list:rc_instance_pk$

        __Data__:

            {
                'contact_role':                       string,         # required
                'contact': {
                    <'username'|'mail_name'>:         string,         # required
                    'email:                           string,         # required
                }
            }
        __Response__:

            {
                "url": url,
                "contact_role": string,
                "contact": {
                    <"mail_name"|"username">: string,
                    "email": string
                }
            }
        """
        return super(ReleaseComponentContactViewSet, self).create(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """
        __Method__:
        DELETE

        __URL__: $LINK:releasecomponentcontact-detail:rc_instance_pk:relation_pk$

        __Response__:

            STATUS: 204 NO CONTENT

        __Example__:

            curl -X DELETE -H "Content-Type: application/json" $URL:releasecomponentcontact-detail:2:3175$
        """
        pk = self.kwargs.get('pk')
        try:
            contact = RoleContact.objects.get(id=pk)
        except RoleContact.DoesNotExist:
            return Response(data={'detail': 'Specified TypedContact[%s] not found.' % pk},
                            status=status.HTTP_404_NOT_FOUND)

        rc_id = self.kwargs.get('instance_pk')
        try:
            rc = ReleaseComponent.objects.get(id=rc_id)
        except ReleaseComponent.DoesNotExist:
            return Response(data={'detail': 'Specified ReleaseComponent[%s] not found.' % rc_id},
                            status=status.HTTP_404_NOT_FOUND)

        old_value = json.dumps(rc.export())
        if contact in rc.contacts.all():
            rc.contacts.remove(contact)
            request.changeset.add("releasecomponent", rc.pk, old_value, json.dumps(rc.export()))
            return Response(status=status.HTTP_204_NO_CONTENT)
        elif contact in rc.global_component.contacts.all():
            return Response(
                data={'detail': 'Contact[%s] is inherited from GlobalComponent[%s] and can only be deleted from there.'
                      % (pk, rc.global_component.pk)},
                status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(
                data={'detail': 'Can not be deleted since Contact[%s] is not in ReleaseComponent[%s].' % (pk, rc_id)},
                status=status.HTTP_404_NOT_FOUND)

    def update(self, request, *args, **kwargs):
        return self.http_method_not_allowed(request, *args, **kwargs)

    def bulk_update(self, request, *args, **kwargs):
        return self.http_method_not_allowed(request, *args, **kwargs)


class BugzillaComponentViewSet(viewsets.PDCModelViewSet):
    """
    ##Overview##

    This page shows the usage of the **Bugzilla Component API**, please see the
    following for more details.
    Bugzilla Component includes what products and components have sub components.
    It also can be tracked in Release Component API.

    ##Test tools##

    You can use ``curl`` in terminal, with -X _method_ (GET|POST|PUT|DELETE),
    -d _data_ (a json string). or GUI plugins for
    browsers, such as ``RESTClient``, ``RESTConsole``.

    """
    model = BugzillaComponent
    queryset = model.objects.all()
    serializer_class = BugzillaComponentSerializer
    filter_class = BugzillaComponentFilter

    def list(self, request, *args, **kwargs):
        """
        __Method__:
        GET

        __URL__: $LINK:bugzillacomponent-list$

        __QUERY Params__:

        %(FILTERS)s

        __Response__:

            # paged lists
            {
                "count": int,
                "next": url,
                "previous": url,
                "results": [
                    {
                        "id": int,
                        "name: string,
                        "parent_component": string,
                        "subcomponents": [
                            ...
                        ]
                    }
                    ...
            }
        """
        return super(BugzillaComponentViewSet, self).list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        """
        __Method__:
        GET

        __URL__: $LINK:bugzillacomponent-detail:instance_pk$

        __Response__:

            {
                "id": int,
                "name": string,
                "parent_component": string,
                "subcomponents": [
                    ...
                ]
            }
        """

        return super(BugzillaComponentViewSet, self).retrieve(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        """
        __Method__:

        PUT: for full fields update
            {'name': 'new_name', 'parent_pk': new_parent_pk}

        PATCH: for partial update
            {'name': 'new_name'}
            or
            {'parent_pk': new_parent_pk}
            or
            {'name': 'new_name', 'parent_pk': new_parent_pk}

        __URL__: $LINK:bugzillacomponent-detail:instance_pk$

        __Response__:

            {
                "id": int,
                "name": string,
                "parent_component": string,
                "subcomponents": [
                    ...
                ]
            }

        __NOTE__:

        For PATCH, {"parent_pk": null} is to set parent_pk to null, while
        parent_pk not given means not update parent_pk
        """
        partial = kwargs.pop('partial', False)
        obj = self.get_object()
        p_bc = None

        if obj is None:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
        if not partial:
            if any(['name' not in request.data, 'parent_pk' not in request.data]):
                return Response({"detail": "PUT for full fields update, filed 'name' or 'parent_pk' is missing"},
                                status=status.HTTP_400_BAD_REQUEST)

        if 'name' in request.data:
            name = request.data.get('name')
        else:
            name = obj.name
        if name is None or name.strip() == "":
            return Response({'detail': 'Missing bugzilla component name.'},
                            status=status.HTTP_400_BAD_REQUEST)

        if 'parent_pk' in request.data:
            parent_pk = request.data.get('parent_pk')
        elif obj.parent_component:
            parent_pk = obj.parent_component.pk
        else:
            parent_pk = None

        if type(parent_pk) not in (types.IntType, types.NoneType):
            return Response({'detail': 'Parent_pk is not typeof int or Nonetype.'},
                            status=status.HTTP_400_BAD_REQUEST)

        if parent_pk is not None:
            try:
                p_bc = BugzillaComponent.objects.get(pk=parent_pk)
            except BugzillaComponent.DoesNotExist:
                return Response({'detail': 'Parent bugzilla component with pk %s does not exist' % parent_pk},
                                status=status.HTTP_404_NOT_FOUND)
        else:
            try:
                bc = BugzillaComponent.objects.get(name=name, parent_component=None)
                # Name+parent_component is not unique if parent_component is None,
                # Check if it is an object update twice or update to an already exists object.
                if not bc == obj:
                    return Response({"detail": "Bugzilla component with this Name and Parent component already exists."},
                                    status=status.HTTP_400_BAD_REQUEST)
            except BugzillaComponent.DoesNotExist:
                pass
        obj.parent_component = p_bc

        serializer = self.get_serializer(obj, data=request.data,
                                         partial=partial)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            self.perform_update(serializer)
        except InvalidMove as err:
            return Response({'detail': err.message}, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.data, status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        """
        __Method__:
        POST

        __URL__: $LINK:bugzillacomponent-list$

        __Data__:

            {
                'name':                          string,         # required
                'parent_pk':                     int,            # optional
            }
        __Response__:

            {
                "id": int,
                "name": string,
                "parent_component": string,
                "subcomponents": [
                    ...
                ]
            }

        __NOTE__:

        Root bugzilla component will be created if parent_pk is not given or
        {"parent_pk": null}
        """
        data = request.data

        serializer_class = self.get_serializer_class()
        extra_keys = set(data.keys()) - serializer_class().get_allowed_keys()
        StrictSerializerMixin.maybe_raise_error(extra_keys)

        name = data.get('name')
        parent_pk = data.get('parent_pk')

        if type(parent_pk) not in (types.IntType, types.NoneType):
            return Response({'detail': 'Parent_pk is not typeof int or Nonetype.'},
                            status=status.HTTP_400_BAD_REQUEST)
        p_bc = None

        if name is None or name.strip() == "":
            return Response({'detail': 'Missing bugzilla component name.'},
                            status=status.HTTP_400_BAD_REQUEST)

        if parent_pk is not None:
            try:
                p_bc = BugzillaComponent.objects.get(pk=parent_pk)
            except BugzillaComponent.DoesNotExist:
                return Response({'detail': 'Parent bugzilla component with pk %s does not exist' % parent_pk},
                                status=status.HTTP_404_NOT_FOUND)
        try:
            bc, created = BugzillaComponent.objects.get_or_create(
                name=name,
                parent_component=p_bc)
        except ValidationError as exc:
            return Response(exc.message_dict, status=status.HTTP_400_BAD_REQUEST)

        serializer = serializer_class(instance=bc, data=request.data, context={'request': request})

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        headers = self.get_success_headers(serializer.data)
        if created:
            self.perform_create(serializer)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        else:
            return Response(serializer.data, status=status.HTTP_200_OK, headers=headers)

    def destroy(self, request, *args, **kwargs):
        """
        __Method__:
        DELETE

        __URL__: $LINK:bugzillacomponent-detail:instance_pk$

        __Response__:

            STATUS: 204 NO CONTENT

        __NOTE__:

        Descendants will be deleted as well.

        __Example__:

            curl -X DELETE -H "Content-Type: application/json" $URL:bugzillacomponent-detail:1$
        """
        return super(BugzillaComponentViewSet, self).destroy(request, *args, **kwargs)

    def perform_destroy(self, instance):
        delete_obj_dict = {}
        for descendant in instance.get_descendants():
            delete_obj_dict[descendant.id] = descendant.export()
        model_name = ContentType.objects.get_for_model(instance).model
        for delete_obj_pk, delete_obj_desc in delete_obj_dict.iteritems():
            self.request.changeset.add(model_name,
                                       delete_obj_pk,
                                       json.dumps(delete_obj_desc),
                                       'null')
            del delete_obj_pk
            del delete_obj_desc

        rc_queryset = ReleaseComponent.objects.filter(bugzilla_component=instance)

        old_value_dict = {}
        for rc in rc_queryset:
            old_value_dict[rc.pk] = rc.export()

        super(BugzillaComponentViewSet, self).perform_destroy(instance)

        for old_rc_pk in old_value_dict.keys():
            m_rc = ReleaseComponent.objects.get(pk=old_rc_pk)
            new_value = m_rc.export()
            model_name = ContentType.objects.get_for_model(m_rc).model
            self.request.changeset.add(model_name,
                                       old_rc_pk,
                                       json.dumps(old_value_dict[old_rc_pk]),
                                       json.dumps(new_value))


class GroupTypeViewSet(viewsets.PDCModelViewSet):
    """
    API endpoint that allows component_group_types to be viewed or edited.
    """
    serializer_class = GroupTypeSerializer
    queryset = GroupType.objects.all()
    filter_class = GroupTypeFilter

    def create(self, request, *args, **kwargs):
        """
        __Method__: POST

        __URL__: $LINK:componentgrouptype-list$

        __Data__:

            {
                "name":             string,     # required
                "description":      string      # optional
            }

        __Response__:

            {
                "name":             string,
                "description":      string|null
            }
        """
        return super(GroupTypeViewSet, self).create(request, *args, **kwargs)

    def list(self, request, *args, **kwargs):
        """
        __Method__: GET

        __URL__: $LINK:componentgrouptype-list$

        __Query params__:

        %(FILTERS)s

        __Response__:

            # paged list
            {
                "count": int,
                "next": url,
                "previous": url,
                "results": [
                    {
                        "name": string,
                        "description": string
                    },
                    ...
                ]
            }
        """
        return super(GroupTypeViewSet, self).list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        """
        __Method__: GET

        __URL__: $LINK:componentgrouptype-detail:instance_pk$

        __Response__:

            {
                "name": string,
                "description": string
            }
        """
        return super(GroupTypeViewSet, self).retrieve(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        """
        __Method__: PUT, PATCH

        __URL__: $LINK:componentgrouptype-detail:instance_pk$

        __Data__:

            {
                "name":             string,
                "description":      string
            }

        __Response__:

            {
                "name":             string,
                "description":      string
            }
        """
        return super(GroupTypeViewSet, self).update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """
        __Method__: DELETE

        __URL__: $LINK:componentgrouptype-detail:instance_pk$

        __Response__:

            {
                "Response": "No content"
            }
        """
        return super(GroupTypeViewSet, self).destroy(request, *args, **kwargs)


class GroupViewSet(viewsets.PDCModelViewSet):
    """
    API endpoint that allows component_groups to be viewed or edited.
    """
    serializer_class = GroupSerializer
    queryset = ReleaseComponentGroup.objects.all()
    filter_class = GroupFilter

    def create(self, request, *args, **kwargs):
        """
        __Method__: POST

        __URL__: $LINK:componentgroup-list$

        __Data__:

            {
                "group_type":       string,         # required
                "release":          string,         # required
                "description":      string,         # required
                "components":       list            # optional
            }

        *group_type*: $LINK:componentgrouptype-list$

        __Note__:

          * components: list of release_components, eg: [{"id": 1}, {"id": 2}] or
          [{"release": "release-1.0", "global_component": "python", "name": "python27"}]
          * group_type, release and release_components have to be existed before creating Release Component Group
          * It's not allowed to group release_components from different releases

        __Response__:

            {
                "release":          string,
                "components":       list,
                "description":      string,
                "group_type":       string
            }

        """
        return super(GroupViewSet, self).create(request, *args, **kwargs)

    def list(self, request, *args, **kwargs):
        """
        __Method__: GET

        __URL__: $LINK:componentgroup-list$

        __Query params__:

        %(FILTERS)s

        __Response__:

            # paged list
            {
                "count": int,
                "next": url,
                "previous": url,
                "results": [
                    {
                        "release": string,
                        "components": list,
                        "description": string,
                        "group_type": string
                    },
                    ...
                ]
            }
        """
        return super(GroupViewSet, self).list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        """
        __Method__: GET

        __URL__: $LINK:componentgroup-detail:instance_pk$

        __Response__:

            {
                "release": string,
                "components": list,
                "description": string,
                "group_type": string
            }

        """
        return super(GroupViewSet, self).retrieve(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        """
        __Method__: PUT, PATCH

        __URL__: $LINK:componentgroup-detail:instance_pk$

        __Data__:

            {
                "group_type":       string,
                "release":          string,
                "description":      string,
                "components":       list
            }

        __Note__:

          * components: list of release_components, eg: [{"id": 1}, {"id": 2}] or
          [{"release": "release-1.0", "global_component": "python", "name": "python27"}]

        __Response__:

            {
                "release": string,
                "components": list,
                "description": string,
                "group_type": string
            }
        """
        return super(GroupViewSet, self).update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """
        __Method__: DELETE

        __URL__: $LINK:componentgroup-detail:instance_pk$

        __Response__:

            {
                "Response": "No content"
            }
        """
        return super(GroupViewSet, self).destroy(request, *args, **kwargs)


class ReleaseComponentRelationshipTypeViewSet(viewsets.StrictQueryParamMixin,
                                              mixins.ListModelMixin,
                                              drf_viewsets.GenericViewSet):
    """
    API endpoint that allows release_component_relationship_types to be viewed.
    """
    serializer_class = RCRelationshipTypeSerializer
    queryset = ReleaseComponentRelationshipType.objects.all()

    def list(self, request, *args, **kwargs):
        """
        __Method__: GET

        __URL__: $LINK:componentrelationshiptype-list$

        __Response__:

            # paged list
            {
                "count": int,
                "next": url,
                "previous": url,
                "results": [
                    {
                        "name": string,
                    },
                    ...
                ]
            }
        """
        return super(ReleaseComponentRelationshipTypeViewSet, self).list(request, *args, **kwargs)


class ReleaseComponentRelationshipViewSet(viewsets.PDCModelViewSet):
    """
    API endpoint that allows release component relationship to be viewed or edited.
    """
    serializer_class = ReleaseComponentRelationshipSerializer
    queryset = ReleaseComponentRelationship.objects.all()
    filter_class = ReleaseComponentRelationshipFilter

    def create(self, request, *args, **kwargs):
        """
        __Method__: POST

        __URL__: $LINK:rcrelationship-list$

        __Data__:

            {
                "from_component":       dict,         # required
                "type":                 string,       # required
                "to_component":         dict,         # required
            }

        *type*: $LINK:componentrelationshiptype-list$

        __Note__:

          * from_component: {"id": 1} or {"release": "release-1.0", "global_component": "python", "name": "python27"}
          * type: relationship type
          * to_component: {"id": 2} or {"release": "release-2.0", "global_component": "python", "name": "python27"}

        __Response__:

            {
                "from_component": {
                    "id":       release component id,
                    "name":     string,
                    "release":  string
                },
                "id":   relationship id,
                "to_component": {
                    "id":       release component id,
                    "name":     string,
                    "release":  string
                },
                "type": string
            }

        """
        return super(ReleaseComponentRelationshipViewSet, self).create(request, *args, **kwargs)

    def list(self, request, *args, **kwargs):
        """
        __Method__: GET

        __URL__: $LINK:rcrelationship-list$

        __Query params__:

        %(FILTERS)s

        __Response__:

            # paged list
            {
                "count": int,
                "next": url,
                "previous": url,
                "results": [
                    {
                        "from_component": {
                            "id":       release component id,
                            "name":     string,
                            "release":  string
                        },
                        "id":   relationship id,
                        "to_component": {
                            "id":       release component id,
                            "name":     string,
                            "release":  string
                        },
                        "type": string
                    },
                    ...
                ]
            }
        """
        return super(ReleaseComponentRelationshipViewSet, self).list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        """
        __Method__: GET

        __URL__: $LINK:rcrelationship-detail:instance_pk$

        __Response__:

             {
                "from_component": {
                    "id":       release component id,
                    "name":     string,
                    "release":  string
                },
                "id":   relationship id,
                "to_component": {
                    "id":       release component id,
                    "name":     string,
                    "release":  string
                },
                "type":     string
            }

        """
        return super(ReleaseComponentRelationshipViewSet, self).retrieve(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        """
        __Method__: PUT, PATCH

        __URL__: $LINK:rcrelationship-detail:instance_pk$

        __Data__:

            {
                "from_component":       dict,         # required
                "type":                 string,       # required
                "to_component":         dict,         # required
            }

        __Note__:

          * from_component: {"id": 1} or {"release": "release-1.0", "global_component": "python", "name": "python27"}
          * to_component: {"id": 2} or {"release": "release-2.0", "global_component": "python", "name": "python27"}

        __Response__:

            {
                "from_component": {
                    "id":       release component id,
                    "name":     string,
                    "release":  string
                },
                "id":   relationship id,
                "to_component": {
                    "id":       release component id,
                    "name":     string,
                    "release":  string
                },
                "type":     string
            }
        """
        return super(ReleaseComponentRelationshipViewSet, self).update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """
        __Method__: DELETE

        __URL__: $LINK:rcrelationship-detail:instance_pk$

        __Response__:

            {
                "Response": "No content"
            }
        """
        return super(ReleaseComponentRelationshipViewSet, self).destroy(request, *args, **kwargs)
