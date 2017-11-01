# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('repository', '0004_multidestination'),
    ]

    operations = [
        migrations.AddField(
            model_name='contentformat',
            name='pdc_endpoint',
            field=models.CharField(max_length=200, null=True),
        ),
    ]
