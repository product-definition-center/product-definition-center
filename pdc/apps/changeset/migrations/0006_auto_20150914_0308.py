# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('changeset', '0005_changeset_requested_on_data_migration'),
    ]

    operations = [
        migrations.AlterField(
            model_name='changeset',
            name='requested_on',
            field=models.DateTimeField(),
        ),
    ]
