from pdc.apps.module.views import ModuleViewSet
from pdc.apps.utils.SortedRouter import router


router.register(r'modules', ModuleViewSet, base_name='modules')
