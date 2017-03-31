#
# Copyright (c) 2017 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#

from pdc.apps.componentbranch import views
from pdc.apps.utils.SortedRouter import router


router.register(r'component-branches', views.ComponentBranchViewSet)
router.register(r'component-sla-types', views.SLAViewSet)
router.register(r'component-branch-slas', views.SLAToComponentBranchViewSet)
