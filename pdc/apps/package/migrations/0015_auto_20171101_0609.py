# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import datetime
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('repository', '0004_multidestination'),
        ('package', '0014_auto_20170412_1331'),
    ]

    operations = [
        migrations.CreateModel(
            name='ReleasedFiles',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('build', models.CharField(max_length=200, null=True, blank=True)),
                ('package', models.CharField(max_length=200, null=True, blank=True)),
                ('file', models.CharField(max_length=200, null=True, blank=True)),
                ('file_primary_key', models.IntegerField(default=0)),
                ('released_date', models.DateField(null=True, blank=True)),
                ('release_date', models.DateField()),
                ('created_at', models.DateTimeField(default=datetime.datetime(2017, 11, 1, 6, 9, 49, 156194, tzinfo=utc), null=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('zero_day_release', models.BooleanField(default=False)),
                ('obsolete', models.BooleanField(default=False)),
                ('repo', models.ForeignKey(to='repository.Repo')),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='releasedfiles',
            unique_together=set([('file_primary_key', 'repo')]),
        ),
    ]
