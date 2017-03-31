#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
"""
Extra Django settings for test environment of pdc project.
"""

from settings import *


# Database settings
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'test.sqlite3',
        'USER': '',
        'PASSWORD': '',
        'HOST': '',
        'PORT': '',
    }
}

# disable PERMISSION while testing
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'pdc.apps.auth.authentication.TokenAuthenticationWithChangeSet',
        'rest_framework.authentication.SessionAuthentication',
    ),

#    'DEFAULT_PERMISSION_CLASSES': [
#        'rest_framework.permissions.DjangoModelPermissions'
#    ],

    'DEFAULT_FILTER_BACKENDS': ('rest_framework.filters.DjangoFilterBackend',
                                'rest_framework.filters.OrderingFilter'),

    'DEFAULT_METADATA_CLASS': 'contrib.bulk_operations.metadata.BulkMetadata',

    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
        'pdc.apps.common.renderers.ReadOnlyBrowsableAPIRenderer',
    ),

    'EXCEPTION_HANDLER': 'pdc.apps.common.handlers.exception_handler',

    'DEFAULT_PAGINATION_CLASS': 'pdc.apps.common.pagination.AutoDetectedPageNumberPagination',

    'NON_FIELD_ERRORS_KEY': 'detail',
}

COMPONENT_BRANCH_NAME_BLACKLIST_REGEX = r'^epel\d+$'
