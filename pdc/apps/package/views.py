#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
from rest_framework import viewsets, mixins

from contrib.bulk_operations import bulk_operations
from pdc.apps.common import viewsets as pdc_viewsets
from pdc.apps.common.constants import PUT_OPTIONAL_PARAM_WARNING
from pdc.apps.common.viewsets import PDCModelViewSet
from pdc.apps.auth.permissions import APIPermission
from . import models
from . import serializers
from . import filters


class RPMViewSet(pdc_viewsets.StrictQueryParamMixin,
                 pdc_viewsets.NotificationMixin,
                 pdc_viewsets.ChangeSetCreateModelMixin,
                 pdc_viewsets.ChangeSetUpdateModelMixin,
                 mixins.RetrieveModelMixin,
                 mixins.ListModelMixin,
                 viewsets.GenericViewSet):
    """
    API endpoint that allows RPMs to be viewed.
    """
    queryset = models.RPM.objects.all().order_by("id")
    serializer_class = serializers.RPMSerializer
    filter_class = filters.RPMFilter
    permission_classes = (APIPermission,)
    docstring_macros = PUT_OPTIONAL_PARAM_WARNING

    doc_list = """
        All the dependency filters use the same data format.

        The simpler option is just name of the dependency. In that case it will
        filter RPMs that depend on that given name.

        The other option is an expression `NAME OP VERSION`. This will filter
        all RPMs that have a dependency on `NAME` such that adding this
        constraint will not make the package dependencies inconsistent.

        For example filtering by `python=2.7.0` would include packages with
        dependency on `python=2.7.0`, `python>=2.6.0`, `python<3.0.0` and
        `python`, but exclude `python=2.6.0` because it's not possible to use
        python-2.6.0 package if the dependency filter specifies that the
        package version should be greater or equal 2.6.0.

        Another example: Dependency `python<3.0.0` satisfies filter
        `python>=2.7.0` because it's possible to pick any version of python
        between 2.7.0 (inclusive) up to 3.0.0 (exclusive) - e.g. python-2.7.0.

        If dependency doesn't include version, it is satisfied by any filter.

        Only single filter for each dependency type is allowed.
    """

    doc_create = """
        __Method__:
        POST

        __URL__: $LINK:rpms-list$

        __Data__:

        %(WRITABLE_SERIALIZER)s

        The `srpm_nevra` field should be empty if and only if `arch` is `src`.
        If `filename` is not specified, it will default to a name created from
        *NEVRA*.

        The format of each dependency is either just name of the package that
        the new RPM depends on, or it can have the format `NAME OP VERSION`,
        where `OP` can be any comparison operator. Recognized dependency types
        are *provides*, *requires*, *obsoletes*, *conflicts*, *suggests* and
        *recommends*

        __Response__:

        %(SERIALIZER)s
    """

    doc_retrieve = """
        __Method__:
        GET

        __URL__: $LINK:rpms-detail:instance_pk$

        __Response__:

        %(SERIALIZER)s
    """

    doc_update = """
        %(PUT_OPTIONAL_PARAM_WARNING)s

        __Method__: `PUT`, `PATCH`

        __URL__: $LINK:rpms-detail:instance_pk$

        __Data__:

        %(WRITABLE_SERIALIZER)s

        If the `dependencies` key is omitted on `PATCH` request, they will not
        be changed. On `PUT` request, they will be completely removed. When a
        value is specified, it completely replaces existing dependencies.

        The format of the dependencies themselves is same as for create.

        __Response__:

        %(SERIALIZER)s
    """


class ImageViewSet(pdc_viewsets.StrictQueryParamMixin,
                   mixins.ListModelMixin,
                   viewsets.GenericViewSet):
    """
    List and query images.
    """
    queryset = models.Image.objects.all().order_by('id')
    serializer_class = serializers.ImageSerializer
    filter_class = filters.ImageFilter
    permission_classes = (APIPermission,)

    doc_list = """
        __Method__: GET

        __URL__: $LINK:image-list$

        __Query params__:

        %(FILTERS)s

        The `compose` filter allows filtering images connected to a particular
        compose. The value should be compose ID.

        If the same filter is specified multiple times, it will do a OR query.

        __Response__: a paged list of following objects

        %(SERIALIZER)s
    """


class BuildImageViewSet(pdc_viewsets.PDCModelViewSet):
    """
    ViewSet for  BuildImage.
    """
    queryset = models.BuildImage.objects.all().order_by('id')
    serializer_class = serializers.BuildImageSerializer
    filter_class = filters.BuildImageFilter

    doc_create = """
        If the RPM filename is omitted, a default value will be constructed
        based on name, version, release and arch.
    """

    doc_list = """
        The value of `component_name` should be either SRPM name or release
        component name if release component to srpm mapping exists.
    """

    doc_update = """
        __NOTE:__ when updating `image_format`, its value must be an existed one, otherwise it will
        cause HTTP 400 BAD REQUEST error.
    """


class BuildImageRTTTestsViewSet(pdc_viewsets.StrictQueryParamMixin,
                                pdc_viewsets.NotificationMixin,
                                pdc_viewsets.ChangeSetUpdateModelMixin,
                                pdc_viewsets.MultiLookupFieldMixin,
                                mixins.RetrieveModelMixin,
                                mixins.ListModelMixin,
                                viewsets.GenericViewSet):
    """
    ViewSet for  BuildImage RTT Tests.
    """
    queryset = models.BuildImage.objects.all().order_by('id')
    serializer_class = serializers.BuildImageRTTTestsSerializer
    filter_class = filters.BuildImageRTTTestsFilter
    permission_classes = (APIPermission,)
    lookup_fields = (('image_id', r'[^/]+'),
                     ('image_format__name', r'[^/]+'))

    doc_list = """
        __Method__: GET

        __URL__: $LINK:buildimagertttests-list$

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
                    "build_nvr":    string,
                    "format":       string,
                    "id":           int,
                    "test_result":  string
                },
                ...
              ]
            }
    """

    doc_retrieve = """
        __Method__:
        GET

        __URL__: $LINK:buildimagertttests-detail:build_nvr}/{image_format$

        __Response__:

            {
                "build_nvr":    string,
                "format":       string,
                "id":           int,
                "test_result":  string
            }
    """

    def update(self, request, *args, **kwargs):
        # This method is used by bulk update and partial update, but should not
        # be called directly.
        if not kwargs.get('partial', False):
            return self.http_method_not_allowed(request, *args, **kwargs)

        if not request.data:
            return pdc_viewsets.NoEmptyPatchMixin.make_response()
        return super(BuildImageRTTTestsViewSet, self).update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        """
        Only `test_result` fields can be modified by this call.
        Trying to change anything else will result in 400 BAD REQUEST response.

        __Method__: PATCH

        __URL__: $LINK:buildimagertttests-detail:build_nvr}/{image_format$

        __Data__:

            {
                "test_result": string
            }

        __Response__:

            {
                "build_nvr":    string,
                "format":       string,
                "id":           int,
                "test_result":  string
            }
        """
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    def bulk_update(self, *args, **kwargs):
        """
        It is possible to perform bulk partial update on 'test_result' with `PATCH`
        method. The request body should contain an object, where keys are identifiers
        of objects to be modified and their values use the same format as normal patch.
        """
        return bulk_operations.bulk_update_impl(self, *args, **kwargs)


class ReleasedFilesViewSet(PDCModelViewSet):
    """
    #**Warning: This is an experimental API**#
    This API endpoint is about released files.
    """
    queryset = models.ReleasedFiles.objects.all().order_by('id')
    serializer_class = serializers.ReleasedFilesSerializer
    filter_class = filters.ReleasedFilesFilter
    permission_classes = (APIPermission,)
    docstring_macros = PUT_OPTIONAL_PARAM_WARNING

    doc_list = """
        __Method__: GET

        __URL__: $LINK:releasedfiles-list$

        __Query params__:

        %(FILTERS)s

        __Response__: a paged list of following objects

        Return with *build*, *file*, *package* the *build* is *rpm.srpm_name-rpm.version-rpm.arch*,
        the *file* is *rpm.filename*, the *package* is *rpm.srpm_name*.

        Please visit $LINK:contentdeliverycontentformat-list$ to get the endpoint's name of file_primary_key

        %(SERIALIZER)s
    """

    doc_create = """
        __Method__: POST

        __URL__: $LINK:releasedfiles-list$

        __Data__:

        %(WRITABLE_SERIALIZER)s

        * *repo*: $LINK:contentdeliveryrepos-list$

        Currently release-files just can insert data with *repo.content_format* rpm.

        __Response__:

        Return with *build*, *file*, *package* the *build* is *rpm.srpm_name-rpm.version-rpm.arch*,
        the *file* is *rpm.filename*, the *package* is *rpm.srpm_name*.

        %(SERIALIZER)s
    """

    doc_retrieve = """
        __Method__: GET

        __URL__: $LINK:releasedfiles-detail:instance_pk$

        __Response__:

        Return with *build*, *file*, *package* the *build* is *rpm.srpm_name-rpm.version-rpm.arch*,
        the *file* is *rpm.filename*, the *package* is *rpm.srpm_name*.

        %(SERIALIZER)s
    """

    doc_update = """
        %(PUT_OPTIONAL_PARAM_WARNING)s

        __Method__: `PUT`, `PATCH`

        __URL__: $LINK:releasedfiles-detail:instance_pk$

        __Data__:

        %(WRITABLE_SERIALIZER)s

        * *repo*: $LINK:contentdeliveryrepos-list$

        Currently pdc just can insert data with *repo.content_format* rpm.

        __Response__:

        Return with *build*, *file*, *package* the *build* is *rpm.srpm_name-rpm.version-rpm.arch*,
        the *file* is *rpm.filename*, the *package* is *rpm.srpm_name*.

        %(SERIALIZER)s
    """

    doc_destroy = """
        __Method__: DELETE

        __URL__: $LINK:releasedfiles-detail:instance_pk$

        __Response__:

        On success, HTTP status code is 204 and the response has no content

        __Example__:

            curl -X DELETE -H "Content-Type: application/json" $URL:releasedfiles-detail:1$
    """
