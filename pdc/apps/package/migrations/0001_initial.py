# -*- coding: utf-8 -*-
#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
from __future__ import unicode_literals

from django.db import models, migrations
import pdc.apps.common.validators


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Archive',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('build_nvr', models.CharField(max_length=200, db_index=True)),
                ('name', models.CharField(max_length=200, db_index=True)),
                ('size', models.BigIntegerField()),
                ('md5', models.CharField(max_length=32, validators=[pdc.apps.common.validators.validate_md5])),
            ],
        ),
        migrations.CreateModel(
            name='BuildImage',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('image_id', models.CharField(unique=True, max_length=200, db_index=True)),
                ('md5', models.CharField(max_length=32, validators=[pdc.apps.common.validators.validate_md5])),
                ('archives', models.ManyToManyField(to='package.Archive')),
            ],
        ),
        migrations.CreateModel(
            name='Image',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('file_name', models.CharField(max_length=200, db_index=True)),
                ('disc_number', models.PositiveIntegerField()),
                ('disc_count', models.PositiveIntegerField()),
                ('arch', models.CharField(max_length=200, db_index=True)),
                ('mtime', models.BigIntegerField()),
                ('size', models.BigIntegerField()),
                ('bootable', models.BooleanField(default=False)),
                ('implant_md5', models.CharField(max_length=32)),
                ('volume_id', models.CharField(max_length=32, null=True, blank=True)),
                ('md5', models.CharField(blank=True, max_length=32, null=True, validators=[pdc.apps.common.validators.validate_md5])),
                ('sha1', models.CharField(blank=True, max_length=40, null=True, validators=[pdc.apps.common.validators.validate_sha1])),
                ('sha256', models.CharField(max_length=64, validators=[pdc.apps.common.validators.validate_sha256])),
            ],
        ),
        migrations.CreateModel(
            name='ImageFormat',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=30, db_index=True)),
            ],
        ),
        migrations.CreateModel(
            name='ImageType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=30, db_index=True)),
            ],
        ),
        migrations.CreateModel(
            name='RPM',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=200, db_index=True)),
                ('epoch', models.PositiveIntegerField()),
                ('version', models.CharField(max_length=200, db_index=True)),
                ('release', models.CharField(max_length=200, db_index=True)),
                ('arch', models.CharField(max_length=200, db_index=True)),
                ('srpm_name', models.CharField(max_length=200, db_index=True)),
                ('srpm_nevra', models.CharField(db_index=True, max_length=200, null=True, blank=True)),
                ('filename', models.CharField(max_length=4096)),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='rpm',
            unique_together=set([('name', 'epoch', 'version', 'release', 'arch')]),
        ),
        migrations.AddField(
            model_name='image',
            name='image_format',
            field=models.ForeignKey(to='package.ImageFormat'),
        ),
        migrations.AddField(
            model_name='image',
            name='image_type',
            field=models.ForeignKey(to='package.ImageType'),
        ),
        migrations.AddField(
            model_name='buildimage',
            name='image_format',
            field=models.ForeignKey(to='package.ImageFormat'),
        ),
        migrations.AddField(
            model_name='buildimage',
            name='rpms',
            field=models.ManyToManyField(to='package.RPM'),
        ),
        migrations.AlterUniqueTogether(
            name='archive',
            unique_together=set([('build_nvr', 'name', 'md5')]),
        ),
        migrations.AlterUniqueTogether(
            name='image',
            unique_together=set([('file_name', 'sha256')]),
        ),
    ]
