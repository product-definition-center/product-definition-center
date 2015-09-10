# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('component', '0009_releasecomponenttype_has_osbs'),
        ('contact', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='GlobalComponentRoleContact',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('component', models.ForeignKey(related_name='global_component_role_contacts', on_delete=django.db.models.deletion.PROTECT, to='component.GlobalComponent')),
                ('contact', models.ForeignKey(related_name='global_component_role_contacts', on_delete=django.db.models.deletion.PROTECT, to='contact.Contact')),
                ('contact_role', models.ForeignKey(related_name='global_component_role_contacts', on_delete=django.db.models.deletion.PROTECT, to='contact.ContactRole')),
            ],
        ),
        migrations.CreateModel(
            name='ReleaseComponentRoleContact',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('component', models.ForeignKey(related_name='release_component_role_contacts', on_delete=django.db.models.deletion.PROTECT, to='component.ReleaseComponent')),
                ('contact', models.ForeignKey(related_name='release_component_role_contacts', on_delete=django.db.models.deletion.PROTECT, to='contact.Contact')),
                ('contact_role', models.ForeignKey(related_name='release_component_role_contacts', on_delete=django.db.models.deletion.PROTECT, to='contact.ContactRole')),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='releasecomponentrolecontact',
            unique_together=set([('contact', 'contact_role', 'component')]),
        ),
        migrations.AlterUniqueTogether(
            name='globalcomponentrolecontact',
            unique_together=set([('contact', 'contact_role', 'component')]),
        ),
    ]
