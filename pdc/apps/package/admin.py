#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
from django.contrib import admin

from . import models


# Register your models here.
class RPMAdmin(admin.ModelAdmin):
    list_display = ('name', 'epoch', 'version', 'release', 'arch',
                    'srpm_name', 'srpm_nevra')
    search_fields = ['name', 'version', 'relase', 'arch']
    list_filter = ('name', )


class BuildImageAdmin(admin.ModelAdmin):
    list_display = ('image_id', 'md5', 'image_format')
    search_fields = ['image_id', 'image_format']
    list_filter = ('image_format', )


class ArchiveAdmin(admin.ModelAdmin):
    list_display = ('build_nvr', 'name', 'size', 'md5')
    search_fields = ['build_nvr', 'name']


admin.site.register(models.RPM, RPMAdmin)
admin.site.register(models.BuildImage, BuildImageAdmin)
admin.site.register(models.Archive, ArchiveAdmin)
admin.site.register(models.Image)
admin.site.register(models.ImageType)
admin.site.register(models.ImageFormat)
admin.site.register(models.ReleasedFiles)
