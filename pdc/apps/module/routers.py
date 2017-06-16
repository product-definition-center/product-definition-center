from . import views
from pdc.apps.utils.SortedRouter import router


router.register(r'unreleasedvariants', views.UnreleasedVariantViewSet)
