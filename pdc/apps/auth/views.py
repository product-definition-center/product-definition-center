# -*- coding: utf-8 -*-
#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
import inspect
import json

from collections import OrderedDict
from django.shortcuts import render, redirect, get_list_or_404
from django.contrib.auth import (REDIRECT_FIELD_NAME, get_user_model,
                                 load_backend)
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.models import Group, Permission
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.conf import settings
from django.urls import NoReverseMatch

from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.decorators import list_route
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import mixins, viewsets
from rest_framework.reverse import reverse

from . import backends
from . import filters
from . import serializers
from . import models
from pdc.apps.auth.models import ResourceApiUrl
from pdc.apps.auth.permissions import APIPermission
from pdc.apps.common.viewsets import StrictQueryParamMixin, ChangeSetUpdateModelMixin, NotificationMixin
from pdc.apps.common import viewsets as common_viewsets
from pdc.apps.utils.SortedRouter import router, URL_ARG_RE
from pdc.apps.utils.utils import (group_obj_export,
                                  convert_method_to_action,
                                  read_permission_for_all,
                                  urldecode)


def remoteuserlogin(request):
    # if REDIRECT_FIELD_NAME is present in request.GET and has blank
    # value, that can cause redirect loop while redirecting to it
    redirect_to = request.GET.get(REDIRECT_FIELD_NAME, '/').strip() or '/'

    if request.user.is_authenticated and request.user.is_active:
        return HttpResponseRedirect(redirect_to)

    try:
        request.session.flush()
    except Exception:
        pass

    if request.user.is_anonymous:
        reason = "Failed to authenticate. Make sure your browser is correctly configured."
    elif not request.user.is_active:
        reason = "Account is not active."

    context = {'reason': reason}
    return render(request, 'auth_error.html', context)


def logout(request):
    # if REDIRECT_FIELD_NAME is present in request.GET and has blank
    # value, that can cause redirect loop while redirecting to it
    redirect_to = request.GET.get(REDIRECT_FIELD_NAME, '/').strip() or '/'

    if not request.user.is_authenticated:
        return HttpResponseRedirect(redirect_to)

    backend = None
    if 'auth_backend' in request.session:
        backend = load_backend(request.session['auth_backend'])

    auth_logout(request)

    if backend:
        redirect_to = getattr(backend, 'logout_url', '') + redirect_to

    return HttpResponseRedirect(redirect_to)


def get_resource_permission_set(user):
    resource_permission_set = set([])
    if user.is_superuser:
        resource_permission_set = set([obj for obj in models.ResourcePermission.objects.all()])
    else:
        if read_permission_for_all():
            resource_permission_set = set([obj for obj in models.ResourcePermission.objects.filter(
                permission__name__iexact='read')])
        group_id_list = [group.id for group in user.groups.all()]
        queryset = models.GroupResourcePermission.objects.filter(group__id__in=group_id_list)

        for group_resource_permission in queryset:
            resource_permission_set.add(group_resource_permission.resource_permission)
    return resource_permission_set


def _change_row(row, value, d=[]):
    http_method = ['create', 'read', 'update', 'delete']
    for v in d:
        try:
            index = http_method.index(v.lower())
            row[index + 1] = value
        except ValueError:
            raise Exception("The action %s is not valid" % v)
    return row


def _get_resource_permissions_matrix(user):
    dict_resource_perm_map = {}
    result = []

    resource_permission_set = get_resource_permission_set(user)
    for resource_permission in resource_permission_set:
        resource_name = resource_permission.resource.name
        permission_name = resource_permission.permission.name
        dict_resource_perm_map.setdefault(resource_name, []).append(permission_name)

    ori_action_dict = {}
    for resource_name, view_set, _ in router.registry:
        for name, _ in inspect.getmembers(view_set, predicate=inspect.ismethod):
            if name.lower() in ['update', 'create', 'destroy', 'list', 'partial_update', 'retrieve']:
                ori_action_dict.setdefault(resource_name, []).append(convert_method_to_action(name.lower()))

    for key in dict_resource_perm_map:
        row = [key, 'N/A', 'N/A', 'N/A', 'N/A']
        row = _change_row(row, 'No', ori_action_dict.get(key, []))
        row = _change_row(row, 'Yes', dict_resource_perm_map.get(key, []))
        result.append(row)

    return sorted(result)


def user_profile(request):
    context = {'has_ldap': hasattr(settings, "LDAP_URI"),
               'resource_permissions_matrix': _get_resource_permissions_matrix(request.user)}
    return render(request, 'user_profile.html', context)


def get_users_and_groups(resource_permission):
    group_popover = OrderedDict()
    inactive_user = {str(user.username) for user in models.User.objects.filter(is_active=False)}
    superusers_set = {str(user.username) for user in models.User.objects.filter(is_superuser=True)}
    try:
        group_resource_permission_list = get_list_or_404(models.GroupResourcePermission,
                                                         resource_permission=resource_permission)
        groups_list = [str(obj.group.name) for obj in group_resource_permission_list]
        for obj in groups_list:
            users_set = {str(user.username) for user in get_user_model().objects.filter(groups__name=obj)}
            users_list = sorted(users_set - inactive_user)
            group_popover.setdefault('@' + obj, users_list)
    except Http404:
        pass
    group_popover.setdefault('@superusers', sorted(superusers_set - inactive_user))
    return group_popover


def _get_arg_value(arg_name):
    """
    Get a possible argument value. Generally, we want to have argument name
    wrapped in braces, but when some form of primary key is expected, that
    would raise internal server error when link is clicked.
    """
    if 'pk' in arg_name:
        return '0'
    return '{%s}' % arg_name


def _get_list_url(url_name, viewset, request):
    return reverse(url_name, request=request, format=None)


def _get_nested_list_url(url_name, viewset, request, urlargs):
    if not hasattr(viewset, 'list'):
        raise NoReverseMatch
    return reverse(
        url_name,
        request=request,
        args=urlargs,
        format=None
    )


def _get_detail_url(url_name, viewset, request, urlargs):
    if not hasattr(viewset, 'retrieve'):
        raise NoReverseMatch
    return reverse(
        url_name[:-5] + '-detail',
        request=request,
        args=urlargs + ['{%s}' % viewset.lookup_field],
        format=None
    )


def get_url_with_resource(request):
    api_root_dict = OrderedDict()
    viewsets = {}
    ret = OrderedDict()
    list_name = router.routes[0].name
    for prefix, viewset, basename in router.registry:
        api_root_dict[prefix] = list_name.format(basename=basename)
        viewsets[prefix] = viewset
    sorted_api_root_dict = OrderedDict(sorted(api_root_dict.items()))
    for key, url_name in sorted_api_root_dict.items():
        name = URL_ARG_RE.sub(r'{\1}', key)
        ret[name] = None
        urlargs = [_get_arg_value(arg[0]) for arg in URL_ARG_RE.findall(key)]
        for getter in [_get_list_url, _get_nested_list_url, _get_detail_url]:
            try:
                if getter == _get_list_url:
                    ret[name] = urldecode(getter(url_name, viewsets[key], request))
                else:
                    ret[name] = urldecode(getter(url_name, viewsets[key], request, urlargs))
                break
            except NoReverseMatch:
                continue
    return ret


def get_api_perms(request):
    """
    Return all API perms for @groups and users.
    Format: {resource: {create/read/update/delete: [users, @groups]}}
    """
    perms = {}
    ret = get_url_with_resource(request)

    for obj in models.ResourcePermission.objects.all():
        name = URL_ARG_RE.sub(r'{\1}', obj.resource.name)
        if name not in ret:
            continue
        url = ret[name]
        if read_permission_for_all() and obj.permission.name == 'read':
            members_list = ['@all']
        else:
            members_list = get_users_and_groups(obj)
        perm = perms.setdefault(name, OrderedDict())
        perm.setdefault(obj.permission.name, members_list)
        perm.setdefault('url', url)
        perm.setdefault('api_url', getattr(obj.resource, 'api_url', ''))
    # sort groups and users
    for resource in perms:
        for perm in perms[resource]:
            if not isinstance(perms[resource][perm], set):
                # sort only lists with groups and users, skip 'url'
                continue
            perms[resource][perm] = sorted(perms[resource][perm])
    result = OrderedDict(sorted(perms.items()))
    return result


def api_perms(request):
    """
    Render API resource perms.
    """
    context = {
        'api_perms': get_api_perms(request),
    }
    return render(request, 'api_perms.html', context)


def refresh_ldap_groups(request):
    user = request.user
    backends.update_user_from_ldap(user)
    if request.is_ajax():
        return HttpResponse(json.dumps({
            'username': user.username,
            'fullname': user.full_name,
            'e-mail': user.email,
            'is_superuser': user.is_superuser,
            'is_staff': user.is_staff,
            'groups': [g.name for g in user.groups.all()],
            'permissions': list(user.get_all_permissions()),
        }), content_type="application/json")
    return redirect("user/profile")


class TokenViewSet(StrictQueryParamMixin, viewsets.ViewSet):
    """
    ## REST API Auth ##

    We use `TokenAuthentication` for API Authentication.

    Unauthenticated user will not be able to access to APIs.

    **WARNING:** Please do not share your token with anyone else.

    **NOTE:** It's highly recommended to make sure your API is only available over `https` when using `TokenAuthentication`.

    We use DjangoModelPermissions for RESTful API permissions.

    Authorization will only be granted if the user is authenticated
    and has the relevant model permissions assigned.

    * __POST__ requests require the user to have the `add` permission on the model.
    * __PUT__ and __PATCH__ requests require the user to have the `change` permission on the model.
    * __DELETE__ requests require the user to have the `delete` permission on the model.

    ### Using Token

    * obtain token

            curl --negotiate -u : -H "Accept: application/json"  $URL:token-obtain$

        you will get a `Response` like:

            {"token": "00bf04e8187f6e6d54f510515e8bde88e5bb7904"}

    * then you should add one HTTP HEADER with this token in this format with every request need authentication:

            Authorization: Token 00bf04e8187f6e6d54f510515e8bde88e5bb790

        for curl, it should be:

            curl -H 'Authorization: Token 00bf04e8187f6e6d54f510515e8bde88e5bb790' $URL:home$%(API_PATH)s/

    * in case you want refresh your token, you can do it with:

            curl --negotiate -u : -H "Accept: application/json"  $URL:token-refresh$

        you will get a `Response` with refreshed token:

            {"token": "00bf04e8187f6e6d54f510515e8bde88e5bb7904"}

    """

    permission_classes = [IsAuthenticated]

    # Dummy list view for showing ViewSet docstring.
    def list(self, request):
        return Response()

    @list_route(methods=['get', 'post'])
    def obtain(self, request):
        """
        ### Obtain Token

        __URL__: $LINK:token-obtain$

        __EXAMPLE__:

        Run:

            curl --negotiate -u : -H "Accept: application/json"  $URL:token-obtain$

        you will get a `Response` like:

            {"token": "00bf04e8187f6e6d54f510515e8bde88e5bb7904"}
        """

        if request.user.is_authenticated:
            if request.user.is_active:
                token, created = Token.objects.get_or_create(user=request.user)
                return Response({'token': token.key})
            else:
                reason = {"Obtain Token Error": "You're not an active user."}
                return Response(reason, status=status.HTTP_401_UNAUTHORIZED)
        else:
            reason = {"Obtain Token Error": "Failed to authenticate."}
            return Response(reason, status=status.HTTP_401_UNAUTHORIZED)

    @list_route(methods=['get', 'put'])
    def refresh(self, request):
        """
        ### Refresh Token

        __URL__: $LINK:token-refresh$

        __EXAMPLE__:

        Run:

            curl --negotiate -u : -H "Accept: application/json"  $URL:token-refresh$
            # or
            curl --negotiate -u : -X PUT -H "Accept: application/json"  $URL:token-refresh$

        you will get a `Response` with refreshed token:

            {"token": "00bf04e8187f6e6d54f510515e8bde88e5bb7904"}
        """
        if request.user.is_authenticated:
            if request.user.is_active:
                try:
                    token = Token.objects.get(user=request.user)
                    token.delete()
                except Token.DoesNotExist:
                    reason = {"Refresh Token Error": "You have not got a token yet, please try obtain first."}
                    return Response(reason, status=status.HTTP_400_BAD_REQUEST)
                token = Token.objects.create(user=request.user)
                return Response({'token': token.key})
            else:
                reason = {"Refresh Token Error": "You're not an active user."}
                return Response(reason, status=401)
        else:
            reason = {"Refresh Token Error": "Authenticate Failed."}
            return Response(reason, status=401)


class PermissionViewSet(StrictQueryParamMixin,
                        mixins.ListModelMixin,
                        viewsets.GenericViewSet):
    """
    ##Overview##

    This page shows the usage of the **Permission API**, please see the
    following for more details.

    """
    permission_classes = (APIPermission,)

    doc_list = """
        ### LIST

        __Method__:
        `GET`

        __Query Params__:

        %(FILTERS)s

        __URL__: $LINK:permission-list$

        __Response__: a paged list of following objects

        %(SERIALIZER)s

        __Example__:

            curl -H "Accept: application/json"  -X GET $URL:permission-list$
            # output
            {
                "count": 150,
                "next": "$URL:permission-list$?page=2",
                "previous": null,
                "results": [
                    {
                        "codename": "add_logentry",
                        "app_label": "admin",
                        "model": "logentry"
                    },
                    ...
                ]
            }

        With query params:

            curl -H "Accept: application/json"  -G $URL:permission-list$ --data-urlencode "codename=add_logentry"
            # output
            {
                "count": 1,
                "next": null,
                "previous": null,
                "results": [
                    {
                        "codename": "add_logentry",
                        "app_label": "admin",
                        "model": "logentry"
                    }
                ]
            }

    """

    queryset = Permission.objects.all().order_by("id")
    serializer_class = serializers.PermissionSerializer
    filter_class = filters.PermissionFilter


class GroupViewSet(NotificationMixin,
                   ChangeSetUpdateModelMixin,
                   StrictQueryParamMixin,
                   mixins.ListModelMixin,
                   mixins.RetrieveModelMixin,
                   viewsets.GenericViewSet):
    """
    ##Overview##

    This page shows the usage of the **Group API**, please see the
    following for more details.
    """
    doc_list = """
        ### LIST

        __Method__:
        `GET`

        __URL__: $LINK:group-list$

        __Query Params__:

        %(FILTERS)s

        __Response__: a paged list of following objects

        %(SERIALIZER)s

        __Example__:

            {
                "count": 2,
                "next": null,
                "previous": null,
                "results": [
                    {
                        "url": "$URL:group-detail:1$",
                        "name": "group_add_group",
                        "permissions": [
                            {
                                "codename": "add_group",
                                "app_label": "auth",
                                "model": "group"
                            }
                        ]
                    },
                    {
                        "url": "$URL:group-detail:2$",
                        "name": "group_change_change",
                        "permissions": [
                            {
                                "codename": "change_change",
                                "app_label": "changeset",
                                "model": "change"
                            }
                        ]
                    }
                ]
            }

    """

    doc_retrieve = """
        ### RETRIEVE

        __Method__:
        `GET`

        __URL__: $LINK:group-detail:instance_pk$

        __Response__:

        %(SERIALIZER)s

        __Example__:

            # curl command
            curl -H "Content-Type: application/json" $URL:group-detail:1$
            # output
            {
              "url": "$URL:group-detail:1$,
              "name": "group_add_group",
              "permissions": [
                  {
                      "codename": "add_group",
                      "app_label": "auth",
                      "model": "group"
                  }
              ]
            }
    """

    doc_update = """
        ### UPDATE

        __Method__:

        `PUT`: to update name and permissions

        `PATCH`: to update name or permissions

        __URL__: $LINK:group-detail:instance_pk$

        __Response__:

        %(SERIALIZER)s

        __Example__:

        PUT:

            # cat put_data.json
            {
                "name": "new_group",
                "permissions": [
                    {
                        "codename": "change_change",
                        "app_label": "changeset",
                        "model": "change"
                    },
                    {
                        "codename": "add_group",
                        "app_label": "auth",
                        "model": "group"
                    }
                ]
            }
            # curl command
            curl -H "Content-Type: application/json" \\
                 -X PUT \\
                 --data @put_data.json  \\
                $URL:group-detail:1$
            # output
            {
              "url": "$URL:group-detail:1$",
              "name": "new_group",
              "permissions": [
                  {
                      "codename": "change_change",
                      "app_label": "changeset",
                      "model": "change"
                  },
                  {
                      "codename": "add_group",
                      "app_label": "auth",
                      "model": "group"
                  }
              ]
            }

        PATCH:

            # cat patch_data.json
            {
                "permissions": [
                    {
                        "codename": "change_change",
                        "app_label": "changeset",
                        "model": "change"
                    },
                    {
                        "codename": "add_group",
                        "app_label": "auth",
                        "model": "group"
                    }
                ]
            }
            # curl command
            curl -H "Content-Type: application/json" \\
                 -X PATCH \\
                 --data @patch_data.json  \\
                $URL:group-detail:1$
            # output
            {
              "url": "$URL:group-detail:1$",
              "name": "group_add_group",
              "permissions": [
                  {
                      "codename": "change_change",
                      "app_label": "changeset",
                      "model": "change"
                  },
                  {
                      "codename": "add_group",
                      "app_label": "auth",
                      "model": "group"
                  }
              ]
            }

    """

    queryset = Group.objects.all().order_by('id')
    serializer_class = serializers.GroupSerializer
    filter_class = filters.GroupFilter
    permission_classes = (APIPermission,)
    Group.export = group_obj_export


class CurrentUserViewSet(mixins.ListModelMixin,
                         viewsets.GenericViewSet):
    """
    This end-point provides programmatic access to information about current
    user.
    """
    queryset = get_user_model().objects.none()

    def _get_resource_permissions(self, user):
        serializer = serializers.ResourcePermissionSerializer(get_resource_permission_set(user), many=True)
        return serializer.data

    def list(self, request):
        """
        Get information about current user.

        __Method__: `GET`

        __URL__: $LINK:currentuser-list$

        __Response__:

            {
                "username": string,
                "fullname": string,
                "e-mail": string,
                "is_superuser": bool,
                "is_staff": bool,
                "groups": [string],
                "permissions": [string],
                "resource_permissions": [
                    {"resource": string, "permission": string},
                     ...
                ]
            }
        """
        user = request.user
        if not user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED,
                            data={'detail': 'Access denied to unauthorized users.'})
        return Response(data={
            'username': user.username,
            'fullname': user.full_name,
            'e-mail': user.email,
            'is_superuser': user.is_superuser,
            'is_staff': user.is_staff,
            'groups': [g.name for g in user.groups.all()],
            'permissions': sorted(list(user.get_all_permissions())),
            'resource_permissions': self._get_resource_permissions(user)
        })


class ResourcePermissionViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """
    This end-point provides resource permissions information.
    """
    queryset = models.ResourcePermission.objects.all()
    serializer_class = serializers.ResourcePermissionSerializer
    permission_classes = (APIPermission,)
    filter_class = filters.ResourcePermissionFilter

    doc_list = """
        Get information about resource permissions.

        __Method__: `GET`

        __URL__: $LINK:resourcepermissions-list$

        __Query params__:

        %(FILTERS)s

        __Response__:

             # paged lists
            {
                "count": int,
                "next": url,
                "previous": url,
                "results": [
                    {
                        "resource": string,
                        "permission": string
                    }
                    ...
                ]
            }

    """


class GroupResourcePermissionViewSet(common_viewsets.PDCModelViewSet):
    """
    This end-point provides group resource permissions.
    """
    queryset = models.GroupResourcePermission.objects.all()
    serializer_class = serializers.GroupResourcePermissionSerializer
    filter_class = filters.GroupResourcePermissionFilter

    doc_list = """
        Get information about group resource permissions.

        __Method__: `GET`

        __URL__: $LINK:groupresourcepermissions-list$

        __Query params__:

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
                        "group": string,
                        "resource": string,
                        "permission": string
                    },
                    ...
                ]
            }


    """

    doc_create = """
        __Method__: POST

        __URL__: $LINK:groupresourcepermissions-list$

         __Data__:

            {
                "group": string,
                "resource": string,
                "permission": string
            }

        __Response__:

            {
                "id": int,
                "group": string,
                "resource": string,
                "permission": string
            }
    """

    doc_retrieve = """
        __Method__: GET

        __URL__: $LINK:groupresourcepermissions-detail:instance_pk$

        __Response__:

            {
                "id": int,
                "group": string,
                "resource": string,
                "permission": string
            }
    """

    doc_update = """
        __Method__: PUT, PATCH

        __URL__: $LINK:groupresourcepermissions-detail:instance_pk$

        __Data__:

            {
                "group": string,
                "resource": string,
                "permission": string
            }

        __Response__:

            {
                "id": int,
                "group": string,
                "resource": string,
                "permission": string
            }
    """

    doc_destroy = """
        __Method__: DELETE

        __URL__: $LINK:groupresourcepermissions-detail:instance_pk$

        __Response__:

        On success, HTTP status code is 204 and the response has no content.
    """


class ResourceApiUrlViewSet(common_viewsets.PDCModelViewSet):
    """
    This end-point provides URLs with documentation for the REST API.
    """
    queryset = ResourceApiUrl.objects.all()
    serializer_class = serializers.ResourceApiUrlSerializer
    filter_class = filters.ResourceApiUrlFilter

    doc_list = """
        Get information about API documentation URLs.

        __Method__: `GET`

        __URL__: $LINK:resourceapiurls-list$

        __Query params__:

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
                        "resource": string,
                        "url": string
                    },
                    ...
                ]
            }
    """

    doc_create = """
        __Method__: POST

        __URL__: $LINK:resourceapiurls-list$

         __Data__:

            {
                "resource": string,
                "url": string
            }

        __Response__:

            {
                "id": int,
                "resource": string,
                "url": string
            }
    """

    doc_retrieve = """
        __Method__: GET

        __URL__: $LINK:resourceapiurls-detail:instance_pk$

        __Response__:

            {
                "id": int,
                "resource": string,
                "url": string
            }
    """

    doc_update = """
        __Method__: PUT, PATCH

        __URL__: $LINK:resourceapiurls-detail:instance_pk$

        __Data__:

            {
                "resource": string,
                "url": string
            }

        __Response__:

            {
                "id": int,
                "resource": string,
                "url": string
            }
    """

    doc_destroy = """
        __Method__: DELETE

        __URL__: $LINK:resourceapiurls-detail:instance_pk$

        __Response__:

        On success, HTTP status code is 204 and the response has no content.
    """
