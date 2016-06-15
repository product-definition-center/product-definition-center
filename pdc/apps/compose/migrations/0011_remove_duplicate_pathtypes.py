# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db import migrations, models

def remove_duplicate_pathtype(apps, schema_editor):
    PathType = apps.get_model('compose', 'PathType')
    ComposeRelPath = apps.get_model('compose', 'ComposeRelPath')
    qs = PathType.objects.values('name')
    uniq = set([])
    dup = set([])
    for x in qs:
        if x['name'] not in uniq:
            uniq.add(x['name'])
        else:
            dup.add(x['name'])
    for name in dup:
        q = PathType.objects.filter(name=name)
        pt = q.first()
        crps = ComposeRelPath.objects.filter(type__name=name)
        for crp in crps:
            crp.type = pt
            crp.save()
        for p in q.exclude(id=pt.id):
            p.delete()


class Migration(migrations.Migration):
    dependencies = [
        ('compose', '0010_auto_20160407_1322'),
    ]

    operations = [
        migrations.RunPython(remove_duplicate_pathtype, reverse_code=migrations.RunPython.noop),
    ]
