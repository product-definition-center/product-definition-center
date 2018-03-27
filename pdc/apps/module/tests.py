# -*- coding: utf-8 -*-
#
# Copyright (c) 2018 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
from django.core.urlresolvers import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.apps import apps

from pdc.apps.common.test_utils import TestCaseWithChangeSetMixin
from pdc.apps.module.models import Module


class ModuleAPITestCase(TestCaseWithChangeSetMixin, APITestCase):
    fixtures = [
        'pdc/apps/module/fixtures/test/rpm.json',
    ]

    def setUp(self):
        self.data = {
            'name': 'testmodule',
            'stream': 'f27',
            'version': '23456789',
            'context': '12345678',
            'koji_tag': 'some_tag_f27',
            'modulemd': 'modulemd',
            'active': True
        }
        self.expected = {
            'active': True,
            'build_deps': [],
            'context': '12345678',
            'koji_tag': 'some_tag_f27',
            'modulemd': 'modulemd',
            'name': 'testmodule',
            'rpms': [],
            'runtime_deps': [],
            'stream': 'f27',
            'uid': 'testmodule:f27:23456789:12345678',
            'version': '23456789'
        }

    @staticmethod
    def create_module(version='23456789', stream='f27', active=True):
        obj = Module()
        obj.name = 'testmodule'
        obj.stream = stream
        obj.version = version
        obj.context = '12345678'
        obj.koji_tag = 'some_tag_{0}'.format(obj.stream)
        obj.modulemd = 'modulemd'
        obj.active = active
        obj.uid = ':'.join([obj.name, obj.stream, obj.version, obj.context])
        obj.variant_id = obj.name
        obj.save()

    def test_create_module(self):
        url = reverse('modules-list')
        response = self.client.post(url, self.data, format='json')
        # Check the response
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data, self.expected)
        # Check the database
        module_db = Module.objects.filter(uid='testmodule:f27:23456789:12345678').first()
        self.assertTrue(module_db.active)
        self.assertEqual(module_db.build_deps.count(), 0)
        self.assertEqual(module_db.context, '12345678')
        self.assertEqual(module_db.koji_tag, 'some_tag_f27')
        self.assertEqual(module_db.modulemd, 'modulemd')
        self.assertEqual(module_db.name, 'testmodule')
        self.assertEqual(module_db.rpms.count(), 0)
        self.assertEqual(module_db.runtime_deps.count(), 0)
        self.assertEqual(module_db.stream, 'f27')
        self.assertEqual(module_db.uid, 'testmodule:f27:23456789:12345678')
        self.assertEqual(module_db.version, '23456789')
        # Backwards compatibility checks
        self.assertEqual(module_db.variant_id, 'testmodule')
        self.assertEqual(module_db.type, 'module')

    def test_create_module_no_context_error(self):
        url = reverse('modules-list')
        self.data.pop('context')
        response = self.client.post(url, self.data, format='json')
        # In the "unreleasedvariants" API, we had a default context of '00000000', but in the
        # "modules" API, it is now a required field
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'context': ['This field is required.']})

    def test_create_and_get_module_with_rpms(self):
        uid_one = self.expected['uid']
        uid_two = 'testmodule:f27:56789012:12345678'
        url = reverse('modules-list')
        self.data['rpms'] = [{
            'name': 'foobar',
            'epoch': 0,
            'version': '1.0.0',
            'release': '1',
            'arch': 'src',
            'srpm_name': 'foobar',
            'srpm_commit_branch': 'master'
        }]
        messenger = apps.get_app_config('messaging').messenger
        with messenger.listen() as messages:
            response = self.client.post(url, self.data, format='json')

            # Check two messages were sent.
            self.assertEqual([m[0] for m in messages],
                             ['.rpms.added', '.modules.added'])

        # Check the response
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.expected['rpms'] = ['foobar-0:1.0.0-1.src.rpm']
        self.assertEqual(response.data, self.expected)
        # Check it appears properly with a GET request
        url_two = reverse('modules-detail', args=[uid_one])
        response_two = self.client.get(url_two, format='json')
        self.assertEqual(response_two.data, self.expected)

        # Create another module
        self.data['version'] = '56789012'
        self.data['rpms'] = []
        for version, branch in [('2.0.0', 'f27'), ('3.0.0', 'f28')]:
            self.data['rpms'].append({
                'name': 'foobar',
                'epoch': 0,
                'version': version,
                'release': '1',
                'arch': 'src',
                'srpm_name': 'foobar',
                'srpm_commit_branch': branch
            })
        response_three = self.client.post(url, self.data, format='json')
        # Check the response
        self.assertEqual(response_three.status_code, status.HTTP_201_CREATED)
        self.expected['rpms'] = ['foobar-0:2.0.0-1.src.rpm', 'foobar-0:3.0.0-1.src.rpm']
        self.expected['version'] = '56789012'
        self.expected['uid'] = uid_two
        self.assertEqual(response_three.data, self.expected)

        # Check that the filters work
        response_four = self.client.get(url, data={'component_name': 'foobar'}, format='json')
        self.assertEqual(response_four.data['count'], 2)
        response_five = self.client.get(
            url, data={'component_name': 'foobar', 'component_branch': 'master'}, format='json')
        self.assertEqual(response_five.data['count'], 1)
        self.assertEqual(response_five.data['results'][0]['uid'], uid_one)
        response_six = self.client.get(
            url, data={'component_name': 'foobar', 'component_branch': 'f27'}, format='json')
        self.assertEqual(response_six.data['count'], 1)
        self.assertEqual(response_six.data['results'][0]['uid'], uid_two)
        response_seven = self.client.get(url, data={'component_name': 'python'}, format='json')
        self.assertEqual(response_seven.data['count'], 0)

        # Filtering by RPM filename
        response_eight = self.client.get(url,
                                         data={'rpm_filename': 'foobar-2.0.0-1.src.rpm'},
                                         format='json')
        self.assertEqual(response_eight.data['count'], 1)
        response_nine = self.client.get(url,
                                        data={'rpm_filename': 'python-2.7.12-1.el7.noarch.rpm'},
                                        format='json')
        self.assertEqual(response_nine.data['count'], 0)

        # Filtering by both RPM name and branch ("component" filter)
        response = self.client.get(url, data={'component': 'foobar'}, format='json')
        self.assertEqual(response.data['count'], 2)
        response = self.client.get(
            url, data={'component': 'foobar/master'}, format='json')
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['uid'], uid_one)
        response = self.client.get(
            url, data={'component': 'foobar/f27'}, format='json')
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['uid'], uid_two)
        response = self.client.get(url, data={'component': 'python'}, format='json')
        self.assertEqual(response.data['count'], 0)
        response = self.client.get(
            url, data={'component': ['foobar/master', 'foobar/f27']}, format='json')
        self.assertEqual(response.data['count'], 2)

    def test_create_and_get_module_with_exist_rpms(self):
        url = reverse('modules-list')
        self.data['rpms'] = [{
            'name': 'bash-doc',
            'epoch': 0,
            'version': '1.2.3',
            'release': '4.b2',
            'arch': 'x86_64',
            'srpm_name': 'bash',
            'srpm_nevra': 'bash-0:1.2.3-4.b2.src'
        }]
        response = self.client.post(url, self.data, format='json')
        # Check the response
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.expected['rpms'] = ['bash-doc-0:1.2.3-4.b2.x86_64.rpm']
        self.assertEqual(response.data, self.expected)
        # Check it appears properly with a GET request
        url_two = reverse('modules-detail', args=['testmodule:f27:23456789:12345678'])
        response_two = self.client.get(url_two, format='json')
        self.assertEqual(response_two.data, self.expected)

    def test_create_and_get_module_with_deps(self):
        self.version = 56789012

        def _increment_version():
            self.version += 1
            self.data['version'] = str(self.version)
            self.expected['version'] = str(self.version)
            self.expected['uid'] = 'testmodule:f27:{0}:12345678'.format(self.version)

        # Test both build_deps and runtime_deps
        for dep_type in ('build_deps', 'runtime_deps'):
            # Reset the dictionaries
            self.setUp()
            _increment_version()
            uid_one = 'testmodule:f27:{0}:12345678'.format(self.version)

            # Create the first module
            url = reverse('modules-list')
            self.data[dep_type] = [{'dependency': 'platform', 'stream': 'master'}]
            response = self.client.post(url, self.data, format='json')
            # Check the response
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.expected[dep_type] = [{'dependency': 'platform', 'stream': 'master'}]
            self.assertEqual(response.data, self.expected)
            # Check it appears properly with a GET request
            url_two = reverse('modules-detail', args=[uid_one])
            response_two = self.client.get(url_two, format='json')
            self.assertEqual(response_two.data, self.expected)
            # Create another module
            _increment_version()
            uid_two = 'testmodule:f27:{0}:12345678'.format(self.version)
            self.data[dep_type] = [{'dependency': 'python', 'stream': 'f27'}]
            response_three = self.client.post(url, self.data, format='json')
            self.assertEqual(response_three.status_code, status.HTTP_201_CREATED)
            self.expected[dep_type] = [{'dependency': 'python', 'stream': 'f27'}]
            self.assertEqual(response_three.data, self.expected)

            # Test filtering and first start by query for the "unknown" dep
            dep_key = '{0}_name'.format(dep_type[:-1])
            response_four = self.client.get(url, {dep_key: 'unknown'}, format='json')
            self.assertEqual(response_four.status_code, status.HTTP_200_OK)
            self.assertEqual(response_four.data['count'], 0)
            # Query for platform
            response_five = self.client.get(url, data={dep_key: 'platform'}, format='json')
            self.assertEqual(response_five.status_code, status.HTTP_200_OK)
            self.assertEqual(response_five.data['count'], 1)
            self.assertEqual(response_five.data['results'][0]['uid'], uid_one)
            # Query for python:f27
            query = {
                dep_key: 'python',
                '{0}_stream'.format(dep_type[:-1]): 'f27'
            }
            response_six = self.client.get(url, data=query, format='json')
            self.assertEqual(response_six.status_code, status.HTTP_200_OK)
            self.assertEqual(response_six.data['count'], 1)
            self.assertEqual(response_six.data['results'][0]['uid'], uid_two)

    def test_delete_module(self):
        self.create_module()
        url = reverse('modules-detail', args=['testmodule:f27:23456789:12345678'])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        # Check the database
        module_count = Module.objects.filter(uid='testmodule:f27:23456789:12345678').count()
        self.assertEqual(module_count, 0)

    def test_patch_module(self):
        self.create_module()
        old_uid = 'testmodule:f27:23456789:12345678'
        new_version = '04191775'
        new_uid = 'testmodule:f27:{0}:12345678'.format(new_version)
        url = reverse('modules-detail', args=[old_uid])
        response = self.client.patch(url, data={'version': new_version}, format='json')
        self.expected['uid'] = new_uid
        self.expected['version'] = new_version
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, self.expected)
        # Make sure the UID changed
        module_obj = Module.objects.filter(uid=new_uid).first()
        self.assertEqual(module_obj.version, new_version)
        # Make sure the old UID isn't in the database anymore
        self.assertEqual(Module.objects.filter(uid=old_uid).count(), 0)

    def test_put_module(self):
        self.create_module()
        old_uid = 'testmodule:f27:23456789:12345678'
        new_version = '04191775'
        new_uid = 'testmodule:f27:{0}:12345678'.format(new_version)
        url = reverse('modules-detail', args=[old_uid])
        self.data['version'] = new_version
        response = self.client.put(url, data=self.data, format='json')
        self.expected['uid'] = new_uid
        self.expected['version'] = new_version
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, self.expected)
        # Make sure the UID changed
        module_obj = Module.objects.filter(uid=new_uid).first()
        self.assertEqual(module_obj.version, new_version)
        # Make sure the old UID isn't in the database anymore
        self.assertEqual(Module.objects.filter(uid=old_uid).count(), 0)

    def test_get_module_with_dot_in_uid(self):
        self.create_module(version='1.2')
        url = reverse('modules-detail', args=['testmodule:f27:1.2:12345678'])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_modules(self):
        self.create_module(version='23456789', active=True)
        self.create_module(version='89012345', active=False)
        url = reverse('modules-list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected_results = {
            'count': 2,
            'next': None,
            'previous': None,
            'results': [
                self.expected,
                {
                    'active': False,
                    'build_deps': [],
                    'context': '12345678',
                    'koji_tag': 'some_tag_f27',
                    'modulemd': 'modulemd',
                    'name': 'testmodule',
                    'rpms': [],
                    'runtime_deps': [],
                    'stream': 'f27',
                    'uid': 'testmodule:f27:89012345:12345678',
                    'version': '89012345'
                }
            ]
        }
        self.assertEqual(response.data, expected_results)

    def test_filter_modules(self):
        self.create_module(version='23456789', stream='f27', active=True)
        self.create_module(version='89012345', stream='master', active=False)
        url = reverse('modules-list')
        expected_results_f27 = {
            'count': 1,
            'next': None,
            'previous': None,
            'results': [self.expected]
        }
        expected_results_master = {
            'count': 1,
            'next': None,
            'previous': None,
            'results': [{
                'active': False,
                'build_deps': [],
                'context': '12345678',
                'koji_tag': 'some_tag_master',
                'modulemd': 'modulemd',
                'name': 'testmodule',
                'rpms': [],
                'runtime_deps': [],
                'stream': 'master',
                'uid': 'testmodule:master:89012345:12345678',
                'version': '89012345'
            }]
        }
        expected_results_both = {
            'count': 2,
            'next': None,
            'previous': None,
            'results': [
                expected_results_f27['results'][0],
                expected_results_master['results'][0]
            ]
        }
        filters = {
            'f27': [
                {'stream': 'f27'},
                {'active': True},
                {'koji_tag': 'some_tag_f27'},
                {'uid': 'testmodule:f27:23456789:12345678'},
                {'stream': 'f27', 'active': True}
            ],
            'both': [
                {'context': '12345678'},
                {'name': 'testmodule'},
            ],
            'master': [
                {'active': False},
                {'koji_tag': 'some_tag_master'},
                {'uid': 'testmodule:master:89012345:12345678'},
                {'stream': 'master', 'active': False}
            ],
        }
        for expected, item_filters in filters.items():
            if expected == 'f27':
                expected = expected_results_f27
            elif expected == 'master':
                expected = expected_results_master
            elif expected == 'both':
                expected = expected_results_both
            else:
                raise ValueError('"{0}" is an invalid value'.format(expected))
            for item_filter in item_filters:
                response = self.client.get(url, data=item_filter, format='json')
                self.assertEqual(response.status_code, status.HTTP_200_OK)
                self.assertEqual(response.data, expected)
