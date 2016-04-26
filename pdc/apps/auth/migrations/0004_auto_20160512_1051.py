# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def create_action(apps, schema_editor):
    action_permission = apps.get_model('kerb_auth', 'ActionPermission')
    for action in ('create', 'read', 'update', 'delete'):
        action_permission.objects.create(name=action)

class Migration(migrations.Migration):

    dependencies = [
        ('kerb_auth', '0003_auto_20151126_0811'),
    ]

    operations = [
        migrations.CreateModel(
            name='ActionPermission',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='GroupResourcePermission',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('group', models.ForeignKey(to='auth.Group')),
            ],
        ),
        migrations.CreateModel(
            name='Resource',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=500)),
                ('view', models.CharField(max_length=1000)),
            ],
        ),
        migrations.CreateModel(
            name='ResourcePermission',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('permission', models.ForeignKey(to='kerb_auth.ActionPermission')),
                ('resource', models.ForeignKey(to='kerb_auth.Resource')),
            ],
        ),
        migrations.AddField(
            model_name='groupresourcepermission',
            name='resource_permission',
            field=models.ForeignKey(to='kerb_auth.ResourcePermission'),
        ),
        migrations.RunPython(create_action)
    ]
