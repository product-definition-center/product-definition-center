# -*- coding: utf-8 -*-
#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#

from . import views
from pdc.apps.utils.SortedRouter import router


# TODO: these two end-points will be removed
router.register(r'persons', views.PersonViewSet, base_name='persondeprecated')
router.register(r'maillists', views.MaillistViewSet, base_name='maillistdeprecated')
router.register(r'contacts/people', views.PersonViewSet, base_name='person')
router.register(r'contacts/mailing-lists', views.MaillistViewSet, base_name='maillist')
router.register(r'contact-roles', views.ContactRoleViewSet)
router.register(r'role-contacts', views.RoleContactViewSet)
