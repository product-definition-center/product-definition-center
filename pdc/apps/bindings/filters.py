#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
# NOTE it is important not to import any filters module from other apps. Doing
# that could cause cyclic imports and break the application.
from pdc.apps.common.filters import NullableCharFilter


def extend_release_filter(release_view):
    filter_class = release_view.filter_class

    class ExtendedReleaseFilter(filter_class):
        bugzilla_product = NullableCharFilter(name='releasebugzillamapping__bugzilla_product')
        dist_git_branch = NullableCharFilter(name='releasedistgitmapping__dist_git_branch')

        class Meta(filter_class.Meta):
            fields = filter_class.Meta.fields + ('bugzilla_product', 'dist_git_branch',)

    release_view.filter_class = ExtendedReleaseFilter


def extend_release_component_filter(release_component_view):
    filter_class = release_component_view.filter_class

    class ExtendedReleaseComponentFilter(filter_class):
        srpm_name = NullableCharFilter(name='srpmnamemapping__srpm_name')

        class Meta(filter_class.Meta):
            fields = filter_class.Meta.fields + ('srpm_name',)

    release_component_view.filter_class = ExtendedReleaseComponentFilter
