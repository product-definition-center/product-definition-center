# -*- coding: utf-8 -*-
#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models.query import QuerySet
from django.db.models import Count
from django.forms.models import model_to_dict
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _


class ContactRole(models.Model):

    name = models.CharField(max_length=128, unique=True)
    count_limit = models.PositiveSmallIntegerField(
        default=1,
        help_text=_('Contact count limit of the role for each component.')
    )
    UNLIMITED = 0

    def _get_max_component_role_count(self, component_model, role):
        if not component_model.objects.filter(role=role).exists():
            return 0
        return component_model.objects.filter(role=role).values("component_id").annotate(contact_count=Count('id')).\
            order_by('-contact_count')[0]['contact_count']

    def clean(self):
        # don't need to do such check if count_limit set to UNLIMITED
        if self.count_limit == ContactRole.UNLIMITED:
            return
        if self.pk:
            role = ContactRole.objects.get(pk=self.pk)
            old_limit = role.count_limit
            # must check when decrease count limit
            if old_limit == ContactRole.UNLIMITED or self.count_limit < old_limit:
                rc_max_count = self._get_max_component_role_count(ReleaseComponentContact, role)
                gc_max_count = self._get_max_component_role_count(GlobalComponentContact, role)
                if self.count_limit < max(rc_max_count, gc_max_count):
                    raise ValidationError(
                        {'detail': 'Count limit can\'t be lower than %d according to existing data.' %
                                   max(rc_max_count, gc_max_count)})

    def __unicode__(self):
        return u"%s" % self.name

    def export(self, fields=None):
        _fields = ['name', 'count_limit'] if fields is None else fields
        return model_to_dict(self, fields=_fields)


# https://djangosnippets.org/snippets/1034/
class SubclassingQuerySet(QuerySet):
    def __getitem__(self, k):
        result = super(SubclassingQuerySet, self).__getitem__(k)
        if isinstance(result, models.Model):
            return result.as_leaf_class()
        else:
            return result

    def __iter__(self):
        for item in super(SubclassingQuerySet, self).__iter__():
            yield item.as_leaf_class()


class ContactManager(models.Manager):
    def get_queryset(self):
        return SubclassingQuerySet(self.model)


class Contact(models.Model):
    content_type = models.ForeignKey(ContentType, editable=False, null=True, on_delete=models.CASCADE)
    active       = models.BooleanField(default=True)

    objects = ContactManager()

    def __unicode__(self):
        return u"%s" % self.as_leaf_class()

    def export(self, *args, **kwargs):
        return self.as_leaf_class().export()

    def save(self, *args, **kwargs):
        if not self.content_type:
            self.content_type = ContentType.objects.get_for_model(self.__class__)
        super(Contact, self).save(*args, **kwargs)

    def as_leaf_class(self):
        content_type = self.content_type
        model = content_type.model_class()
        if model == Contact:
            return self
        return model.objects.get(id=self.id)


class Person(Contact):
    """
    Person as Contact.
    """
    contact = models.OneToOneField(Contact, related_name="person", parent_link=True, on_delete=models.CASCADE)
    username = models.CharField(max_length=128, db_index=True, unique=True)
    email       = models.EmailField()

    objects = ContactManager()

    def __unicode__(self):
        return u"%s(%s)" % (self.username, self.email)

    def export(self, fields=None):
        _fields = ['username', 'email'] if fields is None else fields
        return model_to_dict(self, fields=_fields)


class Maillist(Contact):
    """
    Maillist as Contact.
    """
    contact   = models.OneToOneField(Contact, related_name="maillist", parent_link=True, on_delete=models.CASCADE)
    mail_name = models.CharField(max_length=128, db_index=True, unique=True)
    email     = models.EmailField()

    objects = ContactManager()

    def __unicode__(self):
        return u"%s(%s)" % (self.mail_name, self.email)

    def export(self, fields=None):
        _fields = ['mail_name', 'email'] if fields is None else fields
        return model_to_dict(self, fields=_fields)


class ValidateRoleCountMixin(object):

    def clean(self):
        if self.role.count_limit != ContactRole.UNLIMITED:
            q = type(self).objects.filter(component=self.component, role=self.role)
            if self.pk:
                q = q.exclude(pk=self.pk)
            if q.count() >= self.role.count_limit:
                raise ValidationError(
                    {'detail': 'Exceed contact role limit for the component. The limit is %d.' % self.role.count_limit})


class GlobalComponentContact(ValidateRoleCountMixin, models.Model):

    role      = models.ForeignKey(ContactRole, on_delete=models.PROTECT)
    contact   = models.ForeignKey(Contact, on_delete=models.PROTECT)
    component = models.ForeignKey('component.GlobalComponent',
                                  on_delete=models.PROTECT)

    def __unicode__(self):
        return u'%s: %s: %s' % (unicode(self.component), unicode(self.role), unicode(self.contact))

    class Meta:
        unique_together = (('role', 'component', 'contact'), )

    def export(self, fields=None):
        return {
            'contact': self.contact.export(fields=fields),
            'role': self.role.name,
            'component': self.component.name,
        }


class ReleaseComponentContact(ValidateRoleCountMixin, models.Model):

    role      = models.ForeignKey(ContactRole, on_delete=models.PROTECT)
    contact   = models.ForeignKey(Contact, on_delete=models.PROTECT)
    component = models.ForeignKey('component.ReleaseComponent',
                                  on_delete=models.PROTECT)

    def __unicode__(self):
        return u'%s: %s: %s' % (unicode(self.component), unicode(self.role), unicode(self.contact))

    class Meta:
        unique_together = (('role', 'component', 'contact'), )

    def export(self, fields=None):
        return {
            'contact': self.contact.export(fields=fields),
            'role': self.role.name,
            'component': self.component.name,
        }
