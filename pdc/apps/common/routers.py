# -*- coding: utf-8 -*-
#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#

from . import views
from pdc.apps.utils.SortedRouter import router


router.register(r'labels', views.LabelViewSet, base_name='label')
router.register(r'arches', views.ArchViewSet)
router.register(r'sigkeys', views.SigKeyViewSet)
