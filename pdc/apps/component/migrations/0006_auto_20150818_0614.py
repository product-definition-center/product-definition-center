# -*- coding: utf-8 -*-
#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('component', '0005_auto_20150727_0929'),
    ]

    operations = [
        migrations.AlterField(
            model_name='releasecomponent',
            name='type',
            field=models.ForeignKey(related_name='release_components', on_delete=django.db.models.deletion.SET_DEFAULT, default=1, to='component.ReleaseComponentType'),
        ),
        migrations.AlterField(
            model_name='releasecomponentgroup',
            name='group_type',
            field=models.ForeignKey(related_name='release_component_groups', on_delete=django.db.models.deletion.PROTECT, to='component.GroupType'),
        ),
        migrations.AlterField(
            model_name='releasecomponentrelationship',
            name='from_component',
            field=models.ForeignKey(related_name='from_release_components', to='component.ReleaseComponent'),
        ),
        migrations.AlterField(
            model_name='releasecomponentrelationship',
            name='to_component',
            field=models.ForeignKey(related_name='to_release_components', to='component.ReleaseComponent'),
        ),
    ]
