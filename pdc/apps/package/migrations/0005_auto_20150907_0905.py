# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('package', '0004_rpm_linked_releases'),
    ]

    operations = [
        migrations.CreateModel(
            name='Dependency',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('type', models.PositiveIntegerField(choices=[(1, b'provides'), (2, b'requires'), (3, b'obsoletes'), (4, b'conflicts'), (5, b'recommends'), (6, b'suggests')])),
                ('name', models.CharField(max_length=200)),
                ('version', models.CharField(max_length=200, null=True, blank=True)),
                ('comparison', models.CharField(max_length=50, null=True, blank=True)),
                ('rpm', models.ForeignKey(to='package.RPM')),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='dependency',
            unique_together=set([('type', 'name', 'version', 'comparison', 'rpm')]),
        ),
    ]
