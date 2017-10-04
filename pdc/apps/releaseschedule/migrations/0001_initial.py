# -*- coding: utf-8 -*-
#
# Copyright (c) 2017 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('release', '0014_auto_20170922_0804'),
        ('componentbranch', '0003_remove_componentbranch_active'),
    ]

    operations = [
        migrations.CreateModel(
            name='ReleaseSchedule',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('date', models.DateField(db_index=True)),
                ('release', models.ForeignKey(to='release.Release')),
                ('sla', models.ForeignKey(to='componentbranch.SLA')),
            ],
            options={
                'ordering': ['date'],
                'get_latest_by': 'date',
            },
        ),
        migrations.AlterUniqueTogether(
            name='releaseschedule',
            unique_together=set([('release', 'sla')]),
        ),
    ]
