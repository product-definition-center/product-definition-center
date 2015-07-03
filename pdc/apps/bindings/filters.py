#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
# NOTE it is important not to import any filters module from other apps. Doing
# that could cause cyclic imports and break the application.
from pdc.apps.common.filters import NullableCharFilter


def add_filter(filter_class, field_name, field):
    filter_class.base_filters[field_name] = field
    if hasattr(filter_class, 'Meta') and hasattr(filter_class.Meta, 'fields'):
        filter_class.Meta.fields = filter_class.Meta.fields + (field_name, )


def extend_release_filter(release_filter):
    add_filter(release_filter, 'bugzilla_product',
               NullableCharFilter(name='releasebugzillamapping__bugzilla_product'))
    add_filter(release_filter, 'dist_git_branch',
               NullableCharFilter(name='releasedistgitmapping__dist_git_branch'))


def extend_release_component_filter(release_component_filter):
    add_filter(release_component_filter, 'srpm_name',
               NullableCharFilter(name='srpmnamemapping__srpm_name'))
