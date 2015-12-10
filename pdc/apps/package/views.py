#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
from rest_framework import viewsets, mixins

from contrib.bulk_operations import bulk_operations
from pdc.apps.common import viewsets as pdc_viewsets
from . import models
from . import serializers
from . import filters


class RPMViewSet(pdc_viewsets.StrictQueryParamMixin,
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

    def list(self, *args, **kwargs):
        """
        __Method__: GET

        __URL__: $LINK:rpms-list$

        __Query params__:

        %(FILTERS)s

        If the `has_no_deps` filter is used, the output will only contain RPMs
        which have some or do not have any dependencies.

        All the dependency filters use the same data format.

        The simpler option is just name of the dependency. In that case it will
        filter RPMs that depend on that given name.

        The other option is an expression `NAME OP VERSION`. This will filter
        all RPMs that have a dependency on `NAME` such that adding this
        constraint will not make the package dependencies inconsistent.

        For example filtering by `python=2.7.0` would include packages with
        dependency on `python=2.7.0`, `python>=2.6.0`, `python<3.0.0`, but
        exclude `python=2.6.0`. Filtering by `python<3.0.0` would include
        packages with `python>2.7.0`, `python=2.6.0`, `python<3.3.0`, but
        exclude `python>3.1.0` or `python>3.0.0 && python <3.3.0`.

        Only single filter for each dependency type is allowed.

        __Response__: a paged list of following objects

        %(SERIALIZER)s
        """
        return super(RPMViewSet, self).list(*args, **kwargs)

    def create(self, request, *args, **kwargs):
        """
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
        return super(RPMViewSet, self).create(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        """
        __Method__:
        GET

        __URL__: $LINK:rpms-detail:instance_pk$

        __Response__:

        %(SERIALIZER)s
        """
        return super(RPMViewSet, self).retrieve(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        """
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
        return super(RPMViewSet, self).update(request, *args, **kwargs)


class ImageViewSet(pdc_viewsets.StrictQueryParamMixin,
                   mixins.ListModelMixin,
                   viewsets.GenericViewSet):
    """
    List and query images.
    """
    queryset = models.Image.objects.all().order_by('id')
    serializer_class = serializers.ImageSerializer
    filter_class = filters.ImageFilter

    def list(self, request):
        """
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
        return super(ImageViewSet, self).list(request)


class BuildImageViewSet(pdc_viewsets.PDCModelViewSet):
    """
    ViewSet for  BuildImage.
    """
    queryset = models.BuildImage.objects.all().order_by('id')
    serializer_class = serializers.BuildImageSerializer
    filter_class = filters.BuildImageFilter

    def create(self, request, *args, **kwargs):
        """
        __Method__:
        POST

        __URL__: $LINK:buildimage-list$

        __Data__:

            {
                "image_id":           string,           # required
                "image_format":       string,           # required
                "md5":                string,           # required
                "rpms": [
                    {
                        "name":          string,         # required
                        "epoch":         int,            # required
                        "version":       string,         # required
                        "release":       string,         # required
                        "arch":          string,         # required
                        "srpm_name":     string,         # required
                        "srpm_nevra":    string,         # optional, the srpm_nevra field should be empty if and only if arch is "src".
                        "filename":      string          # optional
                    }
                    ...
                ],                                       # optional
                "archives": [
                    {
                        "build_nvr":     string,         # required
                        "name":          string,         # required
                        "size":          int,            # required
                        "md5":           string,         # required
                    }
                    ...
                ],                                       # optional
                "releases": [
                        release_id,      string          # optional
                        ......
                ]                                        # optional
            }

        If the RPM filename is omitted, a default value will be constructed
        based on name, version, release and arch.

        __Response__:

            {
                "url": url,
                "image_id":           string,
                "image_format":       string,
                "md5":                string,
                "rpms": [
                    "rpm_nevra",      string,
                    ...
                ],
                "archives": [
                    {
                        "build_nvr":     string,
                        "name":          string,
                        "size":          int,
                        "md5":           string,
                    }
                    ...
                ],
                "releases": [
                        "release_id",   string
                        ......
                ]
            }
        """
        return super(BuildImageViewSet, self).create(request, *args, **kwargs)

    def list(self, request, *args, **kwargs):
        """
        __Method__: GET

        __URL__: $LINK:buildimage-list$

        __Query params__:

        %(FILTERS)s

        The value of `component_name` should be either SRPM name or release
        component name if release component to srpm mapping exists.

        __Response__:

            # paged list
            {
              "count": int,
              "next": url,
              "previous": url,
              "results": [
                {
                    "url": url,
                    "image_id":           string,
                    "image_format":       string,
                    "md5":                string,
                    "rpms": [
                        "rpm_nevra",      string,
                        ...
                    ],
                    "archives": [
                        {
                            "build_nvr":     string,
                            "name":          string,
                            "size":          int,
                            "md5":           string,
                        }
                        ...
                    ],
                    "releases": [
                        "release_id",   string
                        ......
                    ]
                },
                ...
              ]
            }
        """
        return super(BuildImageViewSet, self).list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        """
        __Method__:
        GET

        __URL__: $LINK:buildimage-detail:instance_pk$

        __Response__:

            {
                "url": url,
                "image_id":           string,
                "image_format":       string,
                "md5":                string,
                "rpms": [
                    "rpm_nevra",      string,
                    ...
                ],
                "archives": [
                    {
                        "build_nvr":     string,
                        "name":          string,
                        "size":          int,
                        "md5":           string,
                    }
                    ...
                ],
                "releases": [
                        "release_id",   string
                        ......
                ]
            }
        """
        return super(BuildImageViewSet, self).retrieve(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        """
        __Method__:

        PUT: for full fields update

            {
                "image_id":           string,
                "image_format":       string,
                "md5":                string,
                "rpms": [
                    {
                        "name":          string,
                        "epoch":         int,
                        "version":       string,
                        "release":       string,
                        "arch":          string,
                        "srpm_name":     string,
                        "srpm_nevra":    string,
                    }
                    ...
                ],
                "archives": [
                    {
                        "build_nvr":     string,
                        "name":          string,
                        "size":          int,
                        "md5":           string,
                    }
                    ...
                ],
                "releases": [
                        "release_id",   string
                        ......
                ]
            }

        PATCH: for partial update

            # so you can give one or more fields in ["image_id", "image_format",
            #                                        "md5", "rpms", "archives"]
            # to do the update

        __NOTE:__ when updating `image_format`, its value must be an existed one, otherwise it will
        cause HTTP 400 BAD REQUEST error.

        __URL__: $LINK:buildimage-detail:instance_pk$

        __Response__:

            {
                "url": url,
                "image_id":           string,
                "image_format":       string,
                "md5":                string,
                "rpms": [
                    "rpm_nevra",      string,
                    ...
                ],
                "archives": [
                    {
                        "build_nvr":     string,
                        "name":          string,
                        "size":          int,
                        "md5":           string,
                    }
                    ...
                ],
                "releases": [
                        "release_id",   string
                        ......
                ]
            }
        """
        return super(BuildImageViewSet, self).update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """
        __Method__:
        DELETE

        __URL__: $LINK:buildimage-detail:instance_pk$

        __Response__:

            STATUS: 204 NO CONTENT

        __Example__:

            curl -X DELETE -H "Content-Type: application/json" $URL:buildimage-detail:1$
        """
        return super(BuildImageViewSet, self).destroy(request, *args, **kwargs)


class BuildImageRTTTestsViewSet(pdc_viewsets.StrictQueryParamMixin,
                                pdc_viewsets.ChangeSetUpdateModelMixin,
                                mixins.RetrieveModelMixin,
                                mixins.ListModelMixin,
                                viewsets.GenericViewSet):
    """
    ViewSet for  BuildImage RTT Tests.
    """
    queryset = models.BuildImage.objects.all().order_by('id')
    serializer_class = serializers.BuildImageRTTTestsSerializer
    filter_class = filters.BuildImageRTTTestsFilter

    def list(self, request, *args, **kwargs):
        """
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
                    "id":           int,
                    "test_result":  string
                },
                ...
              ]
            }
        """
        return super(BuildImageRTTTestsViewSet, self).list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        """
        __Method__:
        GET

        __URL__: $LINK:buildimagertttests-detail:instance_pk$

        __Response__:

            {
                "build_nvr":    string,
                "id":           int,
                "test_result":  string
            }
        """
        return super(BuildImageRTTTestsViewSet, self).retrieve(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        """
        PATCH: It only supports partial update. Only test_result could be updated

        __URL__: $LINK:buildimagertttests-detail:instance_pk$

        __Response__:

            {
                "build_nvr":    string,
                "id":           int,
                "test_result":  string
            }
        """
        return super(BuildImageRTTTestsViewSet, self).update(request, *args, **kwargs)

    def bulk_update(self, *args, **kwargs):
        """
        It is possible to perform bulk partial update on 'test_result' with `PATCH`
        method. The request body should contain an object, where keys are identifiers
        of objects to be modified and their values use the same format as normal patch.
        """
        return bulk_operations.bulk_update_impl(self, *args, **kwargs)
