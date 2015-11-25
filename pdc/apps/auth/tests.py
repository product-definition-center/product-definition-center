# -*- coding: utf-8 -*-
#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
import mock

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.urlresolvers import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from . import backends
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
