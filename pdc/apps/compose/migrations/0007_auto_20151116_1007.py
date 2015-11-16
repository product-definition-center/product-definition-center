# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('repository', '0002_auto_20150512_0724'),
        ('compose', '0006_auto_20150821_0616'),
    ]

    operations = [
        migrations.CreateModel(
            name='ComposeTree',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('arch', models.CharField(max_length=50)),
                ('url', models.CharField(max_length=100)),
                ('compose', models.ForeignKey(to='compose.Compose')),
            ],
        ),
        migrations.CreateModel(
            name='Location',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=50)),
                ('short', models.CharField(unique=True, max_length=50)),
            ],
        ),
        migrations.CreateModel(
            name='Scheme',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=50)),
            ],
        ),
        migrations.AddField(
            model_name='composetree',
            name='location',
            field=models.ForeignKey(to='compose.Location'),
        ),
        migrations.AddField(
            model_name='composetree',
            name='scheme',
            field=models.ForeignKey(to='compose.Scheme'),
        ),
        migrations.AddField(
            model_name='composetree',
            name='synced_content',
            field=models.ManyToManyField(to='repository.ContentCategory'),
        ),
        migrations.AddField(
            model_name='composetree',
            name='variant',
            field=models.ForeignKey(to='compose.Variant'),
        ),
        migrations.AlterUniqueTogether(
            name='composetree',
            unique_together=set([('compose', 'variant', 'arch', 'location')]),
        ),
    ]
