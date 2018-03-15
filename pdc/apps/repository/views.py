#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
import json

from rest_framework import mixins, viewsets, status
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from . import models
from . import serializers
from . import filters
from pdc.apps.auth.permissions import APIPermission
from pdc.apps.common.constants import PUT_OPTIONAL_PARAM_WARNING
from pdc.apps.common.viewsets import (StrictQueryParamMixin,
                                      PDCModelViewSet)
from pdc.apps.release.models import Release
from pdc.apps.common import hacks
from pdc.apps.common.serializers import StrictSerializerMixin


class RepoViewSet(PDCModelViewSet):
    """
    An API endpoint providing access to content delivery repositories.
    """
    queryset = models.Repo.objects.all().select_related().order_by('id')
    serializer_class = serializers.RepoSerializer
    filter_class = filters.RepoFilter
    docstring_macros = PUT_OPTIONAL_PARAM_WARNING

    doc_create = """
        __Method__: `POST`

        __URL__: $LINK:contentdeliveryrepos-list$

        __Data__:

        %(WRITABLE_SERIALIZER)s

         * *content_category*: $LINK:contentdeliverycontentcategory-list$
         * *content_format*: $LINK:contentdeliverycontentformat-list$
         * *repo_family*: $LINK:contentdeliveryrepofamily-list$
         * *service*: $LINK:contentdeliveryservice-list$

        __Response__: Same as input data.
    """

    doc_retrieve = """
        __Method__: `GET`

        __URL__: $LINK:contentdeliveryrepos-detail:id$

        __Response__:

        %(SERIALIZER)s
    """

    doc_list = """
        __Method__: `GET`

        __URL__: $LINK:contentdeliveryrepos-list$

        __Query params__:

        %(FILTERS)s

        __Response__:

        %(SERIALIZER)s
    """

    doc_update = """
        %(PUT_OPTIONAL_PARAM_WARNING)s

        __Method__: `PUT`, `PATCH`

        __URL__: $LINK:contentdeliveryrepos-detail:id$

        __Data__:

        %(WRITABLE_SERIALIZER)s

        __Response__:

        %(SERIALIZER)s
    """

    doc_destroy = """
        __Method__: `DELETE`

        __URL__: $LINK:contentdeliveryrepos-detail:id$
    """


class RepoCloneViewSet(StrictQueryParamMixin, viewsets.GenericViewSet):
    """
    Please access this endpoint by $LINK:cdreposclone-list$.
    Endpoint $LINK:repoclone-list$ is deprecated.
    """
    queryset = models.Repo.objects.none()   # Required for permissions
    permission_classes = (APIPermission,)

    def create(self, request):
        """
        Clone all content delivery repositories from one release under another release.

        The call is atomic, i.e. either all content delivery repositories are cloned or nothing
        is done.

        If the source and target releases do not have the same variants, the
        cloning will silently ignore content delivery repositories with Variant.Arch that is
        present in source release but not in target release. It is not a
        problem if the target release has additional variants.

        __Method__: `POST`

        __URL__: $LINK:cdreposclone-list$


        __Data__:

            {
                "release_id_from":          string,
                "release_id_to":            string
                "include_service":          [string],   # optional
                "include_repo_family":      [string],   # optional
                "include_content_format":   [string],   # optional
                "include_content_category": [string],   # optional
                "include_shadow":           bool,       # optional
                "include_product_id":       int         # optional
            }

        The `include_*` keys are used to filter which releases should be
        cloned. If any key is omitted, all values for that attribute will be
        cloned.

        __Response__:
        The call returns a list of content delivery repositories created under target release.

            [
              {
                "shadow":           bool,
                "release_id":       string,
                "variant_uid":      string,
                "arch":             string,
                "service":          string,
                "repo_family":      string,
                "content_format":   string,
                "content_category": string,
                "name":             string,
                "product_id":       int
              },
              ...
            ]
        """
        data = request.data
        keys = set(['release_id_from', 'release_id_to'])
        arg_filter_map = {'include_service': ('service__name__in', hacks.as_list),
                          'include_repo_family': ('repo_family__name__in', hacks.as_list),
                          'include_content_format': ('content_format__name__in', hacks.as_list),
                          'include_content_category': ('content_category__name__in', hacks.as_list),
                          'include_shadow': ('shadow', hacks.convert_str_to_bool),
                          'include_product_id': ('product_id', hacks.convert_str_to_int)}
        allowed_keys = list(keys) + arg_filter_map.keys()

        missing_keys = keys - set(data.keys())
        if missing_keys:
            errors = dict([(k, ['This field is required.']) for k in missing_keys])
            return Response(status=status.HTTP_400_BAD_REQUEST, data=errors)
        extra_keys = set(data.keys()) - set(allowed_keys)
        StrictSerializerMixin.maybe_raise_error(extra_keys)

        get_object_or_404(Release, release_id=data['release_id_from'])
        target_release = get_object_or_404(Release, release_id=data['release_id_to'])

        kwargs = {
            'variant_arch__variant__release__release_id': data['release_id_from']
        }

        for arg, (filter, transform) in arg_filter_map.iteritems():
            arg_data = request.data.get(arg)
            if arg_data:
                kwargs[filter] = transform(arg_data, name=arg)

        repos = models.Repo.objects.filter(**kwargs)

        # Skip repos from nonexisting trees.
        repos_in_target_release = [repo for repo in repos if repo.tree in target_release.trees]

        if not repos or not repos_in_target_release:
            return Response(status=status.HTTP_400_BAD_REQUEST,
                            data={'detail': 'No repos to clone.'})

        serializer = serializers.RepoSerializer(repos_in_target_release, many=True)
        copy = serializer.data
        for repo in copy:
            # The serializer will reject read-only fields, so we need to drop the id.
            del repo['id']
            repo['release_id'] = target_release.release_id
        new_repos = serializers.RepoSerializer(data=copy, many=True)
        if not new_repos.is_valid():
            return Response(status=status.HTTP_400_BAD_REQUEST,
                            data={'detail': dict((repo['name'], err)
                                                 for repo, err in zip(copy, new_repos.errors)
                                                 if err)})
        for raw_repo, repo_obj in zip(copy, new_repos.save()):
            request.changeset.add('Repo', repo_obj.pk,
                                  'null', json.dumps(raw_repo))

        return Response(status=status.HTTP_200_OK, data=new_repos.data)


class RepoFamilyViewSet(StrictQueryParamMixin,
                        mixins.ListModelMixin,
                        viewsets.GenericViewSet):
    """
    ##Overview##

    This page shows the usage of the **ContentDeliveryRepoFamily API**, please see the
    following for more details.

    ##Test tools##

    You can use ``curl`` in terminal, with -X _method_ (GET|POST|PUT|PATCH|DELETE),
    -d _data_ (a json string). or GUI plugins for
    browsers, such as ``RESTClient``, ``RESTConsole``.
    """
    queryset = models.RepoFamily.objects.all().order_by('id')
    serializer_class = serializers.RepoFamilySerializer
    filter_class = filters.RepoFamilyFilter
    permission_classes = (APIPermission,)

    doc_list = """
        __Method__: `GET`

        __URL__: $LINK:contentdeliveryrepofamily-list$

        __Query params__:

        %(FILTERS)s

        __Response__: a paged list of following objects

        %(SERIALIZER)s

        __Example__:

            $ curl  "$URL:contentdeliveryrepofamily-list$
            {
                "count": 3,
                "next": null,
                "previous": null,
                "results": [
                    {
                        "name": "dist",
                        "description": "Production content delivery repositories"
                    },
                    {
                        "name": "beta",
                        "description": "Beta (pre-production) content delivery repositories"
                    },
                    {
                        "name": "htb",
                        "description": "Content delivery repositories for High Touch Beta (HTB) customers"
                    }
                ]
            }
    """


class ContentCategoryViewSet(StrictQueryParamMixin,
                             mixins.ListModelMixin,
                             viewsets.GenericViewSet):
    """
    API endpoint that allows content_category to be viewed.
    """
    serializer_class = serializers.ContentCategorySerializer
    queryset = models.ContentCategory.objects.all().order_by('id')
    permission_classes = (APIPermission,)

    doc_list = """
        __Method__: GET

        __URL__: $LINK:contentdeliverycontentcategory-list$

        __Response__:

        %(SERIALIZER)s
    """


class ContentFormatViewSet(StrictQueryParamMixin,
                           mixins.ListModelMixin,
                           viewsets.GenericViewSet):
    """
    API endpoint that allows content_format to be viewed.
    """
    serializer_class = serializers.ContentFormatSerializer
    queryset = models.ContentFormat.objects.all().order_by('id')
    permission_classes = (APIPermission,)

    doc_list = """
        __Method__: GET

        __URL__: $LINK:contentdeliverycontentformat-list$

        __Response__:

        %(SERIALIZER)s
    """


class ServiceViewSet(StrictQueryParamMixin,
                     mixins.ListModelMixin,
                     viewsets.GenericViewSet):
    """
    API endpoint that allows service to be viewed.
    """
    serializer_class = serializers.ServiceSerializer
    queryset = models.Service.objects.all().order_by('id')
    permission_classes = (APIPermission,)

    doc_list = """
        __Method__: GET

        __URL__: $LINK:contentdeliveryservice-list$

        __Response__:

        %(SERIALIZER)s
    """


class PushTargetViewSet(PDCModelViewSet):
    """
    Push targets for products, product versions, releases and release variants.
    """

    queryset = models.PushTarget.objects.all()
    serializer_class = serializers.PushTargetSerializer
    filter_class = filters.PushTargetFilter
    permission_classes = (APIPermission,)

    doc_create = """
        __Method__: POST

        __URL__: $LINK:pushtarget-list$

        __Data__:

        %(WRITABLE_SERIALIZER)s

        __Response__:

        %(SERIALIZER)s
    """

    doc_retrieve = """
        __Method__: GET

        __URL__: $LINK:pushtarget-detail:instance_pk$

        __Response__:

        %(SERIALIZER)s
    """

    doc_list = """
        __Method__: GET

        __URL__: $LINK:pushtarget-list$

        __Query params__:

        %(FILTERS)s

        __Response__: a paged list of following objects

        %(SERIALIZER)s
    """

    doc_update = """
        __Method__: PUT, PATCH

        __URL__: $LINK:pushtarget-detail:instance_pk$

        __Data__:

        %(WRITABLE_SERIALIZER)s

        __Response__:

        %(SERIALIZER)s
    """

    doc_destroy = """
        __Method__: `DELETE`

        __URL__: $LINK:pushtarget-detail:instance_pk$

        __Response__:

        On success, HTTP status code is 204 and the response has no content.
    """


class MultiDestinationViewSet(PDCModelViewSet):
    """
    Multi-destinations (multi-product) for mapping global component files
    from an origin repository to a destination repository.
    """

    queryset = models.MultiDestination.objects.all().select_related()
    serializer_class = serializers.MultiDestinationSerializer
    filter_class = filters.MultiDestinationFilter
    permission_classes = (APIPermission,)

    doc_create = """
        __Method__: POST

        __URL__: $LINK:multidestination-list$

        __Data__:

        %(WRITABLE_SERIALIZER)s

        __Response__:

        %(SERIALIZER)s
    """

    doc_retrieve = """
        __Method__: GET

        __URL__: $LINK:multidestination-detail:instance_pk$

        __Response__:

        %(SERIALIZER)s
    """

    doc_list = """
        __Method__: GET

        __URL__: $LINK:multidestination-list$

        __Query params__:

        %(FILTERS)s

        __Response__: a paged list of following objects

        %(SERIALIZER)s
    """

    doc_update = """
        __Method__: PUT, PATCH

        __URL__: $LINK:multidestination-detail:instance_pk$

        __Data__:

        %(WRITABLE_SERIALIZER)s

        __Response__:

        %(SERIALIZER)s
    """

    doc_destroy = """
        __Method__: `DELETE`

        __URL__: $LINK:multidestination-detail:instance_pk$

        __Response__:

        On success, HTTP status code is 204 and the response has no content.
    """
