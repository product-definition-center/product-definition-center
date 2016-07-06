from . import views
from pdc.apps.utils.SortedRouter import router


router.register(r'tree', views.TreeViewSet)
router.register(r'unreleasedvariant', views.UnreleasedVariantViewSet)
