# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('kerb_auth', '0004_auto_20160512_1051'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='actionpermission',
            options={'ordering': ('name',)},
        ),
        migrations.AlterModelOptions(
            name='groupresourcepermission',
            options={'ordering': ('group__name', 'resource_permission__resource__name', 'resource_permission__permission__name')},
        ),
        migrations.AlterModelOptions(
            name='resourcepermission',
            options={'ordering': ('resource__name', 'permission__name')},
        ),
    ]
