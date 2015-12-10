# -*- coding: utf-8 -*-
#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#

from . import views
from pdc.apps.utils.SortedRouter import router


router.register(r'rpms', views.RPMViewSet, base_name='rpms')
router.register(r'images', views.ImageViewSet)
router.register(r'build-images', views.BuildImageViewSet)
router.register(r'build-image-rtt-tests', views.BuildImageRTTTestsViewSet, base_name='buildimagertttests')
