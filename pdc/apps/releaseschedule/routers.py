# -*- coding: utf-8 -*-
#
# Copyright (c) 2017 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
from . import views
from pdc.apps.utils.SortedRouter import router


router.register(r'release-schedules',
                views.ReleaseScheduleViewSet,
                base_name='releaseschedule')
