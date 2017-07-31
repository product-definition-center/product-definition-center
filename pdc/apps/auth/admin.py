# -*- coding: utf-8 -*-
#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
from django.contrib import admin

from . import models


class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'last_connected')


admin.site.register(models.User, UserAdmin)
admin.site.register(models.Resource)
admin.site.register(models.ResourcePermission)
admin.site.register(models.ResourceApiUrl)
