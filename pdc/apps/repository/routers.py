# -*- coding: utf-8 -*-
#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#

from . import views
from pdc.apps.utils.SortedRouter import router


router.register(r'content-delivery-repos', views.RepoViewSet,
                base_name='contentdeliveryrepos')
router.register(r'content-delivery-repo-families', views.RepoFamilyViewSet,
                base_name='contentdeliveryrepofamily')
router.register(r'rpc/content-delivery-repos/clone',
                views.RepoCloneViewSet,
                base_name='cdreposclone')
router.register(r'repos', views.RepoViewSet)
router.register(r'repo-families', views.RepoFamilyViewSet,
                base_name='repofamily')
router.register(r'rpc/repos/clone',
                views.RepoCloneViewSet,
                base_name='repoclone')
router.register(r'content-delivery-content-categories', views.ContentCategoryViewSet,
                base_name='contentdeliverycontentcategory')
router.register(r'content-delivery-content-formats', views.ContentFormatViewSet,
                base_name='contentdeliverycontentformat')
router.register(r'content-delivery-services', views.ServiceViewSet,
                base_name='contentdeliveryservice')

# TODO: these three end-points will be removed
router.register(r'content-delivery-content-category', views.ContentCategoryViewSet,
                base_name='contentcategorydeprecated')
router.register(r'content-delivery-content-format', views.ContentFormatViewSet,
                base_name='contentformatdeprecated')
router.register(r'content-delivery-service', views.ServiceViewSet,
                base_name='contentservicedeprecated')
