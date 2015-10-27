# -*- coding: utf-8 -*-
#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
from pdc_client.test_helpers import CLITestCase
from pdc_client.runner import Runner


class RpmTestCase(CLITestCase):
    def setUp(self):
        self.runner = Runner()
        self.runner.setup()

    def test_list_without_filters(self, api):
        with self.expect_failure():
            self.runner.run(['rpm', 'list'])

    def _setup_list(self, api):
        api.add_endpoint('rpms', 'GET', [
            {'id': x,
             'name': 'bash',
             'epoch': 0,
             'version': '4.3.42',
             'release': x,
             'arch': 'x86_64'}
            for x in range(1, 30)
        ])

    def test_list(self, api):
        self._setup_list(api)
        with self.expect_output('list.txt'):
            self.runner.run(['rpm', 'list', '--name', 'bash'])
        self.assertEqual(api.calls['rpms'],
                         [('GET', {'page': 1, 'name': 'bash'}),
                          ('GET', {'page': 2, 'name': 'bash'})])

    def test_list_json(self, api):
        self._setup_list(api)
        with self.expect_output('list.json', parse_json=True):
            self.runner.run(['--json', 'rpm', 'list', '--name', 'bash'])
        self.assertEqual(api.calls['rpms'],
                         [('GET', {'page': 1, 'name': 'bash'}),
                          ('GET', {'page': 2, 'name': 'bash'})])

    def _setup_detail(self, api):
        obj = {
            'id': 1,
            'name': 'bash',
            'epoch': 0,
            'version': '4.3.42',
            'release': 1,
            'arch': 'x86_64',
            'srpm_name': 'bash',
            'srpm_nevra': 'bash-4.3.42-1.src',
            'filename': 'bash-0:4.3.42-1.x86_64.rpm',
            'linked_composes': ['compose-1'],
            'linked_releases': ['release-1'],
            'dependencies': {
                'requires': ['glibc > 0'],
                'obsoletes': [],
                'recommends': [],
                'suggests': [],
                'conflicts': [],
                'provides': [],
            }
        }
        api.add_endpoint('rpms/1', 'GET', obj)
        api.add_endpoint('rpms/1', 'PATCH', obj)
        api.add_endpoint('rpms', 'POST', obj)

    def test_info(self, api):
        self._setup_detail(api)
        with self.expect_output('info.txt'):
            self.runner.run(['rpm', 'info', '1'])
        self.assertEqual(api.calls['rpms/1'], [('GET', {})])

    def test_info_json(self, api):
        self._setup_detail(api)
        with self.expect_output('info.json', parse_json=True):
            self.runner.run(['--json', 'rpm', 'info', '1'])
        self.assertEqual(api.calls['rpms/1'], [('GET', {})])

    def test_create(self, api):
        self._setup_detail(api)
        with self.expect_output('info.txt'):
            self.runner.run(['rpm', 'create',
                             '--name', 'bash',
                             '--srpm-name', 'bash',
                             '--epoch', '0',
                             '--version', '4.3.42',
                             '--arch', 'x86_64',
                             '--release', '1'])
        self.assertEqual(api.calls['rpms'],
                         [('POST', {'name': 'bash', 'srpm_name': 'bash', 'arch': 'x86_64',
                                    'epoch': 0, 'version': '4.3.42', 'release': '1'})])
        self.assertEqual(api.calls['rpms/1'],
                         [('GET', {})])

    def test_update(self, api):
        self._setup_detail(api)
        with self.expect_output('info.txt'):
            self.runner.run(['rpm', 'update', '1',
                             '--name', 'bash',
                             '--srpm-name', 'bash',
                             '--epoch', '0',
                             '--version', '4.3.42',
                             '--release', '1'])
        self.assertEqual(api.calls['rpms/1'],
                         [('PATCH', {'name': 'bash', 'srpm_name': 'bash',
                                     'epoch': 0, 'version': '4.3.42', 'release': '1'}),
                          ('GET', {})])
