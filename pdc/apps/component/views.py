#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
import json
import types

from django.contrib.contenttypes.models import ContentType
from django.shortcuts import get_object_or_404
from django.http import Http404

from mptt.exceptions import InvalidMove

from rest_framework import status, mixins
from rest_framework import viewsets as drf_viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from pdc.apps.common import viewsets
from pdc.apps.common.constants import PUT_OPTIONAL_PARAM_WARNING
from pdc.apps.common.models import Label
from pdc.apps.common.serializers import LabelSerializer, StrictSerializerMixin
from pdc.apps.utils.utils import generate_warning_header_dict
from pdc.apps.common.filters import LabelFilter
from pdc.apps.auth.permissions import APIPermission

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
                          BugzillaComponentSerializer,
                          GroupSerializer,
                          GroupTypeSerializer,
                          ReleaseComponentRelationshipSerializer,
                          ReleaseComponentTypeSerializer,
                          RCRelationshipTypeSerializer)
from .filters import (ComponentFilter,
                      ReleaseComponentFilter,
                      BugzillaComponentFilter,
                      GroupFilter,
                      GroupTypeFilter,
                      ReleaseComponentRelationshipFilter,
                      ReleaseComponentRelationshipTypeFilter)
from . import signals


class GlobalComponentViewSet(viewsets.PDCModelViewSet):
    model = GlobalComponent
    queryset = GlobalComponent.objects.all().order_by('id')
    serializer_class = GlobalComponentSerializer
    filter_class = ComponentFilter

    doc_create = """
        __Example__:

            curl -X POST -H "Content-Type: application/json" $URL:globalcomponent-list$ \\
                    -d '{ "name": "Demo", "dist_git_path": "rpm/Demo"}'
            # output
            {
                "id": 4181,
                "name": "Demo",
                "dist_git_path": "rpm/Demo",
                "dist_git_web_url": "http://pkgs.example.com/cgit/rpms/rpm/Demo"
                "labels": [],
                "upstream": null | {
                                "homepage": string,
                                "scm_type": string,
                                "scm_url": string
                            }
            }
    """

    doc_update = """
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
                "labels": [],
                "upstream": null
            }
    """

    doc_destroy = """
        __Example__:

            curl -X DELETE -H "Content-Type: application/json" $URL:globalcomponent-detail:4181$
    """


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
    queryset = Label.objects.all().order_by('id')
    serializer_class = LabelSerializer
    filter_class = LabelFilter

    def get_queryset(self):
        gc_id = self.kwargs.get('instance_pk')
        try:
            gc = get_object_or_404(GlobalComponent, id=gc_id)
        except ValueError:
            # Raised when non-numeric instance_pk is given.
            raise Http404('Global component with id=%s not found' % gc_id)
        labels = gc.labels.all()
        return labels

    doc_list = """
        __Method__: `GET`

        __URL__: $LINK:globalcomponentlabel-list:component_id$

        __Query params__:

        %(FILTERS)s

        __Response__: a paged list of following objects

        %(SERIALIZER)s

    """

    doc_retrieve = """
        __Method__: `GET`

        __URL__: $LINK:globalcomponentlabel-detail:component_id:label_id$

        __Response__:

        %(SERIALIZER)s
    """

    def update(self, request, *args, **kwargs):
        self.http_method_not_allowed(request, *args, **kwargs)

    def bulk_update(self, request, *args, **kwargs):
        self.http_method_not_allowed(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """
        Delete a label from a specified global component, return an empty
        response if success.

        __URL__: $LINK:globalcomponentlabel-detail:component_id:label_id$
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

        __Method__: `POST`

        __URL__: $LINK:globalcomponentlabel-list:component_id$

        __Data__:

            {
                "name": "string"
            }

        __Response__:

        %(SERIALIZER)s
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
    queryset = ReleaseComponentType.objects.all().order_by('id')
    permission_classes = (APIPermission,)

    doc_list = """
        __Method__: GET

        __URL__: $LINK:releasecomponenttype-list$

        __Response__: a paged list of following objects

        %(SERIALIZER)s
    """


class ReleaseComponentViewSet(viewsets.PDCModelViewSet):
    """
    ##Overview##

    This page shows the usage of the **Release Component API**, please see the
    following for more details.

    ##Test tools##

    You can use ``curl`` in terminal, with -X _method_ (GET|POST|PUT|DELETE),
    -d _data_ (a json string). or GUI plugins for
    browsers, such as ``RESTClient``, ``RESTConsole``.

    """
    model = ReleaseComponent
    queryset = model.objects.all().order_by('id')
    serializer_class = ReleaseComponentSerializer
    filter_class = ReleaseComponentFilter
    extra_query_params = ('include_inactive_release', )
    docstring_macros = PUT_OPTIONAL_PARAM_WARNING

    def get_queryset(self):
        qs = self.model.objects.all()
        query_params = self.request.query_params
        # include_inactive_release is not a field in model ReleaseComponent, so
        # it can not use django-filter to handle.
        if 'include_inactive_release' not in query_params:
            qs = qs.filter(release__active=True)
        return qs

    doc_list = """
        __Method__:
        GET

        __URL__: $LINK:releasecomponent-list$

        __Query Params__:

        %(FILTERS)s

        Components for inactive releases are not shown by default. You can
        change this with `include_inactive_release` set to any non-empty value.

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
                        "srpm": {
                            "name": string
                        } OR null,
                        "type": <string|null>
                    }
                    ...
            }
    """

    doc_retrieve = """
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
                "srpm": {
                    "name": string
                } OR null,
                "type": <string|null>
            }
    """

    def update(self, request, *args, **kwargs):
        """
        %(PUT_OPTIONAL_PARAM_WARNING)s

        __Method__:

        PUT:

        ``name``: new release component's name, **REQUIRED**

        ``dist_git_branch``: new release component dist git branch, **OPTIONAL**

        ``bugzilla_component``: bugzilla component name, **OPTIONAL**

        ``brew_package``: brew package name, **OPTIONAL**

        ``"active"``: status of release component, defalut=true,**OPTIONAL**

        ``"srpm"``:
            {
                "name": srpm name of release component
            } OR null, **OPTIONAL**

        ``"type"``: release component type, **OPTIONAL**

        ``"global_component"``: release component's global component, **OPTIONAL**

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

        ``"global_component"``: release component's global component, **OPTIONAL**

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

    doc_destroy = """
        __Method__:
        DELETE

        __URL__: $LINK:releasecomponent-detail:instance_pk$

        __Response__:

            STATUS: 204 NO CONTENT

        __Example__:

            curl -X DELETE -H "Content-Type: application/json" $URL:releasecomponent-detail:1$
    """


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
    queryset = model.objects.all().order_by('id')
    serializer_class = BugzillaComponentSerializer
    filter_class = BugzillaComponentFilter

    doc_list = """
        __Method__:
        GET

        __URL__: $LINK:bugzillacomponent-list$

        __Query Params__:

        %(FILTERS)s

        __Response__: a paged list of following objects

        %(SERIALIZER)s
    """

    doc_retrieve = """
        __Method__:
        GET

        __URL__: $LINK:bugzillacomponent-detail:instance_pk$

        __Response__:

        %(SERIALIZER)s
    """

    def update(self, request, *args, **kwargs):
        """
        __Method__: `PUT`, `PATCH`

        __URL__: $LINK:bugzillacomponent-detail:instance_pk$

        __Data__:

            {
                "name":                        "string",
                "parent_pk":                   "int"
            }

        __Response__:

        %(SERIALIZER)s

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
                "name":                        "string",         # required
                "parent_pk: (default=None)":   "int"             # optional
            }

        __Response__:

        %(SERIALIZER)s

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

        if created:
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        else:
            return Response(serializer.data, status=status.HTTP_200_OK,
                            headers=generate_warning_header_dict("The bugzilla component already exists"))

    doc_destroy = """
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
    queryset = GroupType.objects.all().order_by('id')
    filter_class = GroupTypeFilter
    docstring_macros = PUT_OPTIONAL_PARAM_WARNING

    doc_create = """
        __Method__: POST

        __URL__: $LINK:componentgrouptype-list$

        __Data__:

        %(WRITABLE_SERIALIZER)s

        __Response__:

        %(SERIALIZER)s
    """

    doc_list = """
        __Method__: GET

        __URL__: $LINK:componentgrouptype-list$

        __Query params__:

        %(FILTERS)s

        __Response__: a paged list of following objects

        %(SERIALIZER)s
    """

    doc_retrieve = """
        __Method__: GET

        __URL__: $LINK:componentgrouptype-detail:instance_pk$

        __Response__:

        %(SERIALIZER)s
    """

    doc_update = """
        %(PUT_OPTIONAL_PARAM_WARNING)s

        __Method__: PUT, PATCH

        __URL__: $LINK:componentgrouptype-detail:instance_pk$

        __Data__:

        %(WRITABLE_SERIALIZER)s

        __Response__:

        %(SERIALIZER)s
    """

    doc_destroy = """
        __Method__: DELETE

        __URL__: $LINK:componentgrouptype-detail:instance_pk$

        __Response__:

        On success, HTTP status code is 204 and the response has no content.
    """


class GroupViewSet(viewsets.PDCModelViewSet):
    """
    API endpoint that allows component_groups to be viewed or edited.
    """
    serializer_class = GroupSerializer
    queryset = ReleaseComponentGroup.objects.all().order_by('id')
    filter_class = GroupFilter

    doc_create = """
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
          [{"release": "release-1.0", "name": "python27"}]
          * group_type, release and release_components have to be existed before creating Release Component Group
          * It's not allowed to group release_components from different releases

        __Response__:

        %(SERIALIZER)s
    """

    doc_list = """
        __Method__: GET

        __URL__: $LINK:componentgroup-list$

        __Query params__:

        %(FILTERS)s

        __Response__: a paged list of following objects

        %(SERIALIZER)s
    """

    doc_retrieve = """
        __Method__: GET

        __URL__: $LINK:componentgroup-detail:instance_pk$

        __Response__:

        %(SERIALIZER)s
    """

    doc_update = """
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
          [{"release": "release-1.0", "name": "python27"}]

        __Response__:

        %(SERIALIZER)s
    """

    doc_destroy = """
        __Method__: DELETE

        __URL__: $LINK:componentgroup-detail:instance_pk$

        __Response__:

        On success, HTTP status code is 204 and the response has no content.
    """


class ReleaseComponentRelationshipTypeViewSet(viewsets.PDCModelViewSet):
    """
    API endpoint that allows release_component_relationship_types to be viewed or edited.
    """
    serializer_class = RCRelationshipTypeSerializer
    queryset = ReleaseComponentRelationshipType.objects.all().order_by('id')
    permission_classes = (APIPermission,)
    filter_class = ReleaseComponentRelationshipTypeFilter

    doc_create = """
        __Method__: POST

        __URL__: $LINK:componentrelationshiptype-list$

        __Data__:

            {
                "name": "string", # required
            }

        *type*: $LINK:componentrelationshiptype-list$

        __Response__:

        %(SERIALIZER)s
    """

    doc_list = """
        __Method__: GET

        __URL__: $LINK:componentrelationshiptype-list$

        __Response__: a paged list of following objects

        %(SERIALIZER)s
    """

    doc_retrieve = """
        __Method__: GET

        __URL__: $LINK:componentrelationshiptype-detail:instance_pk$

        __Response__:

        %(SERIALIZER)s
    """

    doc_update = """
        __Method__: PUT, PATCH

        __URL__: $LINK:componentrelationshiptype-detail:instance_pk$

        __Data__:

            {
                "name": "string", # required
            }

        __Response__:

        %(SERIALIZER)s
    """

    doc_destroy = """
        __Method__: DELETE

        __URL__: $LINK:componentrelationshiptype-detail:instance_pk$

        __Response__:

        On success, HTTP status code is 204 and the response has no content.
    """


class ReleaseComponentRelationshipViewSet(viewsets.PDCModelViewSet):
    """
    API endpoint that allows release component relationship to be viewed or edited.
    """
    serializer_class = ReleaseComponentRelationshipSerializer
    queryset = ReleaseComponentRelationship.objects.all().order_by('id')
    filter_class = ReleaseComponentRelationshipFilter

    doc_create = """
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

          * from_component: {"id": 1} or {"release": "release-1.0", "name": "python27"}
          * type: relationship type
          * to_component: {"id": 2} or {"release": "release-2.0", "name": "python27"}

        __Response__:

        %(SERIALIZER)s
    """

    doc_list = """
        __Method__: GET

        __URL__: $LINK:rcrelationship-list$

        __Query params__:

        %(FILTERS)s

        __Response__: a paged list of following objects

        %(SERIALIZER)s
    """

    doc_retrieve = """
        __Method__: GET

        __URL__: $LINK:rcrelationship-detail:instance_pk$

        __Response__:

        %(SERIALIZER)s
    """

    doc_update = """
        __Method__: PUT, PATCH

        __URL__: $LINK:rcrelationship-detail:instance_pk$

        __Data__:

            {
                "from_component":       dict,         # required
                "type":                 string,       # required
                "to_component":         dict,         # required
            }

        __Note__:

          * from_component: {"id": 1} or {"release": "release-1.0", "name": "python27"}
          * to_component: {"id": 2} or {"release": "release-2.0", "name": "python27"}

        __Response__:

        %(SERIALIZER)s
    """

    doc_destroy = """
        __Method__: DELETE

        __URL__: $LINK:rcrelationship-detail:instance_pk$

        __Response__:

        On success, HTTP status code is 204 and the response has no content.
    """
