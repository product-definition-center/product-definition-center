# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('kerb_auth', '0005_auto_20160516_1025'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='groupresourcepermission',
            unique_together=set([('resource_permission', 'group')]),
        ),
        migrations.AlterUniqueTogether(
            name='resourcepermission',
            unique_together=set([('resource', 'permission')]),
        ),
    ]
