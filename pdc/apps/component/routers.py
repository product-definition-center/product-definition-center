# -*- coding: utf-8 -*-
#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#

from . import views
from pdc.apps.utils.SortedRouter import router


router.register(r'global-components',
                views.GlobalComponentViewSet,
                base_name='globalcomponent')
router.register(r'global-components/(?P<instance_pk>[^/.]+)/labels',
                views.GlobalComponentLabelViewSet,
                base_name='globalcomponentlabel')
router.register(r'release-components',
                views.ReleaseComponentViewSet,
                base_name='releasecomponent')
router.register(r'bugzilla-components',
                views.BugzillaComponentViewSet,
                base_name='bugzillacomponent')
router.register(r'component-groups', views.GroupViewSet, base_name='componentgroup')
router.register(r'component-group-types', views.GroupTypeViewSet, base_name='componentgrouptype')
router.register(r'component-relationship-types', views.ReleaseComponentRelationshipTypeViewSet,
                base_name='componentrelationshiptype')
router.register(r'release-component-relationships', views.ReleaseComponentRelationshipViewSet,
                base_name='rcrelationship')
router.register(r'release-component-types', views.ReleaseComponentTypeViewSet,
                base_name='releasecomponenttype')
