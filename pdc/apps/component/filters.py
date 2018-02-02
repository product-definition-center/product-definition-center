# -*- coding: utf-8 -*-
#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
from django.db.models import Q

from django_filters import CharFilter

from .models import (GlobalComponent,
                     ReleaseComponent,
                     BugzillaComponent,
                     ReleaseComponentGroup,
                     GroupType,
                     ReleaseComponentRelationship,
                     ReleaseComponentRelationshipType)
from pdc.apps.common.filters import (ComposeFilterSet,
                                     value_is_not_empty,
                                     MultiValueFilter,
                                     CaseInsensitiveBooleanFilter)


class ComponentFilter(ComposeFilterSet):
    name = MultiValueFilter()
    dist_git_path = MultiValueFilter()
    label = MultiValueFilter(name='labels__name', distinct=True)
    upstream_homepage = MultiValueFilter(name='upstream__homepage')
    upstream_scm_type = MultiValueFilter(name='upstream__scm_type')
    upstream_scm_url = MultiValueFilter(name='upstream__scm_url')

    class Meta:
        model = GlobalComponent
        fields = ('name', 'dist_git_path', 'label',
                  'upstream_homepage', 'upstream_scm_type', 'upstream_scm_url')


class ReleaseComponentFilter(ComposeFilterSet):
    name = MultiValueFilter()
    release = MultiValueFilter(name='release__release_id')
    global_component = MultiValueFilter(name='global_component__name')
    bugzilla_component = MultiValueFilter(name='bugzilla_component__name')
    brew_package = MultiValueFilter()
    active = CaseInsensitiveBooleanFilter()
    type = CharFilter(name='type__name')
    dist_git_branch = MultiValueFilter(method='filter_by_dist_git_branch')

    @value_is_not_empty
    def filter_by_dist_git_branch(self, qs, name, value):
        q = Q(dist_git_branch__in=value) | Q(release__releasedistgitmapping__dist_git_branch__in=value,
                                             dist_git_branch__isnull=True)
        return qs.filter(q)

    class Meta:
        model = ReleaseComponent
        fields = ('name', 'release', 'global_component', 'active',
                  'bugzilla_component', 'type', 'dist_git_branch')


class BugzillaComponentFilter(ComposeFilterSet):
    name = MultiValueFilter()
    parent_component = MultiValueFilter(name='parent_component__name')

    class Meta:
        model = BugzillaComponent
        fields = ('name', 'parent_component')


class GroupTypeFilter(ComposeFilterSet):
    name = MultiValueFilter()

    class Meta:
        model = GroupType
        fields = ('name',)


class GroupFilter(ComposeFilterSet):
    group_type = MultiValueFilter(name='group_type__name')
    release = MultiValueFilter(name='release__release_id')
    release_component = MultiValueFilter(name='components__name', distinct=True)

    class Meta:
        model = ReleaseComponentGroup
        fields = ('group_type', 'release', 'release_component')


class ReleaseComponentRelationshipFilter(ComposeFilterSet):
    type = MultiValueFilter(name='relation_type__name')
    from_component_release = MultiValueFilter(name='from_component__release__release_id')
    from_component_name = MultiValueFilter(name='from_component__name')
    to_component_release = MultiValueFilter(name='to_component__release__release_id')
    to_component_name = MultiValueFilter(name='to_component__name')

    class Meta:
        model = ReleaseComponentRelationship
        fields = ('type', 'from_component_release', 'from_component_name', 'to_component_release',
                  'to_component_name')


class ReleaseComponentRelationshipTypeFilter(ComposeFilterSet):
    name = MultiValueFilter()

    class Meta:
        model = ReleaseComponentRelationshipType
        fields = ('name',)
