# -*- coding: utf-8 -*-
#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
from __future__ import unicode_literals

from django.db import models, migrations
import mptt.fields


class Migration(migrations.Migration):

    dependencies = [
        ('contact', '0001_initial'),
        ('component', '0001_initial'),
        ('common', '0001_initial'),
        ('release', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='releasecomponent',
            name='contacts',
            field=models.ManyToManyField(to='contact.RoleContact', blank=True),
        ),
        migrations.AddField(
            model_name='releasecomponent',
            name='global_component',
            field=models.ForeignKey(to='component.GlobalComponent'),
        ),
        migrations.AddField(
            model_name='releasecomponent',
            name='release',
            field=models.ForeignKey(to='release.Release'),
        ),
        migrations.AddField(
            model_name='globalcomponent',
            name='contacts',
            field=models.ManyToManyField(to='contact.RoleContact', blank=True),
        ),
        migrations.AddField(
            model_name='globalcomponent',
            name='labels',
            field=models.ManyToManyField(to='common.Label', blank=True),
        ),
        migrations.AddField(
            model_name='globalcomponent',
            name='upstream',
            field=models.OneToOneField(null=True, blank=True, to='component.Upstream'),
        ),
        migrations.AddField(
            model_name='bugzillacomponent',
            name='parent_component',
            field=mptt.fields.TreeForeignKey(related_name='children', blank=True, to='component.BugzillaComponent', null=True),
        ),
        migrations.AlterUniqueTogether(
            name='releasecomponent',
            unique_together=set([('release', 'global_component', 'name')]),
        ),
        migrations.AlterUniqueTogether(
            name='bugzillacomponent',
            unique_together=set([('name', 'parent_component')]),
        ),
    ]
