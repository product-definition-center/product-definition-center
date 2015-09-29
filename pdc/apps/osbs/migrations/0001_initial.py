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
        ('component', '0009_releasecomponenttype_has_osbs'),
    ]

    operations = [
        migrations.CreateModel(
            name='OSBSRecord',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('autorebuild', models.NullBooleanField()),
                ('component', models.OneToOneField(to='component.ReleaseComponent')),
            ],
        ),
    ]
