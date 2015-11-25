# -*- coding: utf-8 -*-
#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
from __future__ import unicode_literals

from django.db import models, migrations


def update_existing_name(apps, schema_editor):
    user_model = apps.get_model('kerb_auth', 'User')
    for user in user_model.objects.all():
        user.full_name = user.first_name + ' ' + user.last_name
        user.save()


class Migration(migrations.Migration):

    dependencies = [
        ('kerb_auth', '0002_user_last_connected'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='full_name',
            field=models.CharField(max_length=80, verbose_name='full name', blank=True),
        ),
        migrations.RunPython(update_existing_name),
        migrations.RemoveField(
            model_name='user',
            name='first_name',
        ),
        migrations.RemoveField(
            model_name='user',
            name='last_name',
        ),
    ]
