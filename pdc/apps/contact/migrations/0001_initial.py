# -*- coding: utf-8 -*-
#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='Contact',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('active', models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name='ContactRole',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=128)),
            ],
        ),
        migrations.CreateModel(
            name='RoleContact',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
            ],
        ),
        migrations.CreateModel(
            name='Maillist',
            fields=[
                ('contact', models.OneToOneField(parent_link=True, related_name='maillist', primary_key=True, serialize=False, to='contact.Contact')),
                ('mail_name', models.CharField(unique=True, max_length=128, db_index=True)),
                ('email', models.EmailField(max_length=254)),
            ],
            bases=('contact.contact',),
        ),
        migrations.CreateModel(
            name='Person',
            fields=[
                ('contact', models.OneToOneField(parent_link=True, related_name='person', primary_key=True, serialize=False, to='contact.Contact')),
                ('username', models.CharField(unique=True, max_length=128, db_index=True)),
                ('email', models.EmailField(max_length=254)),
            ],
            bases=('contact.contact',),
        ),
        migrations.AddField(
            model_name='rolecontact',
            name='contact',
            field=models.ForeignKey(related_name='role_contacts', on_delete=django.db.models.deletion.PROTECT, to='contact.Contact'),
        ),
        migrations.AddField(
            model_name='rolecontact',
            name='contact_role',
            field=models.ForeignKey(related_name='role_contacts', on_delete=django.db.models.deletion.PROTECT, to='contact.ContactRole'),
        ),
        migrations.AddField(
            model_name='contact',
            name='content_type',
            field=models.ForeignKey(editable=False, to='contenttypes.ContentType', null=True),
        ),
        migrations.AlterUniqueTogether(
            name='rolecontact',
            unique_together=set([('contact', 'contact_role')]),
        ),
    ]
