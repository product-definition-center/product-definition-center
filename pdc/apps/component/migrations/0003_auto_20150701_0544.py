# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('release', '0002_auto_20150512_0719'),
        ('component', '0002_auto_20150525_1410'),
    ]

    operations = [
        migrations.CreateModel(
            name='GroupType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=100)),
                ('description', models.CharField(max_length=200, null=True, blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='ReleaseComponentGroup',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('description', models.CharField(max_length=200)),
                ('components', models.ManyToManyField(related_name='release_component_groups', to='component.ReleaseComponent', blank=True)),
                ('group_type', models.ForeignKey(related_name='release_component_groups', to='component.GroupType')),
                ('release', models.ForeignKey(related_name='release_component_groups', to='release.Release')),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='releasecomponentgroup',
            unique_together=set([('group_type', 'release', 'description')]),
        ),
    ]
