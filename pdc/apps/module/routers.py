#
# Copyright (c) 2018 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
from pdc.apps.module.views import ModuleViewSet
from pdc.apps.utils.SortedRouter import router


router.register(r'modules', ModuleViewSet, base_name='modules')
