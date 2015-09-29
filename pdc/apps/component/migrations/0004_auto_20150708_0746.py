# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


def create_release_component_types(apps, schema_editor):
    types = [
        'rpm',
        'container',
        'zip',
        'iso',
        'composite'
    ]
    ReleaseComponentType = apps.get_model('component', 'ReleaseComponentType')
    for rc_type in types:
        ReleaseComponentType.objects.create(name=rc_type)


class Migration(migrations.Migration):

    dependencies = [
        ('component', '0003_auto_20150701_0544'),
    ]

    operations = [
        migrations.CreateModel(
            name='ReleaseComponentType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=100)),
            ],
        ),
        migrations.AddField(
            model_name='releasecomponent',
            name='type',
            field=models.ForeignKey(related_name='release_components', on_delete=django.db.models.deletion.SET_NULL,
                                    blank=True, to='component.ReleaseComponentType', null=True),
        ),
        migrations.RunPython(create_release_component_types),
    ]
