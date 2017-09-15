# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('repository', '0003_pushtarget'),
        ('release', '0013_release_allowed_debuginfos'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='allowed_push_targets',
            field=models.ManyToManyField(to='repository.PushTarget'),
        ),
        migrations.AddField(
            model_name='productversion',
            name='masked_push_targets',
            field=models.ManyToManyField(to='repository.PushTarget'),
        ),
        migrations.AddField(
            model_name='release',
            name='masked_push_targets',
            field=models.ManyToManyField(to='repository.PushTarget'),
        ),
        migrations.AddField(
            model_name='variant',
            name='masked_push_targets',
            field=models.ManyToManyField(to='repository.PushTarget'),
        ),
    ]
