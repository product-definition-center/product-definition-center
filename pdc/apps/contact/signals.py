#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
import json

from django.dispatch import receiver

from . import models
from pdc.apps.component import signals as component_signals


@receiver(component_signals.releasecomponent_clone)
def clone_osbs_record(sender, request, orig_component_pk, component, **kwargs):
    for c in models.ReleaseComponentContact.objects.filter(component_id=orig_component_pk):
        copy = models.ReleaseComponentContact(component=component, contact=c.contact, role=c.role)
        copy.save()
        request.changeset.add('releasecomponentcontact', copy.pk, 'null', json.dumps(copy.export()))
