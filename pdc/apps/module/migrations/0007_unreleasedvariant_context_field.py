# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('module', '0006_unreleasedvariant_rpms'),
    ]

    operations = [
        migrations.AddField(
            model_name='unreleasedvariant',
            name='variant_context',
            field=models.CharField(default=b'00000000', max_length=100),
        ),
        migrations.AlterModelOptions(
            name='unreleasedvariant',
            options={'ordering': ('variant_name', 'variant_version', 'variant_release', 'variant_context')},
        ),
        migrations.AlterUniqueTogether(
            name='unreleasedvariant',
            unique_together=set([('variant_name', 'variant_version', 'variant_release', 'variant_context')]),
        ),
    ]
