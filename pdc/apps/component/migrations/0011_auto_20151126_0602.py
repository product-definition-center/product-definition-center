# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('component', '0010_migrate_existing_contacts'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='globalcomponent',
            name='contacts',
        ),
        migrations.RemoveField(
            model_name='releasecomponent',
            name='contacts',
        ),
    ]
