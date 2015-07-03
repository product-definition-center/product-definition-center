# -*- coding: utf-8 -*-
#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
from django.contrib import admin

from .models import Maillist, ContactRole, Contact, Person, RoleContact


class MaillistAdmin(admin.ModelAdmin):
    list_display = ('mail_name', 'email')
    search_fields = ['mail_name', 'email']
    list_filter = ('mail_name', )


class PersonAdmin(admin.ModelAdmin):
    list_display = ('username', 'email')
    search_fields = ['username', 'email']
    list_filter = ('username', )


class ContactRoleAdmin(admin.ModelAdmin):
    list_display = ('name', )
    search_fields = ['name']


class RoleContactAdmin(admin.ModelAdmin):
    list_display = ('contact_role', 'contact')
    search_fields = ['contact_role', 'contact']


admin.site.register(Maillist, MaillistAdmin)
admin.site.register(Person, PersonAdmin)
admin.site.register(ContactRole, ContactRoleAdmin)
admin.site.register(Contact)
admin.site.register(RoleContact, RoleContactAdmin)
