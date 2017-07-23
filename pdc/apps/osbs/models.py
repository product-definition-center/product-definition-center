#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
from django.db import models

from pdc.apps.component import models as component_models


class OSBSRecord(models.Model):
    """Metadata about building component in OSBS.

    This record should only exist for components with type that has_osbs flag.
    These records are created automatically in signal handler after a component
    is created or updated or when the flag is toggled on type.
    """
    component = models.OneToOneField(component_models.ReleaseComponent,
                                     related_name='osbs',
                                     on_delete=models.CASCADE)
    autorebuild = models.NullBooleanField()

    def __unicode__(self):
        return u'OSBSRecord for {}/{}'.format(self.component.release.release_id,
                                              self.component.name)

    def export(self):
        return {
            'component': unicode(self.component),
            'autorebuild': self.autorebuild,
        }
