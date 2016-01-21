# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('release', '0002_auto_20150512_0719'),
        ('package', '0008_buildimage_test_result'),
    ]

    operations = [
        migrations.AddField(
            model_name='rpm',
            name='built_for_release',
            field=models.ForeignKey(blank=True, to='release.Release', null=True),
        ),
    ]
