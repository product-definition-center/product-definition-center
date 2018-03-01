#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
"""
Extra Django settings for test environment of pdc project.
"""

from settings_common import *


# Database settings
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'test.sqlite3',
        'TEST': {'NAME': 'test.sqlite3'},
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

    'DEFAULT_FILTER_BACKENDS': ('django_filters.rest_framework.DjangoFilterBackend',
                                'pdc.apps.utils.utils.RelatedNestedOrderingFilter'),

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
DISABLE_RESOURCE_PERMISSION_CHECK = True
SKIP_RESOURCE_CREATION = True

MESSAGE_BUS = {
    'MLP': 'test'
}
RELEASE_DEFAULT_SIGKEY = "ABCDEF"
ALLOWED_HOSTS = ['*']
