# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('contact', '0002_auto_20151001_1239'),
    ]

    operations = [
        migrations.AlterField(
            model_name='globalcomponentrolecontact',
            name='component',
            field=models.ForeignKey(to='component.GlobalComponent', on_delete=django.db.models.deletion.PROTECT),
        ),
        migrations.AlterField(
            model_name='globalcomponentrolecontact',
            name='contact',
            field=models.ForeignKey(to='contact.Contact', on_delete=django.db.models.deletion.PROTECT),
        ),
        migrations.AlterField(
            model_name='globalcomponentrolecontact',
            name='contact_role',
            field=models.ForeignKey(to='contact.ContactRole', on_delete=django.db.models.deletion.PROTECT),
        ),
        migrations.AlterField(
            model_name='releasecomponentrolecontact',
            name='component',
            field=models.ForeignKey(to='component.ReleaseComponent', on_delete=django.db.models.deletion.PROTECT),
        ),
        migrations.AlterField(
            model_name='releasecomponentrolecontact',
            name='contact',
            field=models.ForeignKey(to='contact.Contact', on_delete=django.db.models.deletion.PROTECT),
        ),
        migrations.AlterField(
            model_name='releasecomponentrolecontact',
            name='contact_role',
            field=models.ForeignKey(to='contact.ContactRole', on_delete=django.db.models.deletion.PROTECT),
        ),
        migrations.AlterUniqueTogether(
            name='globalcomponentrolecontact',
            unique_together=set([('contact_role', 'component')]),
        ),
        migrations.AlterUniqueTogether(
            name='releasecomponentrolecontact',
            unique_together=set([('contact_role', 'component')]),
        ),
        migrations.RenameField(
            model_name='globalcomponentrolecontact',
            old_name='contact_role',
            new_name='role',
        ),
        migrations.RenameField(
            model_name='releasecomponentrolecontact',
            old_name='contact_role',
            new_name='role',
        ),
        migrations.AlterUniqueTogether(
            name='globalcomponentrolecontact',
            unique_together=set([('role', 'component')]),
        ),
        migrations.AlterUniqueTogether(
            name='releasecomponentrolecontact',
            unique_together=set([('role', 'component')]),
        ),
        migrations.RenameModel(
            old_name='ReleaseComponentRoleContact',
            new_name='GlobalComponentContact',
        ),
        migrations.RenameModel(
            old_name='GlobalComponentRoleContact',
            new_name='ReleaseComponentContact',
        ),
        migrations.AlterField(
            model_name='globalcomponentcontact',
            name='component',
            field=models.ForeignKey(to='component.GlobalComponent', on_delete=django.db.models.deletion.PROTECT),
        ),
        migrations.AlterField(
            model_name='releasecomponentcontact',
            name='component',
            field=models.ForeignKey(to='component.ReleaseComponent', on_delete=django.db.models.deletion.PROTECT),
        ),
    ]
