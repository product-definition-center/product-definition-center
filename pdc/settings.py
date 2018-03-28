#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
"""
Django settings for pdc project.
"""

from settings_common import *

# Attempts to import server specific settings.
# Note that all server specific settings should go to 'settings_local.py'
try:
    from settings_local import *  # noqa
except ImportError:
    pass

if DEBUG and DEBUG_TOOLBAR:
    INTERNAL_IPS = ('127.0.0.1',)
    # Profiling panel requires debug toolbar to be the first middleware class.
    MIDDLEWARE = ['debug_toolbar.middleware.DebugToolbarMiddleware',] + MIDDLEWARE
    INSTALLED_APPS += ('debug_toolbar',)

# Verbose logging in DEBUG mode.
if DEBUG:
    LOGGING['loggers']['pdc']['level'] = 'DEBUG'
