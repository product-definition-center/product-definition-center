#
# Copyright (c) 2018 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#


def update_resources(sender, **kwargs):
    """Updates list of resources for which permissions can be created"""
    import inspect

    from django.conf import settings
    from django.utils.module_loading import autodiscover_modules

    from pdc.apps.auth.models import ResourcePermission, ActionPermission, Resource
    from pdc.apps.utils.SortedRouter import router
    from pdc.apps.utils.utils import convert_method_to_action

    if getattr(settings, 'SKIP_RESOURCE_CREATION', False):
        # We are running tests, don't create anything
        return

    API_WITH_NO_PERMISSION_CONTROL = set(['auth/token', 'auth/current-user'])
    # Import all routers to have list of all end-points.
    autodiscover_modules('routers')

    action_to_obj_dict = {}
    for action in ('update', 'create', 'delete', 'read'):
        action_to_obj_dict[action] = ActionPermission.objects.get(name=action)

    for prefix, view_set, basename in router.registry:
        if prefix in API_WITH_NO_PERMISSION_CONTROL:
            continue
        view_name = str(view_set)
        resource_obj, created = Resource.objects.get_or_create(name=prefix,
                                                               defaults={'view': view_name})
        if not created and resource_obj.view != view_name:
            # Update the name of the View class
            resource_obj.view = view_name
            resource_obj.save()
        for name, method in inspect.getmembers(view_set, predicate=inspect.ismethod):
            action_name = convert_method_to_action(name.lower())
            if action_name:
                action_permission = action_to_obj_dict[action_name]
                ResourcePermission.objects.get_or_create(resource=resource_obj,
                                                         permission=action_permission)
