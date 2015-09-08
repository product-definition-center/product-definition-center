# -*- coding: utf-8 -*-
from django.db import models, migrations

def migrate_requested_on(apps, schema_editor):
    Changeset = apps.get_model("changeset", "Changeset")
    for changeset in Changeset.objects.all():
        if not changeset.requested_on:
            changeset.requested_on = changeset.committed_on
            changeset.save()

class Migration(migrations.Migration):

    dependencies = [
        ('changeset', '0004_changeset_requested_on'),
    ]

    operations = [
        migrations.RunPython(migrate_requested_on),
    ]