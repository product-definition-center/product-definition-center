# -*- coding: utf-8 -*-
#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#

from . import views
from pdc.apps.utils.SortedRouter import router


router.register(r'contacts/people', views.PersonViewSet, base_name='person')
router.register(r'contacts/mailing-lists', views.MaillistViewSet, base_name='maillist')
router.register(r'contact-roles', views.ContactRoleViewSet)
router.register(r'global-component-contacts',
                views.GlobalComponentContactViewSet,
                base_name='globalcomponentcontacts')
router.register(r'release-component-contacts',
                views.ReleaseComponentContactViewSet,
                base_name='releasecomponentcontacts')
