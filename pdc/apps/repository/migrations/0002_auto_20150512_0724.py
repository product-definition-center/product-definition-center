# -*- coding: utf-8 -*-
#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
from __future__ import unicode_literals

from django.db import models, migrations


def create(apps, model_name, data):
    model = apps.get_model('repository', model_name)
    for item in data:
        model.objects.create(**item)


def create_service(apps, schema_editor):
    create(apps, 'Service',
           [
               {
                   'description': 'Red Hat Network',
                   'name': 'rhn'
               },
               {
                   'description': 'Pulp (CDN)',
                   'name': 'pulp'
               },
               {
                   'description': 'ftp://ftp.redhat.com',
                   'name': 'ftp'
               }
           ])


def create_content_category(apps, schema_editor):
    create(apps, 'ContentCategory',
           [
               {
                   'description': 'Binary',
                   'name': 'binary'
               },
               {
                   'description': 'Debug',
                   'name': 'debug'
               },
               {
                   'description': 'Source',
                   'name': 'source'
               }
           ])


def create_content_format(apps, schema_editor):
    create(apps, 'ContentFormat',
           [
               {
                   'description': 'RPM packages',
                   'name': 'rpm'
               },
               {
                   'description': 'ISO images',
                   'name': 'iso'
               },
               {
                   'description': 'Installable kickstart trees',
                   'name': 'kickstart'
               },
               {
                   'description': 'Comps XML with package group definitions',
                   'name': 'comps'
               },
               {
                   'description': 'Docker images',
                   'name': 'docker'
               }
           ])


def create_repo_family(apps, schema_editor):
    create(apps, 'RepoFamily',
           [
               {
                   'description': 'Production repositories',
                   'name': 'dist'
               },
               {
                   'description': 'Beta (pre-production) repositories',
                   'name': 'beta'
               },
               {
                   'description': 'Repostitories for High Touch Beta (HTB) customers',
                   'name': 'htb'
               }
           ])


class Migration(migrations.Migration):

    dependencies = [
        ('repository', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_service),
        migrations.RunPython(create_content_category),
        migrations.RunPython(create_content_format),
        migrations.RunPython(create_repo_family),
    ]
