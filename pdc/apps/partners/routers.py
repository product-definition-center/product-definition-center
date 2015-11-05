# -*- coding: utf-8 -*-
#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#

from . import views
from pdc.apps.utils.SortedRouter import router


router.register(r'partner-types',
                views.PartnerTypeViewSet)
router.register(r'partners',
                views.PartnerViewSet)
router.register(r'partners-mapping',
                views.PartnerMappingViewSet)
