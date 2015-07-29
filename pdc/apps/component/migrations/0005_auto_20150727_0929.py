# -*- coding: utf-8 -*-
#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
from __future__ import unicode_literals

from django.db import models, migrations
from pdc.apps.component.models import ReleaseComponentRelationshipType


def create_release_component_relationship_types(apps, schema_editor):
    types = [
        'bundles',
        'executes'
    ]
    for relation_type in types:
        ReleaseComponentRelationshipType.objects.create(name=relation_type)


class Migration(migrations.Migration):

    dependencies = [
        ('component', '0004_auto_20150708_0746'),
    ]

    operations = [
        migrations.CreateModel(
            name='ReleaseComponentRelationship',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('from_component', models.ForeignKey(related_name='from_release_component', to='component.ReleaseComponent')),
            ],
        ),
        migrations.CreateModel(
            name='ReleaseComponentRelationshipType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=100)),
            ],
        ),
        migrations.AddField(
            model_name='releasecomponentrelationship',
            name='relation_type',
            field=models.ForeignKey(to='component.ReleaseComponentRelationshipType'),
        ),
        migrations.AddField(
            model_name='releasecomponentrelationship',
            name='to_component',
            field=models.ForeignKey(related_name='to_release_component', to='component.ReleaseComponent'),
        ),
        migrations.AlterUniqueTogether(
            name='releasecomponentrelationship',
            unique_together=set([('relation_type', 'from_component', 'to_component')]),
        ),
        migrations.RunPython(create_release_component_relationship_types),
    ]
