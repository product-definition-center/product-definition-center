# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('package', '0013_set_default_subvariant_to_empty_string'),
    ]

    operations = [
        migrations.AddField(
            model_name='rpm',
            name='srpm_commit_branch',
            field=models.CharField(db_index=True, max_length=200, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='rpm',
            name='srpm_commit_hash',
            field=models.CharField(db_index=True, max_length=200, null=True, blank=True),
        ),
    ]
