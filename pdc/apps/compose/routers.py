# -*- coding: utf-8 -*-
#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#

from . import views
from pdc.apps.utils.SortedRouter import router


router.register(r'composes', views.ComposeViewSet)
router.register(r'composes/(?P<compose_id>[^/]+)/rpm-mapping',
                views.ComposeRPMMappingView,
                base_name='composerpmmapping')
router.register(r'compose-rpms', views.ComposeRPMView)
router.register(r'compose-images', views.ComposeImageView)
router.register(r'rpc/compose/import-images',
                views.ComposeImportImagesView,
                base_name='composeimportimages')

router.register('overrides/rpm',
                views.ReleaseOverridesRPMViewSet,
                base_name='overridesrpm')
router.register(r'rpc/where-to-file-bugs', views.FilterBugzillaProductsAndComponents,
                base_name='bugzilla')
router.register('rpc/find-compose-by-release-rpm/(?P<release_id>[^/]+)/(?P<rpm_name>[^/]+)',
                views.FindComposeByReleaseRPMViewSet,
                base_name='findcomposebyrr')
router.register('rpc/find-older-compose-by-compose-rpm/(?P<compose_id>[^/]+)/(?P<rpm_name>[^/]+)',
                views.FindOlderComposeByComposeRPMViewSet,
                base_name='findoldercomposebycr')
router.register('rpc/find-composes-by-product-version-rpm/(?P<product_version>[^/]+)/(?P<rpm_name>[^/]+)',
                views.FindComposeByProductVersionRPMViewSet,
                base_name='findcomposesbypvr')
router.register(r'compose/package',
                views.FindComposeWithOlderPackageViewSet,
                base_name='findcomposewitholderpackage')
router.register(r'compose-tree-locations', views.ComposeTreeViewSet,
                base_name='composetreelocations')
