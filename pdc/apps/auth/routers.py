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
