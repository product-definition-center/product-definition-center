# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('common', '0002_auto_20150512_0703'),
        ('repository', '0002_auto_20150512_0724'),
    ]

    operations = [
        migrations.CreateModel(
            name='UnreleasedVariant',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('variant_id', models.CharField(max_length=100)),
                ('variant_uid', models.CharField(max_length=200)),
                ('variant_name', models.CharField(max_length=300)),
                ('variant_type', models.CharField(max_length=100)),
                ('variant_version', models.CharField(max_length=100)),
                ('variant_release', models.CharField(max_length=100)),
                ('koji_tag', models.CharField(max_length=300)),
            ],
            options={
                'ordering': ('variant_uid', 'variant_version',
                             'variant_release'),
            },
        ),
        migrations.AlterUniqueTogether(
            name='unreleasedvariant',
            unique_together=set([('variant_uid', 'variant_version',
                                  'variant_release')]),
        ),
    ]
