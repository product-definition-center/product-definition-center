from kobo.django.menu.middleware import MenuMiddleware as KoboMenuMiddleware
from django.utils.deprecation import MiddlewareMixin


class MenuMiddleware(MiddlewareMixin, KoboMenuMiddleware):
    """
    Works around old Django support in kobo menu middleware.
    """
    pass
