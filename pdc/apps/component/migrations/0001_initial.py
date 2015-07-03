# -*- coding: utf-8 -*-
#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion
import pdc.apps.component.models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='BugzillaComponent',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=100, validators=[pdc.apps.component.models.validate_bc_name])),
                ('lft', models.PositiveIntegerField(editable=False, db_index=True)),
                ('rght', models.PositiveIntegerField(editable=False, db_index=True)),
                ('tree_id', models.PositiveIntegerField(editable=False, db_index=True)),
                ('level', models.PositiveIntegerField(editable=False, db_index=True)),
            ],
        ),
        migrations.CreateModel(
            name='GlobalComponent',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=100)),
                ('dist_git_path', models.CharField(max_length=200, null=True, blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='ReleaseComponent',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=100)),
                ('dist_git_branch', models.CharField(max_length=100, null=True, blank=True)),
                ('brew_package', models.CharField(max_length=100, null=True, blank=True)),
                ('active', models.BooleanField(default=True)),
                ('bugzilla_component', models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, blank=True, to='component.BugzillaComponent', null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Upstream',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('homepage', models.URLField()),
                ('scm_type', models.CharField(max_length=50, null=True, blank=True)),
                ('scm_url', models.URLField(null=True, blank=True)),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='upstream',
            unique_together=set([('homepage', 'scm_type', 'scm_url')]),
        ),
    ]
