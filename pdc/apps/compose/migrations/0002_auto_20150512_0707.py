# -*- coding: utf-8 -*-
#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
from __future__ import unicode_literals

from django.db import models, migrations


def create_compose_types(apps, schema_editor):
    arches = [
        'production',
        'nightly',
        'test',
    ]
    ComposeType = apps.get_model('compose', 'ComposeType')
    for arch in arches:
        ComposeType.objects.create(name=arch)


def create_compose_acceptance_testing_statuses(apps, schema_editor):
    arches = [
        'untested',
        'passed',
        'failed',
    ]
    ComposeAcceptanceTestingState = apps.get_model('compose', 'ComposeAcceptanceTestingState')
    for arch in arches:
        ComposeAcceptanceTestingState.objects.create(name=arch)


class Migration(migrations.Migration):

    dependencies = [
        ('compose', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_compose_types),
        migrations.RunPython(create_compose_acceptance_testing_statuses),
    ]
