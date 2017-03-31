#
# Copyright (c) 2017 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
from datetime import datetime, timedelta
from django.core.urlresolvers import reverse
from rest_framework.test import APITestCase
from rest_framework import status

from pdc.apps.component.models import GlobalComponent
from pdc.apps.componentbranch.models import (
    ComponentBranch, SLAToComponentBranch, SLA)


class SLAAPITestCase(APITestCase):
    fixtures = ['pdc/apps/componentbranch/fixtures/tests/sla.json']

    def test_create_sla(self):
        url = reverse('sla-list')
        data = {
            'name': 'features',
            'description': 'A wonderful description'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        expected_rv = {
            'name': 'features',
            'description': 'A wonderful description',
            'id': 3
        }
        self.assertEqual(response.data, expected_rv)

    def test_get_sla(self):
        url = reverse('sla-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)
        self.assertEqual(response.data['results'][0]['id'], 2)
        self.assertEqual(response.data['results'][0]['name'], 'bug_fixes')
        self.assertEqual(response.data['results'][0]['description'],
                         'Bug fixes are applied')

    def test_patch_sla(self):
        url = reverse('sla-detail', args=[1])
        data = {
            'description': 'A new description'
        }
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], 1)
        self.assertEqual(response.data['name'], 'security_fixes')
        self.assertEqual(response.data['description'], 'A new description')

    def test_patch_sla_change_name_error(self):
        url = reverse('sla-detail', args=[1])
        data = {
            'name': 'some_new_name'
        }
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        error = {'name': ["You may not modify the SLA's name due to policy"]}
        self.assertEqual(response.data, error)

    def test_put_sla(self):
        url = reverse('sla-detail', args=[1])
        data = {
            'name': 'security_fixes',
            'description': 'A new description'
        }
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], 1)
        self.assertEqual(response.data['name'], 'security_fixes')
        self.assertEqual(response.data['description'], 'A new description')

    def test_put_sla_change_name_error(self):
        url = reverse('sla-detail', args=[1])
        data = {
            'name': 'some_new_name',
            'description': 'A new description'
        }
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        error = {'name': ["You may not modify the SLA's name due to policy"]}
        self.assertEqual(response.data, error)

    def test_delete_sla(self):
        url = reverse('sla-detail', args=[1])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)


class ComponentBranchAPITestCase(APITestCase):
    fixtures = ['pdc/apps/componentbranch/fixtures/tests/global_component.json',
                'pdc/apps/componentbranch/fixtures/tests/sla.json',
                'pdc/apps/componentbranch/fixtures/tests/componentbranch.json']

    def test_create_branch(self):
        url = reverse('componentbranch-list')
        data = {
            'name': '3.6',
            'global_component': 'python',
            'type': 'rpm',
            'critical_path': True
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        expected_rv = {
            'name': '3.6',
            'slas': [],
            'global_component': 'python',
            'active': False,
            'critical_path': True,
            'type': 'rpm',
            'id': 3
        }
        self.assertEqual(response.data, expected_rv)

    def test_create_branch_critical_path_default(self):
        url = reverse('componentbranch-list')
        data = {
            'name': '3.6',
            'global_component': 'python',
            'type': 'rpm'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        branch = ComponentBranch.objects.filter(id=1).first()
        self.assertEqual(branch.critical_path, False)

    def test_create_branch_bad_name(self):
        url = reverse('componentbranch-list')
        data = {
            'name': 'epel7',
            'global_component': 'python',
            'type': 'rpm',
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        expected_rv = {'name': ['The branch name is not allowed based on the regex "^epel\\d+$"']}
        self.assertEqual(response.data, expected_rv)

    def test_get_branch(self):
        url = reverse('componentbranch-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)
        self.assertEqual(response.data['results'][0]['id'], 2)
        self.assertEqual(response.data['results'][0]['name'], '2.6')
        self.assertEqual(response.data['results'][0]['global_component'],
                         'python')
        self.assertEqual(response.data['results'][0]['type'], 'rpm')
        self.assertFalse(response.data['results'][0]['active'])
        self.assertFalse(response.data['results'][0]['critical_path'])

    def test_get_branch_filter(self):
        url = reverse('componentbranch-list')
        url = '{0}?global_component=python&type=rpm&name=2.7'.format(url)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['id'], 1)
        self.assertEqual(response.data['results'][0]['name'], '2.7')
        self.assertEqual(response.data['results'][0]['global_component'],
                         'python')
        self.assertEqual(response.data['results'][0]['type'], 'rpm')
        self.assertFalse(response.data['results'][0]['active'])
        self.assertFalse(response.data['results'][0]['critical_path'])

    def test_patch_branch(self):
        gc2 = GlobalComponent(name='pythonx')
        gc2.save()
        url = reverse('componentbranch-detail', args=[2])
        data = {
            'global_component': 'pythonx'
        }
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], 2)
        self.assertEqual(response.data['name'], '2.6')
        self.assertEqual(response.data['global_component'],
                         'pythonx')
        self.assertEqual(response.data['type'], 'rpm')
        self.assertFalse(response.data['active'])
        self.assertFalse(response.data['critical_path'])

    def test_patch_branch_change_name_error(self):
        url = reverse('componentbranch-detail', args=[1])
        data = {
            'name': '3.6'
        }
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        error_msg = {
            'name': ["You may not modify the branch's name due to policy"]}
        self.assertEqual(response.data, error_msg)

    def test_put_branch(self):
        gc2 = GlobalComponent(name='pythonx')
        gc2.save()
        url = reverse('componentbranch-detail', args=[2])
        data = {
            'name': '2.6',
            'global_component': 'pythonx',
            'type': 'rpm',
            'critical_path': False
        }
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], 2)
        self.assertEqual(response.data['name'], '2.6')
        self.assertEqual(response.data['global_component'],
                         'pythonx')
        self.assertEqual(response.data['type'], 'rpm')
        self.assertFalse(response.data['active'])
        self.assertFalse(response.data['critical_path'])

    def test_put_branch_change_name_error(self):
        url = reverse('componentbranch-detail', args=[1])
        data = {
            'name': '3.6',
            'global_component': 'python',
            'type': 'rpm',
            'critical_path': False
        }
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        error_msg = {
            'name': ["You may not modify the branch's name due to policy"]}
        self.assertEqual(response.data, error_msg)

    def test_delete_branch(self):
        url = reverse('componentbranch-detail', args=[1])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_delete_branch_with_slas(self):
        branch = ComponentBranch.objects.get(id=1)
        sla = SLA.objects.get(name='bug_fixes')
        sla_entry = SLAToComponentBranch(
            sla=sla, branch=branch, eol='2222-01-01')
        sla_entry.save()
        url = reverse('componentbranch-detail', args=[1])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)


class SLAToBranchAPITestCase(APITestCase):
    fixtures = ['pdc/apps/componentbranch/fixtures/tests/global_component.json',
                'pdc/apps/componentbranch/fixtures/tests/sla.json',
                'pdc/apps/componentbranch/fixtures/tests/componentbranch.json',
                'pdc/apps/componentbranch/fixtures/tests/slatocomponentbranch.json']

    def test_create_sla_to_branch_branch_exists(self):
        url = reverse('slatocomponentbranch-list')
        data = {
            'sla': 'bug_fixes',
            'eol': '2222-01-01',
            'branch': {
                'name': '2.7',
                'global_component': 'python',
                'type': 'rpm',
                'critical_path': False
            }
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        expected_rv = {
            'sla': 'bug_fixes',
            'eol': '2222-01-01',
            'branch': {
                'name': '2.7',
                'global_component': 'python',
                'type': 'rpm',
                'active': True,
                'critical_path': False,
                'id': 1
            },
            'id': 2
        }
        self.assertEqual(response.data, expected_rv)

    def test_create_sla_to_branch_branch_exists_critical_path_wrong(self):
        url = reverse('slatocomponentbranch-list')
        data = {
            'sla': 'bug_fixes',
            'eol': '2222-01-01',
            'branch': {
                'name': '2.7',
                'global_component': 'python',
                'type': 'rpm',
                'critical_path': True
            }
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        error = ('The found branch\'s critical_path field did not match the '
                 'supplied value')
        error_msg = {'branch.critical_path': [error]}
        self.assertEqual(response.data, error_msg)

    def test_create_sla_to_branch(self):
        url = reverse('slatocomponentbranch-list')
        data = {
            'sla': 'bug_fixes',
            'eol': '2222-01-01',
            'branch': {
                'name': '2.7',
                'global_component': 'python',
                'type': 'rpm',
                'critical_path': False
            }
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        expected_rv = {
            'sla': 'bug_fixes',
            'eol': '2222-01-01',
            'branch': {
                'name': '2.7',
                'global_component': 'python',
                'type': 'rpm',
                'active': True,
                'critical_path': False,
                'id': 1
            },
            'id': 2
        }
        self.assertEqual(response.data, expected_rv)

    def test_create_sla_to_branch_branch(self):
        url = reverse('slatocomponentbranch-list')
        data = {
            'sla': 'security_fixes',
            'eol': '2222-01-01',
            'branch': {
                'name': '3.6',
                'global_component': 'python',
                'type': 'rpm',
                'critical_path': True
            }
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        expected_rv = {
            'sla': 'security_fixes',
            'eol': '2222-01-01',
            'branch': {
                'name': '3.6',
                'global_component': 'python',
                'type': 'rpm',
                'active': True,
                'critical_path': True,
                'id': 3
            },
            'id': 2
        }
        self.assertEqual(response.data, expected_rv)

    def test_create_sla_to_branch_branch_critical_path_default(self):
        url = reverse('slatocomponentbranch-list')
        data = {
            'sla': 'security_fixes',
            'eol': '2222-01-01',
            'branch': {
                'name': '3.6',
                'global_component': 'python',
                'type': 'rpm',
            }
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        expected_rv = {
            'sla': 'security_fixes',
            'eol': '2222-01-01',
            'branch': {
                'name': '3.6',
                'global_component': 'python',
                'type': 'rpm',
                'active': True,
                'critical_path': False,
                'id': 3
            },
            'id': 2
        }
        self.assertEqual(response.data, expected_rv)

    def test_create_sla_to_branch_bad_branch_name(self):
        url = reverse('slatocomponentbranch-list')
        data = {
            'sla': 'security_fixes',
            'eol': '2222-01-01',
            'branch': {
                'name': 'epel7',
                'global_component': 'python',
                'type': 'rpm',
                'critical_path': False
            }
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        expected_rv = {'branch': {'name': ['The branch name is not allowed based on the regex "^epel\\d+$"']}}
        self.assertEqual(response.data, expected_rv)

    def test_get_sla_to_branch(self):
        url = reverse('slatocomponentbranch-list')
        response = self.client.get(url)
        expected_branch = {
            'name': '2.7',
            'global_component': 'python',
            'type': 'rpm',
            'active': True,
            'critical_path': False,
            'id': 1
        }
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['id'], 1)
        self.assertEqual(response.data['results'][0]['sla'], 'security_fixes')
        self.assertEqual(response.data['results'][0]['eol'], '2222-01-01')
        self.assertEqual(response.data['results'][0]['branch'], expected_branch)

    def test_get_sla_to_branch_filtering(self):
        url = reverse('slatocomponentbranch-list')
        url = '{0}?branch=2.7&global_component=python&branch_type=rpm'.format(url)
        response = self.client.get(url)
        expected_branch = {
            'name': '2.7',
            'global_component': 'python',
            'type': 'rpm',
            'active': True,
            'critical_path': False,
            'id': 1
        }
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['id'], 1)
        self.assertEqual(response.data['results'][0]['sla'], 'security_fixes')
        self.assertEqual(response.data['results'][0]['eol'], '2222-01-01')
        self.assertEqual(response.data['results'][0]['branch'], expected_branch)

    def test_patch_sla_to_branch(self):
        url = reverse('slatocomponentbranch-detail', args=[1])
        data = {
            'eol': '2222-03-01'
        }
        response = self.client.patch(url, data, format='json')
        expected_branch = {
            'name': '2.7',
            'global_component': 'python',
            'type': 'rpm',
            'active': True,
            'critical_path': False,
            'id': 1
        }
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], 1)
        self.assertEqual(response.data['sla'], 'security_fixes')
        self.assertEqual(response.data['eol'], '2222-03-01')
        self.assertEqual(response.data['branch'], expected_branch)

    def test_patch_sla_to_branch_change_branch_error(self):
        url = reverse('slatocomponentbranch-detail', args=[1])
        data = {
            'branch': {
                'name': '3.6',
                'global_component': 'python',
                'type': 'rpm',
                'critical_path': False,
            }
        }
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        error_msg = {'branch': ['The branch cannot be modified using this API']}
        self.assertEqual(response.data, error_msg)

    def test_put_sla_to_branch(self):
        url = reverse('slatocomponentbranch-detail', args=[1])
        branch = {
            'name': '2.7',
            'global_component': 'python',
            'type': 'rpm',
            'critical_path': False
        }
        data = {
            'sla': 'security_fixes',
            'eol': '2222-03-01',
            'branch': branch,
        }
        response = self.client.put(url, data, format='json')
        branch['id'] = 1
        branch['active'] = True
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], 1)
        self.assertEqual(response.data['sla'], 'security_fixes')
        self.assertEqual(response.data['eol'], '2222-03-01')
        self.assertEqual(response.data['branch'], branch)

    def test_put_sla_to_branch_no_critical_path(self):
        url = reverse('slatocomponentbranch-detail', args=[1])
        branch = {
            'name': '2.7',
            'global_component': 'python',
            'type': 'rpm'
        }
        data = {
            'sla': 'security_fixes',
            'eol': '2222-03-01',
            'branch': branch,
        }
        response = self.client.put(url, data, format='json')
        branch['id'] = 1
        branch['active'] = True
        branch['critical_path'] = False
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], 1)
        self.assertEqual(response.data['sla'], 'security_fixes')
        self.assertEqual(response.data['eol'], '2222-03-01')
        self.assertEqual(response.data['branch'], branch)

    def test_put_sla_to_branch_change_branch_error(self):
        url = reverse('slatocomponentbranch-detail', args=[1])
        branch = {
            'name': '3.5',
            'global_component': 'python',
            'type': 'rpm',
            'critical_path': False
        }
        data = {
            'sla': 'security_fixes',
            'eol': '2222-03-01',
            'branch': branch,
        }
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        error = {'branch': ['The branch cannot be modified using this API']}
        self.assertEqual(response.data, error)

    def test_delete_sla_to_branch(self):
        url = reverse('slatocomponentbranch-detail', args=[1])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_delete_sla_with_sla_to_branch_relationships(self):
        branch = ComponentBranch.objects.get(id=1)
        sla = SLA.objects.get(name='bug_fixes')
        sla_entry = SLAToComponentBranch(
            sla=sla, branch=branch, eol='2222-01-01')
        sla_entry.save()
        url = reverse('sla-detail', args=[2])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_active_componentbranch_false(self):
        url = reverse('componentbranch-list')
        url = '{0}?active=false'.format(url)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    def test_active_with_sla_of_today(self):
        today = str(datetime.utcnow().date())
        branch = ComponentBranch.objects.get(id=2)
        sla = SLA.objects.get(name='bug_fixes')
        sla_entry = SLAToComponentBranch(
            sla=sla, branch=branch, eol=today)
        sla_entry.save()
        url = reverse('componentbranch-detail', args=[2])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['active'])

    def test_active_with_sla_of_yesterday(self):
        yesterday = str(datetime.utcnow().date() - timedelta(days=1))
        branch = ComponentBranch.objects.get(id=2)
        sla = SLA.objects.get(name='bug_fixes')
        sla_entry = SLAToComponentBranch(
            sla=sla, branch=branch, eol=yesterday)
        sla_entry.save()
        url = reverse('componentbranch-detail', args=[2])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['active'])

    def test_active_with_valid_and_invalid_sla(self):
        yesterday = str(datetime.utcnow().date() - timedelta(days=1))
        tomorrow = str(datetime.utcnow().date() + timedelta(days=1))
        branch = ComponentBranch.objects.get(id=2)
        sla_bug_fixes = SLA.objects.get(name='bug_fixes')
        sla_entry_one = SLAToComponentBranch(
            sla=sla_bug_fixes, branch=branch, eol=yesterday)
        sla_entry_one.save()
        sla_security_fixes = SLA.objects.get(name='security_fixes')
        sla_entry_two = SLAToComponentBranch(
            sla=sla_security_fixes, branch=branch, eol=tomorrow)
        sla_entry_two.save()
        url = reverse('componentbranch-detail', args=[2])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['active'])

    def test_active_filter_sla(self):
        yesterday = str(datetime.utcnow().date() - timedelta(days=1))
        branch = ComponentBranch.objects.get(id=2)
        sla_bug_fixes = SLA.objects.get(name='bug_fixes')
        sla_entry_one = SLAToComponentBranch(
            sla=sla_bug_fixes, branch=branch, eol=yesterday)
        sla_entry_one.save()
        url = reverse('slatocomponentbranch-list')
        url = '{0}?branch_active=true'.format(url)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    def test_active_filter_false(self):
        yesterday = str(datetime.utcnow().date() - timedelta(days=1))
        branch = ComponentBranch.objects.get(id=2)
        sla_bug_fixes = SLA.objects.get(name='bug_fixes')
        sla_entry_one = SLAToComponentBranch(
            sla=sla_bug_fixes, branch=branch, eol=yesterday)
        sla_entry_one.save()
        sla_security_fixes = SLA.objects.get(name='security_fixes')
        sla_entry_two = SLAToComponentBranch(
            sla=sla_security_fixes, branch=branch, eol=yesterday)
        sla_entry_two.save()
        url = reverse('slatocomponentbranch-list')
        url = '{0}?branch_active=false'.format(url)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)

    def test_active_filter_false_one_valid_one_invalid(self):
        tomorrow = str(datetime.utcnow().date() + timedelta(days=1))
        yesterday = str(datetime.utcnow().date() - timedelta(days=1))
        branch = ComponentBranch.objects.get(id=2)
        sla_bug_fixes = SLA.objects.get(name='bug_fixes')
        sla_entry_one = SLAToComponentBranch(
            sla=sla_bug_fixes, branch=branch, eol=yesterday)
        sla_entry_one.save()
        sla_security_fixes = SLA.objects.get(name='security_fixes')
        sla_entry_two = SLAToComponentBranch(
            sla=sla_security_fixes, branch=branch, eol=tomorrow)
        sla_entry_two.save()
        url = reverse('slatocomponentbranch-list')
        url = '{0}?branch_active=false'.format(url)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 0)

    def test_active_filter_sla_valid_and_invalid(self):
        yesterday = str(datetime.utcnow().date() - timedelta(days=1))
        tomorrow = str(datetime.utcnow().date() + timedelta(days=1))
        branch = ComponentBranch.objects.get(id=2)
        sla_bug_fixes = SLA.objects.get(name='bug_fixes')
        sla_entry_one = SLAToComponentBranch(
            sla=sla_bug_fixes, branch=branch, eol=yesterday)
        sla_entry_one.save()
        sla_security_fixes = SLA.objects.get(name='security_fixes')
        sla_entry_two = SLAToComponentBranch(
            sla=sla_security_fixes, branch=branch, eol=tomorrow)
        sla_entry_two.save()
        url = reverse('slatocomponentbranch-list')
        url = '{0}?branch_active=true'.format(url)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 3)
