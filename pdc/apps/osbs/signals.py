#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
from django.dispatch import receiver
from django.db.models.signals import post_save

from . import models
from pdc.apps.component import models as component_models


@receiver(post_save, sender=component_models.ReleaseComponent)
def component_post_save_handler(sender, instance, **kwargs):
    """Create or delete OSBS record after component is saved.
    """
    if instance.type.has_osbs and not hasattr(instance, 'osbs'):
        models.OSBSRecord.objects.create(component=instance)
    elif not instance.type.has_osbs and hasattr(instance, 'osbs'):
        models.OSBSRecord.objects.get(component=instance).delete()


@receiver(post_save, sender=component_models.ReleaseComponentType)
def type_post_save_handler(sender, instance, **kwargs):
    """Create records for all components if their type now has OSBS.

    If the has_osbs has been set to True, this call will take quite a lot of
    time.
    """
    if instance.has_osbs:
        models.OSBSRecord.objects.bulk_create(
            [models.OSBSRecord(component=c)
             for c in instance.release_components.filter(osbs__isnull=True)]
        )
    else:
        models.OSBSRecord.objects.filter(component__type=instance).delete()
