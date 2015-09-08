# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('changeset', '0003_changeset_pdc_change_comment'),
    ]

    operations = [
        migrations.AddField(
            model_name='changeset',
            name='requested_on',
            field=models.DateTimeField(null=True),
        ),
    ]
