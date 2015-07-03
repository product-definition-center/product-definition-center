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
        ('bindings', '0002_auto_20150525_1410'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='brewtag',
            unique_together=set([]),
        ),
        migrations.RemoveField(
            model_name='brewtag',
            name='brew_mapping',
        ),
        migrations.RemoveField(
            model_name='releasebrewmapping',
            name='release',
        ),
        migrations.DeleteModel(
            name='BrewTag',
        ),
        migrations.DeleteModel(
            name='ReleaseBrewMapping',
        ),
    ]
