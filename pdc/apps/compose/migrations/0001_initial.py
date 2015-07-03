# -*- coding: utf-8 -*-
#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('common', '0001_initial'),
        ('repository', '0001_initial'),
        ('package', '0001_initial'),
        ('release', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Compose',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('compose_id', models.CharField(unique=True, max_length=200)),
                ('compose_date', models.DateField()),
                ('compose_respin', models.PositiveIntegerField()),
                ('compose_label', models.CharField(max_length=200, null=True, blank=True)),
                ('dt_imported', models.DateTimeField(auto_now_add=True)),
                ('deleted', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='ComposeAcceptanceTestingState',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=200)),
            ],
        ),
        migrations.CreateModel(
            name='ComposeImage',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('image', models.ForeignKey(to='package.Image')),
            ],
        ),
        migrations.CreateModel(
            name='ComposeRPM',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('content_category', models.ForeignKey(to='repository.ContentCategory')),
            ],
        ),
        migrations.CreateModel(
            name='ComposeType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=200)),
            ],
        ),
        migrations.CreateModel(
            name='OverrideRPM',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('variant', models.CharField(max_length=200)),
                ('arch', models.CharField(max_length=20)),
                ('srpm_name', models.CharField(max_length=200)),
                ('rpm_name', models.CharField(max_length=200)),
                ('rpm_arch', models.CharField(max_length=20)),
                ('include', models.BooleanField(default=True)),
                ('comment', models.CharField(max_length=200, blank=True)),
                ('do_not_delete', models.BooleanField(default=False)),
                ('release', models.ForeignKey(to='release.Release')),
            ],
        ),
        migrations.CreateModel(
            name='Path',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('path', models.CharField(unique=True, max_length=4096)),
            ],
        ),
        migrations.CreateModel(
            name='Variant',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('variant_id', models.CharField(max_length=100)),
                ('variant_uid', models.CharField(max_length=200)),
                ('variant_name', models.CharField(max_length=300)),
                ('deleted', models.BooleanField(default=False)),
                ('compose', models.ForeignKey(to='compose.Compose')),
                ('variant_type', models.ForeignKey(related_name='compose_variant', to='release.VariantType')),
            ],
            options={
                'ordering': ('variant_uid',),
            },
        ),
        migrations.CreateModel(
            name='VariantArch',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('deleted', models.BooleanField(default=False)),
                ('arch', models.ForeignKey(related_name='+', to='common.Arch')),
                ('variant', models.ForeignKey(to='compose.Variant')),
            ],
            options={
                'ordering': ('variant', 'arch'),
            },
        ),
        migrations.AddField(
            model_name='composerpm',
            name='path',
            field=models.ForeignKey(to='compose.Path'),
        ),
        migrations.AddField(
            model_name='composerpm',
            name='rpm',
            field=models.ForeignKey(to='package.RPM'),
        ),
        migrations.AddField(
            model_name='composerpm',
            name='sigkey',
            field=models.ForeignKey(blank=True, to='common.SigKey', null=True),
        ),
        migrations.AddField(
            model_name='composerpm',
            name='variant_arch',
            field=models.ForeignKey(to='compose.VariantArch'),
        ),
        migrations.AddField(
            model_name='composeimage',
            name='variant_arch',
            field=models.ForeignKey(to='compose.VariantArch'),
        ),
        migrations.AddField(
            model_name='compose',
            name='acceptance_testing',
            field=models.ForeignKey(to='compose.ComposeAcceptanceTestingState'),
        ),
        migrations.AddField(
            model_name='compose',
            name='compose_type',
            field=models.ForeignKey(to='compose.ComposeType'),
        ),
        migrations.AddField(
            model_name='compose',
            name='linked_releases',
            field=models.ManyToManyField(related_name='linked_composes', to='release.Release', blank=True),
        ),
        migrations.AddField(
            model_name='compose',
            name='release',
            field=models.ForeignKey(to='release.Release'),
        ),
        migrations.AlterUniqueTogether(
            name='variantarch',
            unique_together=set([('variant', 'arch')]),
        ),
        migrations.AlterUniqueTogether(
            name='variant',
            unique_together=set([('compose', 'variant_uid')]),
        ),
        migrations.AlterUniqueTogether(
            name='overriderpm',
            unique_together=set([('release', 'variant', 'arch', 'rpm_name', 'rpm_arch')]),
        ),
        migrations.AlterUniqueTogether(
            name='composerpm',
            unique_together=set([('variant_arch', 'rpm')]),
        ),
        migrations.AlterUniqueTogether(
            name='composeimage',
            unique_together=set([('variant_arch', 'image')]),
        ),
        migrations.AlterUniqueTogether(
            name='compose',
            unique_together=set([('release', 'compose_label'), ('release', 'compose_date', 'compose_type', 'compose_respin')]),
        ),
    ]
