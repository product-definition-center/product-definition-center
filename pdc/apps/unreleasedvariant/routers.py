#
# Copyright (c) 2018 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
from pdc.apps.unreleasedvariant.views import UnreleasedVariantViewSet
from pdc.apps.utils.SortedRouter import router


router.register(r'unreleasedvariants', UnreleasedVariantViewSet, base_name='unreleasedvariants')
