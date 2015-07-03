# -*- coding: utf-8 -*-
#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('bindings', '0001_initial'),
        ('component', '0001_initial'),
        ('release', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='releasecomponentsrpmnamemapping',
            name='release_component',
            field=models.OneToOneField(related_name='srpmnamemapping', to='component.ReleaseComponent'),
        ),
        migrations.AddField(
            model_name='releasebugzillamapping',
            name='release',
            field=models.OneToOneField(to='release.Release'),
        ),
        migrations.AddField(
            model_name='releasebrewmapping',
            name='release',
            field=models.OneToOneField(related_name='brew_mapping', to='release.Release'),
        ),
        migrations.AddField(
            model_name='brewtag',
            name='brew_mapping',
            field=models.ForeignKey(related_name='allowed_tags', to='bindings.ReleaseBrewMapping'),
        ),
        migrations.AlterUniqueTogether(
            name='brewtag',
            unique_together=set([('brew_mapping', 'tag_name')]),
        ),
    ]
