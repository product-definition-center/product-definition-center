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
router.register(r'rpc/repos/clone',
                views.RepoCloneViewSet,
                base_name='repoclone')
router.register(r'content-delivery-content-categories', views.ContentCategoryViewSet,
                base_name='contentdeliverycontentcategory')
router.register(r'content-delivery-content-formats', views.ContentFormatViewSet,
                base_name='contentdeliverycontentformat')
router.register(r'content-delivery-services', views.ServiceViewSet,
                base_name='contentdeliveryservice')
router.register(r'push-targets', views.PushTargetViewSet,
                base_name='pushtarget')
router.register(r'multi-destinations', views.MultiDestinationViewSet,
                base_name='multidestination')
