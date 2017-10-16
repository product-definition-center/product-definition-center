# -*- coding: utf-8 -*-
#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
from django.contrib.auth.models import PermissionsMixin, UserManager, AbstractBaseUser
from django.db import models
from django.core import validators
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone
from django.core.mail import send_mail
from django.contrib.auth.models import Group


MAX_LENGTH = 255


class User(AbstractBaseUser, PermissionsMixin):
    """
    Copied from django.contrib.auth.models.AbstractUser.
    The only change performed is increasing maximum length of user name and
    allowing / in it.
    """
    username = models.CharField(
        _('username'),
        max_length=MAX_LENGTH,
        unique=True,
        help_text=_('Required. %s characters or fewer. Letters, digits and @/./+/-/_ or / only.') % MAX_LENGTH,
        validators=[
            validators.RegexValidator(
                r'^[\w.@+-/]+$',
                _('Enter a valid username. This value may contain only '
                  'letters, numbers ' 'and @/./+/-/_ or / characters.')
            ),
        ],
        error_messages={
            'unique': _("A user with that username already exists."),
        },
    )
    full_name = models.CharField(_('full name'), max_length=80, blank=True)
    email = models.EmailField(_('email address'), blank=True)
    is_staff = models.BooleanField(
        _('staff status'),
        default=False,
        help_text=_('Designates whether the user can log into this admin site.'),
    )
    is_active = models.BooleanField(
        _('active'),
        default=True,
        help_text=_(
            'Designates whether this user should be treated as active. '
            'Unselect this instead of deleting accounts.'
        ),
    )
    date_joined = models.DateTimeField(_('date joined'), default=timezone.now)
    last_connected = models.DateTimeField(_('date last connected to service'), blank=True, null=True)

    objects = UserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')

    def get_full_name(self):
        """
        Returns the full name for the user.
        """
        return self.full_name

    def get_short_name(self):
        """
        Returns full name as short name for the user.
        """
        return self.full_name

    def email_user(self, subject, message, from_email=None, **kwargs):
        """
        Sends an email to this User.
        """
        send_mail(subject, message, from_email, [self.email], **kwargs)

    def get_all_permissions(self, obj=None):
        return sorted(super(User, self).get_all_permissions(obj))


class Resource(models.Model):
    """
    Resource permissions
    """
    name = models.CharField(max_length=500, unique=True)
    view = models.CharField(max_length=1000)

    def __unicode__(self):
        return u'%s %s' % (self.name, self.view)

    def export(self, fields=None):
        return {'name': self.name,
                'view': self.view}


class ActionPermission(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ("name", )

    def __unicode__(self):
        return u'%s' % self.name

    def export(self, fields=None):
        return {'name': self.name}


class ResourcePermission(models.Model):
    resource = models.ForeignKey(Resource)
    permission = models.ForeignKey(ActionPermission)

    class Meta:
        ordering = ("resource__name", "permission__name")
        unique_together = [
            ('resource', 'permission')
        ]

    def __unicode__(self):
        return u"%s %s" % (self.resource, self.permission)

    def export(self):
        return {
            "resource": self.resource,
            "permission": self.permission,
        }


class GroupResourcePermission(models.Model):
    resource_permission = models.ForeignKey(ResourcePermission)
    group = models.ForeignKey(Group)

    class Meta:
        ordering = ("group__name", "resource_permission__resource__name", "resource_permission__permission__name")
        unique_together = [
            ('resource_permission', 'group')
        ]

    def __unicode__(self):
        return u"(%s) %s" % (self.resource_permission, self.group)

    def export(self):
        return {
            "resource_permission": str(self.resource_permission),
            "group": self.group.name,
        }


class ResourceApiUrl(models.Model):
    """
    API documentation URLs for resources
    """
    resource = models.OneToOneField(
        Resource, related_name='api_url', on_delete=models.CASCADE)
    url = models.URLField(max_length=255, blank=True)

    class Meta:
        ordering = ("resource__name",)

    def __unicode__(self):
        return u"%s %s" % (self.resource, self.url)

    def export(self):
        return {
            "resource": self.resource.name,
            "url": self.url,
        }
