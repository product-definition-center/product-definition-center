# -*- coding: utf-8 -*-
#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
from pdc_client.test_helpers import CLITestCase
from pdc_client.runner import Runner


class GlobalComponentTestCase(CLITestCase):
    def setUp(self):
        self.runner = Runner()
        self.runner.setup()
        self.detail = {
            'id': '1',
            'name': 'Test Global Component',
            'dist_git_path': None,
            'dist_git_web_url': 'http://pkgs.example.com/test_global_component',
            'contacts': [
                {
                    'url': 'http://example.com/global-components/1/contacts/1/',
                    'contact_role': 'test_role_a',
                    'contact': {
                        'mail_name': 'Test Maillist',
                        'email': 'test_mail@example.com'
                    }
                },
                {
                    'url': 'http://example.com/global-components/1/contacts/2/',
                    'contact_role': 'test_role_b',
                    'contact': {
                        'username': 'Test User',
                        'email': 'test_user@example.com'
                    }
                }
            ],
            'labels': [
                {
                    'url': 'http://example.com/lable/1',
                    'name': 'test label',
                    'description': 'test label description'
                }
            ],
            'upstream': {
                'homepage': 'http://test_global_component.org',
                'scm_type': 'git',
                'scm_url': 'http://test_global_component.org/git'
            }
        }

    def _setup_detail(self, api):
        api.add_endpoint('global-components/1', 'GET', self.detail)

    def test_list_without_filters(self, api):
        with self.expect_failure():
            self.runner.run(['global-component', 'list'])

    def test_list_multi_page(self, api):
        api.add_endpoint('global-components', 'GET', [
            {'id': x,
             'name': 'Test Global Component %s' % x}
            for x in range(1, 26)
        ])
        with self.expect_output('global_component/list_multi_page.txt'):
            self.runner.run(['global-component', 'list',
                             '--label', 'test label'])
        self.assertEqual(api.calls['global-components'],
                         [('GET', {'page': 1, 'label': 'test label'}),
                          ('GET', {'page': 2, 'label': 'test label'})])

    def test_detail(self, api):
        self._setup_detail(api)
        api.add_endpoint('global-component-contacts',
                         'GET',
                         {'count': 1,
                          'next': None,
                          'previous': None,
                          'results': [
                              {
                                  'id': 1,
                                  'component': 'Test Global Component',
                                  'role': 'pm',
                                  'contact': {
                                      'id': 1,
                                      'mail_name': 'maillist1',
                                      'email': 'maillist1@test.com'
                                  }
                              }
                          ]})
        with self.expect_output('global_component/detail.txt'):
            self.runner.run(['global-component', 'info', '1'])
        self.assertDictEqual(api.calls,
                             {'global-components/1': [('GET', {})],
                              'global-component-contacts':
                                  [('GET',
                                    {'component': 'Test Global Component',
                                     'page': 1})
                                   ]
                              })

    def test_update(self, api):
        self._setup_detail(api)
        api.add_endpoint('global-component-contacts',
                         'GET',
                         {'count': 1,
                          'next': None,
                          'previous': None,
                          'results': [
                              {
                                  'id': 1,
                                  'component': 'Test Global Component',
                                  'role': 'pm',
                                  'contact': {
                                      'id': 1,
                                      'mail_name': 'maillist1',
                                      'email': 'maillist1@test.com'
                                  }
                              }
                          ]})
        api.add_endpoint('global-components/1', 'PATCH', {})
        with self.expect_output('global_component/detail.txt'):
            self.runner.run(['global-component', 'update', '1', '--name', 'new test name'])
        self.assertDictEqual(api.calls,
                             {'global-components/1': [('PATCH', {'name': 'new test name'}),
                                                      ('GET', {})],
                              'global-component-contacts':
                                  [('GET',
                                    {'component': 'Test Global Component',
                                     'page': 1})
                                   ]
                              })

    def test_create(self, api):
        api.add_endpoint('global-component-contacts',
                         'GET',
                         {'count': 1,
                          'next': None,
                          'previous': None,
                          'results': [
                              {
                                  'id': 1,
                                  'component': 'Test Global Component',
                                  'role': 'pm',
                                  'contact': {
                                      'id': 1,
                                      'mail_name': 'maillist1',
                                      'email': 'maillist1@test.com'
                                  }
                              }
                          ]})
        api.add_endpoint('global-components', 'POST', self.detail)
        self._setup_detail(api)
        with self.expect_output('global_component/detail.txt'):
            self.runner.run(['global-component', 'create',
                             '--name', 'Test Global Component',
                             '--dist-git-path', 'test_global_component'])
        self.assertDictEqual(api.calls,
                             {'global-components': [('POST', {'name': 'Test Global Component',
                                                     'dist_git_path': 'test_global_component'})],
                              'global-components/1': [('GET', {})],
                              'global-component-contacts':
                                  [('GET',
                                    {'component': 'Test Global Component',
                                     'page': 1})
                                   ]
                              })

    def test_info_json(self, api):
        api.add_endpoint('global-component-contacts', 'GET', {'count': 0,
                                                              'next': None,
                                                              'previous': None,
                                                              'results': []})
        self._setup_detail(api)
        with self.expect_output('global_component/detail.json', parse_json=True):
            self.runner.run(['--json', 'global-component', 'info', '1'])
        self.assertDictEqual(api.calls,
                             {'global-components/1': [('GET', {})],
                              'global-component-contacts':
                                  [('GET',
                                    {'component': 'Test Global Component',
                                     'page': 1})
                                   ]
                              })

    def test_list_json(self, api):
        api.add_endpoint('global-components', 'GET', [self.detail])
        with self.expect_output('global_component/list.json', parse_json=True):
            self.runner.run(['--json', 'global-component', 'list',
                             '--label', 'test label'])


class ReleaseComponentTestCase(CLITestCase):
    def setUp(self):
        self.runner = Runner()
        self.runner.setup()
        self.detail = {
            'id': '1',
            'release': {
                'release_id': 'test_release',
                'active': True
            },
            'bugzilla_component': None,
            'brew_package': None,
            'global_component': 'test_global_component',
            'name': 'Test Release Component',
            'dist_git_branch': 'test_branch',
            'dist_git_web_url': 'http://pkgs.example.com/test_release_component',
            'active': True,
            'type': 'rpm',
            'srpm': None,
            'contacts': [
                {
                    'url': 'http://example.com/release-components/1/contacts/1/',
                    'contact_role': 'test_role_a',
                    'contact': {
                        'mail_name': 'Test Maillist',
                        'email': 'test_mail@example.com'
                    }
                },
                {
                    'url': 'http://example.com/release-components/1/contacts/2/',
                    'contact_role': 'test_role_b',
                    'contact': {
                        'username': 'Test User',
                        'email': 'test_user@example.com'
                    }
                }
            ]
        }

    def _setup_detail(self, api):
        api.add_endpoint('release-components/1', 'GET', self.detail)

    def test_list_without_filters(self, api):
        with self.expect_failure():
            self.runner.run(['release-component', 'list'])

    def test_list_multi_page(self, api):
        api.add_endpoint('release-components', 'GET', [
            {'id': x,
             'release': {'active': True,
                         'release_id': 'Test Release'},
             'name': 'Test Release Component %s' % x}
            for x in range(1, 26)
        ])
        with self.expect_output('release_component/list_multi_page.txt'):
            self.runner.run(['release-component', 'list',
                             '--release', 'Test Release'])
        self.assertEqual(api.calls['release-components'],
                         [('GET', {'page': 1, 'release': 'Test Release'}),
                          ('GET', {'page': 2, 'release': 'Test Release'})])

    def test_detail(self, api):
        api.add_endpoint('release-component-contacts',
                         'GET',
                         {'count': 1,
                          'next': None,
                          'previous': None,
                          'results': [
                              {
                                  'id': 1,
                                  'component': {
                                      'release': 'test_release',
                                      'id': 1,
                                      'name': 'Test Release Component'
                                  },
                                  'role': 'pm',
                                  'contact': {
                                      'id': 1,
                                      'mail_name': 'maillist1',
                                      'email': 'maillist1@test.com'
                                  }
                              }
                          ]})
        self._setup_detail(api)
        with self.expect_output('release_component/detail.txt'):
            self.runner.run(['release-component', 'info', '1'])
        self.assertDictEqual(api.calls,
                             {'release-components/1': [('GET', {})],
                              'release-component-contacts':
                                  [('GET',
                                    {'component': 'Test Release Component',
                                     'page': 1,
                                     'release': 'test_release'})
                                   ]
                              })

    def test_update(self, api):
        api.add_endpoint('release-component-contacts',
                         'GET',
                         {'count': 1,
                          'next': None,
                          'previous': None,
                          'results': [
                              {
                                  'id': 1,
                                  'component': {
                                      'release': 'test_release',
                                      'id': 1,
                                      'name': 'Test Release Component'
                                  },
                                  'role': 'pm',
                                  'contact': {
                                      'id': 1,
                                      'mail_name': 'maillist1',
                                      'email': 'maillist1@test.com'
                                  }
                              }
                          ]})
        self._setup_detail(api)
        api.add_endpoint('release-components/1', 'PATCH', {})
        with self.expect_output('release_component/detail.txt'):
            self.runner.run(['release-component', 'update', '1', '--name', 'new test name'])
        self.assertDictEqual(api.calls,
                             {'release-components/1': [('PATCH', {'name': 'new test name'}),
                                                       ('GET', {})],
                              'release-component-contacts':
                                  [('GET',
                                    {'component': 'Test Release Component',
                                     'page': 1,
                                     'release': 'test_release'})
                                   ]
                              })

    def test_create(self, api):
        api.add_endpoint('release-component-contacts',
                         'GET',
                         {'count': 1,
                          'next': None,
                          'previous': None,
                          'results': [
                              {
                                  'id': 1,
                                  'component': {
                                      'release': 'test_release',
                                      'id': 1,
                                      'name': 'Test Release Component'
                                  },
                                  'role': 'pm',
                                  'contact': {
                                      'id': 1,
                                      'mail_name': 'maillist1',
                                      'email': 'maillist1@test.com'
                                  }
                              }
                          ]})
        api.add_endpoint('release-components', 'POST', self.detail)
        self._setup_detail(api)
        with self.expect_output('release_component/detail.txt'):
            self.runner.run(['release-component', 'create',
                             '--name', 'Test Release Component',
                             '--release', 'test_release',
                             '--global-component', 'test_global_component'])
        self.assertDictEqual(api.calls,
                             {'release-components': [('POST',
                                                     {'name': 'Test Release Component',
                                                      'release': 'test_release',
                                                      'global_component': 'test_global_component'})],
                              'release-components/1': [('GET', {})],
                              'release-component-contacts':
                                  [('GET',
                                    {'component': 'Test Release Component',
                                     'page': 1,
                                     'release': 'test_release'})
                                   ]
                              })

    def test_info_json(self, api):
        api.add_endpoint('release-component-contacts', 'GET', {'count': 0,
                                                               'next': None,
                                                               'previous': None,
                                                               'results': []})
        self._setup_detail(api)
        with self.expect_output('release_component/detail.json', parse_json=True):
            self.runner.run(['--json', 'release-component', 'info', '1'])
        self.assertDictEqual(api.calls,
                             {'release-components/1': [('GET', {})],
                              'release-component-contacts':
                                  [('GET',
                                    {'component': 'Test Release Component',
                                     'page': 1,
                                     'release': 'test_release'})
                                   ]
                              })

    def test_list_json(self, api):
        api.add_endpoint('release-components', 'GET', [self.detail])
        with self.expect_output('release_component/list.json', parse_json=True):
            self.runner.run(['--json', 'release-component', 'list',
                             '--release', 'test_release'])
