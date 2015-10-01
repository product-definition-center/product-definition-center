# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def migrate_rc_contacts(apps, schema_editor):
    """Migrate contacts stored directly on release components."""
    RoleContact = apps.get_model('contact', 'RoleContact')
    ReleaseComponentContact = apps.get_model('contact', 'ReleaseComponentContact')
    for contact in RoleContact.objects.all():
        for rc in contact.releasecomponent_set.all():
            ReleaseComponentContact.objects.create(component=rc,
                                                   role=contact.contact_role,
                                                   contact=contact.contact)

def migrate_gc_contacts(apps, schema_editor):
    """Migrate global components contacts.

    Store directly on global components and add them to release components
    unless the same type is already provided.
    """
    RoleContact = apps.get_model('contact', 'RoleContact')
    GlobalComponentContact = apps.get_model('contact', 'GlobalComponentContact')
    ReleaseComponentContact = apps.get_model('contact', 'ReleaseComponentContact')
    for contact in RoleContact.objects.all():
        for gc in contact.globalcomponent_set.all():
            GlobalComponentContact.objects.create(component=gc,
                                                  role=contact.contact_role,
                                                  contact=contact.contact)
            for rc in gc.releasecomponent_set.all():
                if not ReleaseComponentContact.objects.filter(component=rc,
                                                              role=contact.contact_role).exists():
                    ReleaseComponentContact.objects.create(component=rc,
                                                           role=contact.contact_role,
                                                           contact=contact.contact)


class Migration(migrations.Migration):

    dependencies = [
        ('component', '0009_releasecomponenttype_has_osbs'),
        ('contact', '0003_auto_20151001_1309'),
    ]

    operations = [
        migrations.RunPython(migrate_rc_contacts),
        migrations.RunPython(migrate_gc_contacts),
    ]
