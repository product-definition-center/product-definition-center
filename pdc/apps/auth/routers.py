# -*- coding: utf-8 -*-
#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#

from . import views
from pdc.apps.utils.SortedRouter import router


router.register(r'auth/token', views.TokenViewSet, base_name='token')
router.register(r'auth/groups', views.GroupViewSet)
router.register(r'auth/permissions', views.PermissionViewSet)
router.register(r'auth/current-user',
                views.CurrentUserViewSet,
                base_name='currentuser')
router.register(r'auth/resource-permissions', views.ResourcePermissionViewSet, base_name='resourcepermissions')
router.register(r'auth/group-resource-permissions', views.GroupResourcePermissionViewSet, base_name='groupresourcepermissions')
router.register(r'auth/resource-api-urls', views.ResourceApiUrlViewSet, base_name='resourceapiurls')
