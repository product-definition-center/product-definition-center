from . import views
from pdc.apps.utils.SortedRouter import router


router.register(r'trees', views.TreeViewSet)
router.register(r'unreleasedvariants', views.UnreleasedVariantViewSet)
