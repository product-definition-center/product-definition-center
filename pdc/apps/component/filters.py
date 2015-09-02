# -*- coding: utf-8 -*-
#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
import collections

from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.forms import SelectMultiple

from django_filters import FilterSet, MethodFilter, CharFilter

from .models import (GlobalComponent,
                     ReleaseComponent,
                     BugzillaComponent,
                     ReleaseComponentGroup,
                     GroupType,
                     ReleaseComponentRelationship)
from pdc.apps.contact.models import (Person,
                                     Maillist,
                                     ContactRole,
                                     RoleContact)
from pdc.apps.common.filters import (ComposeFilterSet,
                                     value_is_not_empty,
                                     MultiValueFilter,
                                     CaseInsensitiveBooleanFilter)


class RoleContactFilter(FilterSet):
    contact_role = MethodFilter(action='filter_contact_role',
                                widget=SelectMultiple)
    email = MethodFilter(action='filter_email',
                         widget=SelectMultiple)
    username = MethodFilter(action='filter_username',
                            widget=SelectMultiple)
    mail_name = MethodFilter(action='filter_mail_name',
                             widget=SelectMultiple)

    @value_is_not_empty
    def filter_contact_role(self, qs, value):
        if isinstance(value, collections.Iterable):
            return qs.filter(contact_role__name__in=value)
        else:
            return qs.filter(contact_role__name=value)

    @value_is_not_empty
    def filter_email(self, qs, value):
        person_type = ContentType.objects.get_for_model(Person)
        mail_type = ContentType.objects.get_for_model(Maillist)

        persons = person_type.get_all_objects_for_this_type(email__in=value)
        mails = mail_type.get_all_objects_for_this_type(email__in=value)

        if not persons.exists() and mails.exists():
            return qs.filter(contact__in=mails)

        elif not mails.exists() and persons.exists():
            return qs.filter(contact__in=persons)

        else:
            return qs.filter(Q(contact__in=persons) | Q(
                contact__in=mails))

    @value_is_not_empty
    def filter_username(self, qs, value):
        person_type = ContentType.objects.get_for_model(Person)
        persons = person_type.get_all_objects_for_this_type(
            username__in=value)
        return qs.filter(contact__in=persons)

    @value_is_not_empty
    def filter_mail_name(self, qs, value):
        mail_type = ContentType.objects.get_for_model(Maillist)
        mails = mail_type.get_all_objects_for_this_type(mail_name__in=value)
        return qs.filter(contact__in=mails)

    class Meta:
        model = RoleContact
        fields = ('contact_role', 'email', 'username', 'mail_name')


class ComponentFilter(ComposeFilterSet):
    name = MultiValueFilter()
    dist_git_path = MultiValueFilter()
    contact_role = email = MethodFilter(action='filter_together', widget=SelectMultiple)
    label = MultiValueFilter(name='labels__name', distinct=True)
    upstream_homepage = MultiValueFilter(name='upstream__homepage')
    upstream_scm_type = MultiValueFilter(name='upstream__scm_type')
    upstream_scm_url = MultiValueFilter(name='upstream__scm_url')

    @value_is_not_empty
    def filter_together(self, qs, value):
        email_str = self.data.get('email', None)
        email = [email_str] if email_str else []

        contact_role_str = self.data.get('contact_role', None)
        contact_role = [contact_role_str] if contact_role_str else []

        if email:
            person_type = ContentType.objects.get_for_model(Person)
            mail_type = ContentType.objects.get_for_model(Maillist)
            persons = person_type.get_all_objects_for_this_type(email__in=email)
            mails = mail_type.get_all_objects_for_this_type(email__in=email)

            if not contact_role:
                if not persons.exists() and mails.exists():
                    return qs.filter(contacts__contact__in=mails).distinct()

                elif not mails.exists() and persons.exists():
                    return qs.filter(contacts__contact__in=persons).distinct()

                else:
                    return qs.filter(Q(contacts__object_id__in=persons) | Q(
                        contacts__object_id__in=mails)).distinct()
            else:
                if not persons.exists() and mails.exists():
                    contacts = RoleContact.objects.filter(contact__in=mails,
                                                          contact_role__name__in=contact_role)

                elif not mails.exists() and persons.exists():
                    contacts = RoleContact.objects.filter(contact__in=persons,
                                                          contact_role__name__in=contact_role)

                else:
                    contacts = RoleContact.objects.filter(
                        Q(contact__in=persons) | Q(contact__in=mails),
                        contact_role__name__in=contact_role)

                return qs.filter(contacts=contacts).distinct()

        else:
            return qs

    class Meta:
        model = GlobalComponent
        fields = ('name', 'dist_git_path', 'email', 'contact_role', 'label',
                  'upstream_homepage', 'upstream_scm_type', 'upstream_scm_url')


class ReleaseComponentFilter(ComposeFilterSet):
    name = MultiValueFilter()
    release = MultiValueFilter(name='release__release_id')
    global_component = MultiValueFilter(name='global_component__name')
    contact_role = email = MethodFilter(action='filter_together',
                                        widget=SelectMultiple)
    bugzilla_component = MultiValueFilter(name='bugzilla_component__name')
    brew_package = MultiValueFilter()
    active = CaseInsensitiveBooleanFilter()
    type = CharFilter(name='type__name')

    @value_is_not_empty
    def filter_together(self, qs, value):
        email_str = self.data.get('email', None)
        email = [email_str] if email_str else []

        contact_role_str = self.data.get('contact_role', None)
        contact_role = [contact_role_str] if contact_role_str else []

        if email:
            person_type = ContentType.objects.get_for_model(Person)
            mail_type = ContentType.objects.get_for_model(Maillist)
            persons = person_type.get_all_objects_for_this_type(email__in=email)
            mails = mail_type.get_all_objects_for_this_type(email__in=email)

            if not persons.exists() and not mails.exists():
                return qs.none()

            if not contact_role:

                contact_Q = Q()
                if persons.exists():
                    contact_Q |= Q(contact__in=persons, )
                if mails.exists():
                    contact_Q |= Q(contact__in=mails, )
                contacts = RoleContact.objects.filter(contact_Q)

                qs = qs.filter(
                    Q(contacts__in=contacts) |
                    Q(global_component__contacts__in=contacts)
                )

                qs = qs.distinct()
            else:
                contact_roles = ContactRole.objects.filter(
                    name__in=contact_role)

                contact_Q = Q()
                if persons.exists():
                    contact_Q |= Q(contact__in=persons, )
                if mails.exists():
                    contact_Q |= Q(contact__in=mails, )
                contacts = RoleContact.objects.filter(contact_Q)

                qs = qs.filter(
                    (Q(
                        contacts__contact_role__in=contact_roles) & Q(
                        contacts__in=contacts)) |
                    (Q(
                        global_component__contacts__contact_role__in=contact_roles) & Q(
                        global_component__contacts__in=contacts))
                )

                qs = qs.distinct()

            # NOTE: For the PDC-184, if a release component has the same
            # contact type as global component contacts, it will overwrite
            # the global component contact and show in the output json string.
            # ----------------------------------------------------------------
            # |  Global Component Contacts   |   Release Component Contacts  |
            # ----------------------------------------------------------------
            # |  QE_Leader, A@example.com    |   N/A                         |
            # |  QE_ACK, B@example.com       |   QE_ACK, NEW@example.com     |
            # |  QE_Group, C@example.com     |   N/A                         |
            # ----------------------------------------------------------------
            #
            # if we filter the release component with email=B@example.com,
            # there is no result here, because B@example.com is overwrited by
            # release component's QE_ACK.
            #
            # ----------------------------------------------------------------
            # |  Global Component Contacts   |   Release Component Contacts  |
            # ----------------------------------------------------------------
            # |  QE_Leader, B@example.com    |   N/A                         |
            # |  QE_ACK, B@example.com       |   QE_ACK, NEW@example.com     |
            # |  QE_Group, C@example.com     |   N/A                         |
            # ----------------------------------------------------------------
            #
            # if we filter this one with email=B@rehdat.com, the result will
            # include this one, because QE_Leader is not overwrited.
            #
            # Here is a hack for the current implementation, and it is not a
            # good way to resolve RHBZ-1181932.
            #
            # Maybe we could use database view to filter it with SQL.
            id_include_inherited = []
            for release_component in qs.iterator():
                release_contacts = release_component.contacts.filter(
                    contact_role__in=set(contacts.values_list('contact_role', flat=True)))
                global_contacts = release_component.global_component.contacts.filter(
                    id__in=[obj.id for obj in contacts])

                if release_contacts.exists() and global_contacts.exists():
                    release_contact_roles = set([contact.contact_role for contact in release_contacts])
                    global_contact_roles = set([contact.contact_role for contact in global_contacts])

                    if global_contact_roles - release_contact_roles:
                        id_include_inherited.append(release_component.id)
                else:
                    id_include_inherited.append(release_component.id)

            return ReleaseComponent.objects.filter(pk__in=id_include_inherited)
        else:
            return qs

    class Meta:
        model = ReleaseComponent
        fields = ('name', 'release', 'email', 'contact_role', 'global_component', 'active',
                  'bugzilla_component', 'type')


class BugzillaComponentFilter(ComposeFilterSet):
    name = MultiValueFilter()
    parent_component = MultiValueFilter(name='parent_component__name')

    class Meta:
        model = BugzillaComponent
        fields = ('name', 'parent_component')


class GroupTypeFilter(ComposeFilterSet):
    name = MultiValueFilter()

    class Meta:
        model = GroupType
        fields = ('name',)


class GroupFilter(ComposeFilterSet):
    group_type = MultiValueFilter(name='group_type__name')
    release = MultiValueFilter(name='release__release_id')
    release_component = MultiValueFilter(name='components__name', distinct=True)

    class Meta:
        model = ReleaseComponentGroup
        fields = ('group_type', 'release', 'release_component')


class ReleaseComponentRelationshipFilter(ComposeFilterSet):
    type = MultiValueFilter(name='relation_type__name')
    from_component_release = MultiValueFilter(name='from_component__release__release_id')
    from_component_name = MultiValueFilter(name='from_component__name')
    to_component_release = MultiValueFilter(name='to_component__release__release_id')
    to_component_name = MultiValueFilter(name='to_component__name')

    class Meta:
        model = ReleaseComponentRelationship
        fields = ('type', 'from_component_release', 'from_component_name', 'to_component_release',
                  'to_component_name')
