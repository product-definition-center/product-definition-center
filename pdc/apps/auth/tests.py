# -*- coding: utf-8 -*-
#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
import mock

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.core.urlresolvers import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from . import backends
from .models import Resource, ResourcePermission, GroupResourcePermission, ActionPermission
from pdc.apps.common.test_utils import TestCaseWithChangeSetMixin


class LDAPSyncTestCase(TestCase):
    def setUp(self):
        self.user_data = [('uid=jdoe,ou=users,dc=test,dc=com', {
            'uid': ['jdoe'],
            'mail': ['jdoe@test.com'],
            'givenName': ['Joe'],
            'sn': ['Doe'],
        })]
        self.group_data = []

        self.connection = mock.Mock()
        self.connection.search_s = lambda x, _1, _2, _3=None: self.user_data if 'users' in x else self.group_data

    def test_updates_attributes(self):
        self.group_data = [
            ('cn=test1,ou=Groups,dc=test,dc=com', {'cn': ['test1']}),
            ('cn=test2,ou=Groups,dc=test,dc=com', {'cn': ['test2']}),
        ]

        user = get_user_model().objects.create()
        user.username = 'jdoe'

        backends.update_user_from_ldap(user, self.connection)

        user = get_user_model().objects.get(username='jdoe')
        self.assertEqual(user.full_name, 'Joe Doe')
        self.assertEqual(user.email, 'jdoe@test.com')
        self.assertEqual(set(g.name for g in user.groups.all()), set(['test1', 'test2']))

    def test_does_not_set_user_group(self):
        self.group_data = [
            ('cn=test1,ou=Groups,dc=test,dc=com', {'cn': ['test1']}),
            ('cn=jdoe,ou=Groups,dc=test,dc=com', {'cn': ['jdoe']})
        ]

        user = get_user_model().objects.create()
        user.username = 'jdoe'

        backends.update_user_from_ldap(user, self.connection)

        groups = get_user_model().objects.get(username='jdoe').groups.all()
        self.assertEqual(set(g.name for g in groups), set(['test1']))


class TokenViewTestCase(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create(username='test', email='test@test.com', password='test')
        self.user.save()
        self.token = Token.objects.create(user=self.user)
        self.token.save()
        self.client.force_authenticate(user=self.user)

    def test_obtain_token(self):
        response = self.client.get(reverse('token-obtain'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {"token": "%s" % self.token.key})

    def test_obtain_token_fail(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(reverse('token-obtain'))

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_renew_token(self):
        response = self.client.get(reverse('token-refresh'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {"token": "%s" % Token.objects.get(user=self.user).key})

    def test_renew_token_401(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(reverse('token-refresh'))

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_renew_token_400(self):
        self.token.delete()
        response = self.client.get(reverse('token-refresh'))

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class GroupRESTTestCase(TestCaseWithChangeSetMixin, APITestCase):

    fixtures = [
        'pdc/apps/auth/fixtures/tests/groups.json',
    ]

    def test_create(self):
        url = reverse('group-list')
        data = {'name': 'new_group'}
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_get(self):
        url = reverse('group-detail', args=[1])
        response = self.client.get(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_list(self):
        url = reverse('group-list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 3)

    def test_query_with_name(self):
        url = reverse('group-list')
        response = self.client.get(url + '?name=group_add_group', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 1)

    def test_query_with_permission_model(self):
        url = reverse('group-list')
        response = self.client.get(url + '?permission_model=group', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 3)

    def test_query_with_permission_app_label(self):
        url = reverse('group-list')
        response = self.client.get(url + '?permission_app_label=auth', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 3)

    def test_query_with_permission_codename(self):
        url = reverse('group-list')
        response = self.client.get(url + '?permission_codename=add_group', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 1)

    def test_patch_update_permissions(self):
        url = reverse('group-detail', args=[1])
        data = {'permissions': [{'codename': 'change_group',
                                 'app_label': 'auth',
                                 'model': 'group'}]
                }
        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('permissions'), data.get('permissions'))

    def test_patch_update_group_should_record_in_changeset(self):
        url = reverse('group-detail', args=[1])
        data = {'permissions': [{'codename': 'change_group',
                                 'app_label': 'auth',
                                 'model': 'group'}]
                }
        self.client.patch(url, data, format='json')
        self.assertNumChanges([1])

    def test_patch_update_group_with_same_content_should_not_record_in_changeset(self):
        url = reverse('group-detail', args=[1])
        data = {'permissions': [{'codename': 'add_group',
                                 'app_label': 'auth',
                                 'model': 'group'}]
                }
        self.client.patch(url, data, format='json')
        self.assertNumChanges([])

    def test_update_404(self):
        url = reverse('group-detail', args=[9])
        data = {'name': 'new_group',
                'permissions': [{'codename': 'change_group',
                                 'app_label': 'auth',
                                 'model': 'group'}]
                }
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_partial_update_empty(self):
        url = reverse('group-detail', args=[2])
        response = self.client.patch(url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_put_update_empty(self):
        url = reverse('group-detail', args=[2])
        response = self.client.put(url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_put_update(self):
        url = reverse('group-detail', args=[1])
        data = {'name': 'new_group',
                'permissions': [{'codename': 'change_group',
                                 'app_label': 'auth',
                                 'model': 'group'}]
                }
        response = self.client.put(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('name'), data.get('name'))
        self.assertEqual(response.data.get('permissions'), data.get('permissions'))

    def test_put_update_only_name(self):
        url = reverse('group-detail', args=[1])
        data = {'name': 'new_group'}
        response = self.client.put(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'permissions': [u'This field is required.']})

    def test_put_update_only_permission(self):
        url = reverse('group-detail', args=[1])
        data = {'permissions': [{'codename': 'change_group',
                                 'app_label': 'auth',
                                 'model': 'group'}]
                }
        response = self.client.put(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'name': [u'This field is required.']})

    def test_delete(self):
        url = reverse('group-detail', args=[1])
        response = self.client.delete(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


class CurrentUserTestCase(APITestCase):
    fixtures = [
        'pdc/apps/auth/fixtures/tests/groups.json',
    ]

    def setUp(self):
        self.user = get_user_model().objects.create(username='alice',
                                                    email='alice@example.com',
                                                    full_name='Alice von Test')
        self.user.save()

    def test_can_access_data_authorized(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(reverse('currentuser-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('username'), 'alice')
        self.assertEqual(response.data.get('fullname'), 'Alice von Test')
        self.assertEqual(response.data.get('groups'), [])
        self.assertEqual(response.data.get('permissions'), [])

    def test_can_not_access_without_authentication(self):
        response = self.client.get(reverse('currentuser-list'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_can_view_user_permissions(self):
        p = Group.objects.get(pk=1).permissions.first()
        self.user.user_permissions.add(p)
        self.client.force_authenticate(user=self.user)
        response = self.client.get(reverse('currentuser-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertItemsEqual(response.data['permissions'], ['auth.add_group'])

    def test_can_view_groups(self):
        Group.objects.get(pk=1).user_set.add(self.user)
        self.client.force_authenticate(user=self.user)
        response = self.client.get(reverse('currentuser-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertItemsEqual(response.data['groups'], ['group_add_group'])
        self.assertItemsEqual(response.data['permissions'], ['auth.add_group'])

    def test_permissions_sorted(self):
        change_group = Group.objects.get(pk=2).permissions.first()
        add_group = Group.objects.get(pk=1).permissions.first()
        delete_group = Group.objects.get(pk=3).permissions.first()
        self.user.user_permissions.add(delete_group)
        self.user.user_permissions.add(change_group)
        self.user.user_permissions.add(add_group)
        self.client.force_authenticate(user=self.user)
        response = self.client.get(reverse('currentuser-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['permissions'], sorted(response.data['permissions']))

    def test_resource_permissions(self):
        self.client.force_authenticate(user=self.user)
        for permission in Permission.objects.all():
            self.user.user_permissions.add(permission)

        for name, view in (("group-resource-permissions",
                            "<class 'pdc.apps.auth.views.GroupResourcePermissionViewSet'>"),
                           ("release-components", "<class 'pdc.apps.component.views.ReleaseComponentViewSet'>"),
                           ("rpc/find-compose-by-release-rpm/(?P<release_id>[^/]+)/(?P<rpm_name>[^/]+)",
                            "<class 'pdc.apps.compose.views.FindComposeByReleaseRPMViewSet'>")):
            Resource.objects.create(name=name, view=view)
        for resource in Resource.objects.all():
            for permission in ActionPermission.objects.all():
                ResourcePermission.objects.create(resource=resource, permission=permission)

        group = Group.objects.get(pk=1)
        for per in ResourcePermission.objects.all():
                GroupResourcePermission.objects.create(group=group, resource_permission=per)

        self.group = group.user_set.add(self.user)
        response = self.client.get(reverse('currentuser-list'), format='json')
        self.assertEqual(len(response.data['resource_permissions']), 3 * 4)
        self.assertTrue({'resource': 'rpc/find-compose-by-release-rpm/(?P<release_id>[^/]+)/(?P<rpm_name>[^/]+)',
                         'permission': 'create'} in response.data['resource_permissions'])

    def test_resource_permission_all_read_permissions_on(self):
        temp = False
        if hasattr(settings, 'ALLOW_ALL_USER_READ'):
            temp = settings.ALLOW_ALL_USER_READ

        self.client.force_authenticate(user=self.user)
        for permission in Permission.objects.all():
            self.user.user_permissions.add(permission)

        for name, view in (("group-resource-permissions",
                            "<class 'pdc.apps.auth.views.GroupResourcePermissionViewSet'>"),
                           ("release-components", "<class 'pdc.apps.component.views.ReleaseComponentViewSet'>"),
                           ("rpc/find-compose-by-release-rpm/(?P<release_id>[^/]+)/(?P<rpm_name>[^/]+)",
                            "<class 'pdc.apps.compose.views.FindComposeByReleaseRPMViewSet'>")):
            Resource.objects.create(name=name, view=view)
        for resource in Resource.objects.all():
            for permission in ActionPermission.objects.all():
                ResourcePermission.objects.create(resource=resource, permission=permission)

        settings.ALLOW_ALL_USER_READ = False
        response = self.client.get(reverse('currentuser-list'), format='json')
        self.assertEqual(len(response.data['resource_permissions']), 0)

        settings.ALLOW_ALL_USER_READ = True
        response = self.client.get(reverse('currentuser-list'), format='json')
        self.assertEqual(len(response.data['resource_permissions']), 3)

        settings.ALLOW_ALL_USER_READ = temp


class GroupResourcePermissionsTestCase(APITestCase):
    fixtures = [
        'pdc/apps/auth/fixtures/tests/groups.json',
    ]

    def setUp(self):
        self.user = get_user_model().objects.create(username='test', email='test@test.com', password='test')
        self.user.save()
        self.token = Token.objects.create(user=self.user)
        self.token.save()
        self.client.force_authenticate(user=self.user)
        self.group = Group.objects.all().first()
        if hasattr(settings, 'ALLOW_ALL_USER_READ'):
            self.ALLOW_ALL_USER_READ = settings.ALLOW_ALL_USER_READ
            settings.ALLOW_ALL_USER_READ = False
        if hasattr(settings, 'DISABLE_RESOURCE_PERMISSION_CHECK'):
            self.DISABLE_RESOURCE_PERMISSION_CHECK = settings.DISABLE_RESOURCE_PERMISSION_CHECK
            settings.DISABLE_RESOURCE_PERMISSION_CHECK = False

        for permission in Permission.objects.all():
            self.user.user_permissions.add(permission)

        for name, view in (("group-resource-permissions",
                            "<class 'pdc.apps.auth.views.GroupResourcePermissionViewSet'>"),
                           ("release-components", "<class 'pdc.apps.component.views.ReleaseComponentViewSet'>"),
                           ("rpc/find-compose-by-release-rpm/(?P<release_id>[^/]+)/(?P<rpm_name>[^/]+)",
                            "<class 'pdc.apps.compose.views.FindComposeByReleaseRPMViewSet'>")):
            Resource.objects.create(name=name, view=view)
        for resource in Resource.objects.all():
            for permission in ActionPermission.objects.all():
                ResourcePermission.objects.create(resource=resource, permission=permission)

        permissions = ('create', 'read', 'update', 'delete')
        group_resource_permissions = [ResourcePermission.objects.get(resource__name='group-resource-permissions',
                                                                     permission__name=per) for per in permissions]
        for group in Group.objects.all():
            for per in group_resource_permissions:
                GroupResourcePermission.objects.create(group=group, resource_permission=per)
        self.group.user_set.add(self.user)

    def tearDown(self):
        if hasattr(settings, 'ALLOW_ALL_USER_READ'):
            settings.ALLOW_ALL_USER_READ = self.ALLOW_ALL_USER_READ
        if hasattr(settings, 'DISABLE_RESOURCE_PERMISSION_CHECK'):
            settings.DISABLE_RESOURCE_PERMISSION_CHECK = self.DISABLE_RESOURCE_PERMISSION_CHECK

    def test_control_read_permission(self):
        url = reverse('releasecomponent-list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data, {u'detail': u'You do not have permission to perform this action.'})
        url = reverse('releasecomponent-detail', kwargs={'pk': 1})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data, {u'detail': u'You do not have permission to perform this action.'})

        # grant user's group read permission
        url = reverse('groupresourcepermissions-list')
        data = {'group': self.group.name, "permission": "read", "resource": "release-components"}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        url = reverse('releasecomponent-list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        url = reverse('releasecomponent-detail', kwargs={'pk': 1})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # remove from the group and retest
        self.group.user_set.remove(self.user)
        url = reverse('releasecomponent-list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_control_delete_permission(self):
        url = reverse('releasecomponent-detail', kwargs={'pk': 1})
        response = self.client.delete(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data, {u'detail': u'You do not have permission to perform this action.'})

        # grant user's group delete permission
        url = reverse('groupresourcepermissions-list')
        data = {'group': self.group.name, "permission": "delete", "resource": "release-components"}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        url = reverse('releasecomponent-detail', kwargs={'pk': 1})
        response = self.client.delete(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # remove from the group and retest
        self.group.user_set.remove(self.user)
        response = self.client.delete(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_control_update_permission(self):
        url = reverse('releasecomponent-detail', kwargs={'pk': 1})
        patch_data = {'name': 'fake_name'}
        response = self.client.patch(url, patch_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data, {u'detail': u'You do not have permission to perform this action.'})

        put_data = {'release': 'release-1.0', 'global_component': 'python', 'name': 'python34',
                    'brew_package': 'python-pdc', 'active': 'True'}
        response = self.client.put(url, put_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data, {u'detail': u'You do not have permission to perform this action.'})

        # grant user's group update permission
        url = reverse('groupresourcepermissions-list')
        data = {'group': self.group.name, "permission": "update", "resource": "release-components"}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        url = reverse('releasecomponent-detail', kwargs={'pk': 1})
        response = self.client.patch(url, patch_data, format='json')
        self.assertNotEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        response = self.client.put(url, put_data, format='json')
        self.assertNotEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # remove from the group and retest
        self.group.user_set.remove(self.user)
        response = self.client.patch(url, patch_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        response = self.client.put(url, put_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_control_create_permission(self):
        url = reverse('releasecomponent-list')
        data = {'release': 'release-1.0', 'global_component': 'python', 'name': 'python34',
                'brew_package': 'python-pdc', 'active': 'True'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data, {u'detail': u'You do not have permission to perform this action.'})

        # grant user's group create permission
        url = reverse('groupresourcepermissions-list')
        data = {'group': self.group.name, "permission": "create", "resource": "release-components"}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        url = reverse('releasecomponent-list')
        response = self.client.post(url, data, format='json')
        self.assertNotEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # remove from the group and retest
        self.group.user_set.remove(self.user)
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_permission_change_after_update_permission(self):
        # grant user's group read permission
        url = reverse('groupresourcepermissions-list')
        data = {'group': self.group.name, "permission": "read", "resource": "release-components"}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        created_id = response.data['id']

        url = reverse('releasecomponent-list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # change read to create
        url = reverse('groupresourcepermissions-detail', args=[created_id])
        data = {'group': self.group.name, "permission": "create", "resource": "release-components"}
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        url = reverse('releasecomponent-list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # change back
        url = reverse('groupresourcepermissions-detail', args=[created_id])
        data = {'group': self.group.name, "permission": "read", "resource": "release-components"}
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        url = reverse('releasecomponent-list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_permission_change_after_update_permission_with_patch(self):
        # grant user's group read permission
        url = reverse('groupresourcepermissions-list')
        data = {'group': self.group.name, "permission": "read", "resource": "release-components"}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        created_id = response.data['id']

        url = reverse('releasecomponent-list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # change read to create
        url = reverse('groupresourcepermissions-detail', args=[created_id])
        data = {"permission": "create"}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        url = reverse('releasecomponent-list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # change back
        url = reverse('groupresourcepermissions-detail', args=[created_id])
        data = {"permission": "read"}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        url = reverse('releasecomponent-list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # only change group
        group_2 = Group.objects.all().get(pk=2)
        # change read to create
        url = reverse('groupresourcepermissions-detail', args=[created_id])
        data = {"group": group_2.name}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        url = reverse('releasecomponent-list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_work_with_regexp_resource_name(self):
        url = reverse('findcomposebyrr-list', kwargs={'rpm_name': 'bash', 'release_id': 'release-1.0'})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data, {u'detail': u'You do not have permission to perform this action.'})

        # grant user's group update permission
        url = reverse('groupresourcepermissions-list')
        data = {'group': self.group.name, "permission": "read",
                "resource": "rpc/find-compose-by-release-rpm/(?P<release_id>[^/]+)/(?P<rpm_name>[^/]+)"}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        url = reverse('findcomposebyrr-list', kwargs={'rpm_name': 'bash', 'release_id': 'release-1.0'})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # remove from the group and retest
        self.group.user_set.remove(self.user)
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_enable_all_permissions_flag(self):
        if hasattr(settings, 'DISABLE_RESOURCE_PERMISSION_CHECK'):
            settings.DISABLE_RESOURCE_PERMISSION_CHECK = True
            # automatically have permission
            url = reverse('findcomposebyrr-list', kwargs={'rpm_name': 'bash', 'release_id': 'release-1.0'})
            response = self.client.get(url, format='json')
            self.assertNotEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_group_permission(self):
        # grant user's group read permission
        permission_url = reverse('groupresourcepermissions-list')
        data = {'group': self.group.name, "permission": "read", "resource": "release-components"}
        response = self.client.post(permission_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        created_id = response.data['id']

        rc_url = reverse('releasecomponent-list')
        response = self.client.get(rc_url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        url = reverse('groupresourcepermissions-detail', kwargs={'pk': created_id})
        self.client.delete(url, format='json')

        response = self.client.get(rc_url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_filter_with_group_name(self):
        data = {'group': self.group.name}
        url = reverse('groupresourcepermissions-list')

        response = self.client.get(url, data, format='json')
        self.assertEqual(response.data['count'], 4)

        data = {'group': 'fake_group'}
        response = self.client.get(url, data, format='json')
        self.assertEqual(response.data['count'], 0)

    def test_filter_with_permission(self):
        data = {'permission': 'create'}
        url = reverse('groupresourcepermissions-list')

        response = self.client.get(url, data, format='json')
        self.assertEqual(response.data['count'], 3)

        data = {'permission': 'read'}
        response = self.client.get(url, data, format='json')
        self.assertEqual(response.data['count'], 3)

        data = {'permission': 'fake_permission'}
        response = self.client.get(url, data, format='json')
        self.assertEqual(response.data['count'], 0)

    def test_filter_with_resource(self):
        data = {'resource': 'group-resource-permissions'}
        url = reverse('groupresourcepermissions-list')

        response = self.client.get(url, data, format='json')
        self.assertEqual(response.data['count'], 12)

        data = {'resource': 'fake_resource'}
        response = self.client.get(url, data, format='json')
        self.assertEqual(response.data['count'], 0)

        data = {'resource': 'rpc/find-compose-by-release-rpm/(?P<release_id>[^/]+)/(?P<rpm_name>[^/]+)'}
        response = self.client.get(url, data, format='json')
        self.assertEqual(response.data['count'], 0)

        data = {'group': self.group.name, "permission": "read",
                "resource": "rpc/find-compose-by-release-rpm/(?P<release_id>[^/]+)/(?P<rpm_name>[^/]+)"}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        data = {'resource': 'rpc/find-compose-by-release-rpm/(?P<release_id>[^/]+)/(?P<rpm_name>[^/]+)'}
        response = self.client.get(url, data, format='json')
        self.assertEqual(response.data['count'], 1)

    def test_retrieve(self):
        data = {'group': self.group.name, "permission": "read",
                "resource": "rpc/find-compose-by-release-rpm/(?P<release_id>[^/]+)/(?P<rpm_name>[^/]+)"}
        url = reverse('groupresourcepermissions-list')
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        obj_id = response.data['id']
        url = reverse('groupresourcepermissions-detail', args=[obj_id])
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data.update({'id': obj_id})
        self.assertEqual(data, response.data)

    def test_list_with_unknown_field(self):
        url = reverse('groupresourcepermissions-list')
        data = {'aaa': 'bbb'}
        response = self.client.get(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {"detail": "Unknown query params: aaa."})

    def test_patch_with_unknown_field(self):
        permission_url = reverse('groupresourcepermissions-list')
        data = {'group': self.group.name, "permission": "read", "resource": "release-components"}
        response = self.client.post(permission_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        created_id = response.data['id']

        url = reverse('groupresourcepermissions-detail', kwargs={'pk': created_id})
        data = {'group': self.group.name, "permission": "update", "aaa": "bbb"}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'detail': 'Unknown fields: "aaa".'})

    def test_uniqueness_check_response(self):
        # grant user's group update permission
        url = reverse('groupresourcepermissions-list')
        data = {'group': self.group.name, "permission": "read",
                "resource": "rpc/find-compose-by-release-rpm/(?P<release_id>[^/]+)/(?P<rpm_name>[^/]+)"}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # again
        url = reverse('groupresourcepermissions-list')
        data = {'group': self.group.name, "permission": "read",
                "resource": "rpc/find-compose-by-release-rpm/(?P<release_id>[^/]+)/(?P<rpm_name>[^/]+)"}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data,
                         {'detail': ['The fields resource, permission, group must make a unique set.']})

        # check 'put' method to violate uniqueness
        url = reverse('groupresourcepermissions-list')
        data = {'group': self.group.name, "permission": "delete",
                "resource": "rpc/find-compose-by-release-rpm/(?P<release_id>[^/]+)/(?P<rpm_name>[^/]+)"}
        response = self.client.post(url, data, format='json')
        obj_id = response.data['id']
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        url = reverse('groupresourcepermissions-detail', kwargs={'pk': obj_id})
        data = {'group': self.group.name, "permission": "read",
                "resource": "rpc/find-compose-by-release-rpm/(?P<release_id>[^/]+)/(?P<rpm_name>[^/]+)"}
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data,
                         {'detail': ['The fields resource, permission, group must make a unique set.']})


class ResourcePermissionsAPITestCase(APITestCase):
    fixtures = [
        'pdc/apps/auth/fixtures/tests/groups.json',
    ]

    def setUp(self):
        self.user = get_user_model().objects.create(username='test', email='test@test.com', password='test')
        self.user.save()
        self.token = Token.objects.create(user=self.user)
        self.token.save()
        self.client.force_authenticate(user=self.user)
        self.url = reverse('resourcepermissions-list')

        for permission in Permission.objects.all():
            self.user.user_permissions.add(permission)

        for name, view in (("group-resource-permissions",
                            "<class 'pdc.apps.auth.views.GroupResourcePermissionViewSet'>"),
                           ("release-components", "<class 'pdc.apps.component.views.ReleaseComponentViewSet'>"),
                           ("rpc/find-compose-by-release-rpm/(?P<release_id>[^/]+)/(?P<rpm_name>[^/]+)",
                            "<class 'pdc.apps.compose.views.FindComposeByReleaseRPMViewSet'>")):
            Resource.objects.create(name=name, view=view)
        for resource in Resource.objects.all():
            for permission in ActionPermission.objects.all():
                ResourcePermission.objects.create(resource=resource, permission=permission)

    def test_filter_with_permission(self):
        data = {'permission': 'create'}
        response = self.client.get(self.url, data, format='json')
        self.assertEqual(response.data['count'], 3)

        data = {'permission': 'read'}
        response = self.client.get(self.url, data, format='json')
        self.assertEqual(response.data['count'], 3)

        data = {'permission': 'fake_permission'}
        response = self.client.get(self.url, data, format='json')
        self.assertEqual(response.data['count'], 0)

    def test_filter_with_resource(self):
        data = {'resource': 'group-resource-permissions'}

        response = self.client.get(self.url, data, format='json')
        self.assertEqual(response.data['count'], 4)

        data = {'resource': 'fake_resource'}
        response = self.client.get(self.url, data, format='json')
        self.assertEqual(response.data['count'], 0)

    def test_list(self):
        response = self.client.get(self.url, format='json')
        self.assertEqual(response.data['count'], 12)

        data = {'permission': 'create', 'resource': 'group-resource-permissions'}
        response = self.client.get(self.url, data, format='json')
        self.assertEqual(response.data['count'], 1)


class ResourceApiUrlsTestCase(APITestCase):
    fixtures = ['pdc/apps/auth/fixtures/tests/resource_api_urls.json']

    def test_list(self):
        url = reverse('resourceapiurls-list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        data = {
            "id": 1,
            "resource": "auth/groups",
            "url": "https://www.example.com/pdc/auth/groups"
        }
        self.assertEqual(response.data.get('results')[0], data)

    def test_retrieve(self):
        url = reverse('resourceapiurls-detail', args=[1])
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = {
            "id": 1,
            "resource": "auth/groups",
            "url": "https://www.example.com/pdc/auth/groups"
        }
        self.assertEqual(response.data, data)

    def test_create(self):
        url = reverse('resourceapiurls-list')
        data = {
            "resource": "auth/permissions",
            "url": "https://www.example.com/pdc/auth/permissions"}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['resource'], data['resource'])
        self.assertEqual(response.data['url'], data['url'])

    def test_update(self):
        url = reverse('resourceapiurls-detail', args=[1])
        data = {"url": "https://www.example.com/pdc/auth/groups-new"}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data['id'] = 1
        data['resource'] = "auth/groups"
        self.assertEqual(response.data, data)

    def test_filter(self):
        url = reverse('resourceapiurls-list')
        response = self.client.get(url, {"resource": "auth/groups"}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        data = {
            "id": 1,
            "resource": "auth/groups",
            "url": "https://www.example.com/pdc/auth/groups"
        }
        self.assertEqual(response.data.get('results')[0], data)

    def test_delete(self):
        url = reverse('resourceapiurls-detail', args=[1])
        response = self.client.delete(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_add_api_again_fails(self):
        url = reverse('resourceapiurls-list')
        data = {'resource': 'auth/groups', 'url': 'https://www.example.com/pdc/auth/groups-new'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, ['The API URL for given resource already exists.'])
