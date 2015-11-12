# -*- coding: utf-8 -*-
#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
from pdc_client.test_helpers import CLITestCase
from pdc_client.runner import Runner


class ReleaseTestCase(CLITestCase):
    def setUp(self):
        self.runner = Runner()
        self.runner.setup()
        self.release_detail = {
            'release_id': 'release-1.0',
            'active': True,
            'name': 'Test Release',
            'version': '1.0',
            'short': 'release',
            'product_version': 'release-1',
            'base_product': None,
            'release_type': 'ga',
            'integrated_with': None,
            'bugzilla': {'product': 'Test Release'},
            'dist_git': {'branch': 'release-1.0-candidate'},
            'compose_set': []
        }

    def _setup_release_detail(self, api):
        api.add_endpoint('releases/release-1.0', 'GET', self.release_detail)
        api.add_endpoint('release-variants', 'GET', [
            {'type': 'variant', 'uid': 'Server', 'id': 1, 'id': 'Server', 'name': 'Server',
             'arches': ['x86_64', 's390x']}
        ])

    def test_list_active_multi_page(self, api):
        api.add_endpoint('releases', 'GET', [
            {'release_id': 'release-0.{}'.format(x),
             'active': True,
             'name': 'Test Release'}
            for x in range(25)
        ])
        with self.expect_output('list_multi_page.txt'):
            self.runner.run(['release', 'list'])
        self.assertEqual(api.calls['releases'],
                         [('GET', {'page': 1, 'active': True}),
                          ('GET', {'page': 2, 'active': True})])

    def test_list_inactive(self, api):
        api.add_endpoint('releases', 'GET', [])
        with self.expect_output('empty.txt'):
            self.runner.run(['release', 'list', '--inactive'])
        self.assertEqual(api.calls['releases'],
                         [('GET', {'page': 1, 'active': False})])

    def test_list_all(self, api):
        api.add_endpoint('releases', 'GET', [])
        with self.expect_output('empty.txt'):
            self.runner.run(['release', 'list', '--all'])
        self.assertEqual(api.calls['releases'],
                         [('GET', {'page': 1})])

    def test_detail(self, api):
        self._setup_release_detail(api)
        with self.expect_output('detail.txt'):
            self.runner.run(['release', 'info', 'release-1.0'])
        self.assertDictEqual(api.calls,
                             {'releases/release-1.0': [('GET', {})],
                              'release-variants': [('GET', {'page': 1, 'release': 'release-1.0'})]})

    def test_update(self, api):
        self._setup_release_detail(api)
        api.add_endpoint('releases/release-0.9', 'PATCH', self.release_detail)
        with self.expect_output('detail.txt'):
            self.runner.run(['release', 'update', 'release-0.9', '--version', '1.0'])
        self.assertDictEqual(api.calls,
                             {'releases/release-0.9': [('PATCH', {'version': '1.0'})],
                              'releases/release-1.0': [('GET', {})],
                              'release-variants': [('GET', {'page': 1, 'release': 'release-1.0'})]})

    def test_create(self, api):
        api.add_endpoint('releases', 'POST', self.release_detail)
        self._setup_release_detail(api)
        with self.expect_output('detail.txt'):
            self.runner.run(['release', 'create', '--short', 'release',
                             '--version', '1.0',
                             '--name', 'Test Release',
                             '--release-type', 'ga'])
        self.assertDictEqual(api.calls,
                             {'releases': [('POST', {'name': 'Test Release',
                                                     'short': 'release',
                                                     'version': '1.0',
                                                     'release_type': 'ga'})],
                              'releases/release-1.0': [('GET', {})],
                              'release-variants': [('GET', {'page': 1, 'release': 'release-1.0'})]})

    def test_clone(self, api):
        api.add_endpoint('rpc/release/clone', 'POST', self.release_detail)
        self._setup_release_detail(api)
        with self.expect_output('detail.txt'):
            self.runner.run(['release', 'clone', 'old_release_id', '--version', '1.0'])
        self.assertDictEqual(api.calls,
                             {'rpc/release/clone': [('POST',
                                                     {'old_release_id': 'old_release_id',
                                                      'version': '1.0'})],
                              'releases/release-1.0': [('GET', {})],
                              'release-variants': [('GET', {'page': 1, 'release': 'release-1.0'})]})

    def test_clone_fails(self, api):
        with self.expect_failure():
            self.runner.run(['release', 'clone', 'old_release_id'])
        self.assertDictEqual(api.calls, {})

    def test_info_json(self, api):
        self._setup_release_detail(api)
        with self.expect_output('detail.json', parse_json=True):
            self.runner.run(['--json', 'release', 'info', 'release-1.0'])
        self.assertDictEqual(api.calls,
                             {'releases/release-1.0': [('GET', {})],
                              'release-variants': [('GET', {'page': 1, 'release': 'release-1.0'})]})

    def test_list_json(self, api):
        api.add_endpoint('releases', 'GET', [self.release_detail])
        with self.expect_output('list.json', parse_json=True):
            self.runner.run(['--json', 'release', 'list'])

    def test_can_not_activate_and_deactivate(self, api):
        with self.expect_failure():
            self.runner.run(['release', 'update', 'release-1.0', '--activate', '--deactivate'])
