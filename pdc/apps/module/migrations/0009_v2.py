# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('module', '0008_unreleasedvariant_make_variant_uid_unique'),
    ]

    operations = [
        migrations.RenameModel('UnreleasedVariant', 'Module'),
        migrations.RenameField(
            model_name='module',
            old_name='variant_version',
            new_name='stream',
        ),
        migrations.RenameField(
            model_name='module',
            old_name='variant_release',
            new_name='version',
        ),
        migrations.RenameField(
            model_name='module',
            old_name='variant_context',
            new_name='context',
        ),
        migrations.RenameField(
            model_name='module',
            old_name='variant_name',
            new_name='name',
        ),
        migrations.RenameField(
            model_name='module',
            old_name='variant_type',
            new_name='type',
        ),
        migrations.RenameField(
            model_name='module',
            old_name='variant_uid',
            new_name='uid',
        ),
        # Increase the max length to be the sum of name:stream:version:context
        # with a little bit of cushion
        migrations.AlterField(
            model_name='module',
            name='uid',
            field=models.CharField(unique=True, max_length=610),
        ),
        # Set the default value to 'module'
        migrations.AlterField(
            model_name='module',
            name='type',
            field=models.CharField(default=b'module', max_length=100),
        ),
        # Remove the default value
        migrations.AlterField(
            model_name='module',
            name='context',
            field=models.CharField(max_length=100),
        ),
        migrations.AlterModelOptions(
            name='module',
            options={'ordering': ('name', 'stream', 'version', 'context')},
        ),
        migrations.AlterUniqueTogether(
            name='module',
            unique_together=set([('name', 'stream', 'version', 'context')]),
        ),
    ]
