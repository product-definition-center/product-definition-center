# -*- coding: utf-8 -*-
#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
import sys
import json

from pdc_client import get_paged
from pdc_client.plugin_helpers import (PDCClientPlugin,
                                       add_parser_arguments,
                                       extract_arguments,
                                       add_create_update_args)


def update_component_contacts(component, component_contacts):
    contacts = []
    if component_contacts:
        for contact in component_contacts:
            contact.pop('component')
            contacts.append(contact)
        component['contacts'] = contacts


class GlobalComponentPlugin(PDCClientPlugin):
    def register(self):
        self.set_command('global-component')

        list_parser = self.add_action('list', help='list all global components')
        filters = ('dist_git_path contact_role email label name upstream_homepage upstream_scm_type '
                   'upstream_scm_url'.split())
        for arg in filters:
            list_parser.add_argument('--' + arg.replace('_', '-'), dest='filter_' + arg)
        list_parser.set_defaults(func=self.list_global_components)

        info_parser = self.add_action('info', help='display details of a global component')
        info_parser.add_argument('global_component_id', metavar='GLOBAL_COMPONENT_ID')
        info_parser.set_defaults(func=self.global_component_info)

        update_parser = self.add_action('update', help='update an existing global component')
        update_parser.add_argument('global_component_id', metavar='GLOBAL_COMPONENT_ID')
        self.add_global_component_arguments(update_parser)
        update_parser.set_defaults(func=self.global_component_update)

        create_parser = self.add_action('create', help='create new global component')
        self.add_global_component_arguments(create_parser, required=True)
        create_parser.set_defaults(func=self.global_component_create)

    def add_global_component_arguments(self, parser, required=False):
        add_create_update_args(parser,
                               {'name': {}},
                               {'dist_git_path': {}},
                               required)
        add_parser_arguments(parser, {
            'upstream__homepage': {'arg': 'homepage'},
            'upstream__scm_type': {'arg': 'scm-type'},
            'upstream__scm_url': {'arg': 'scm-url'}},
            group='Upstream (optional)')

    def list_global_components(self, args):
        filters = extract_arguments(args, prefix='filter_')
        if not filters:
            self.subparsers.choices.get('list').error('At least some filter must be used.')
        global_components = get_paged(self.client['global-components']._, **filters)

        if args.json:
            print json.dumps(list(global_components))
            return

        if global_components:
            for global_component in global_components:
                print '{:<10} {}'.format(
                      global_component['id'],
                      global_component['name'])

    def global_component_info(self, args, global_component_id=None):
        global_component_id = global_component_id or args.global_component_id
        global_component = self.client['global-components'][global_component_id]._()

        component_contacts = get_paged(self.client['global-component-contacts']._,
                                       component=global_component['name'])
        update_component_contacts(global_component, component_contacts)

        if args.json:
            print json.dumps(global_component)
            return

        fmt = '{:20} {}'
        print fmt.format('ID', global_component['id'])
        print fmt.format('Name', global_component['name'])
        print fmt.format('Dist Git Path', global_component['dist_git_path'] or '')
        print fmt.format('Dist Git URL', global_component['dist_git_web_url'] or '')
        if global_component['labels']:
            print 'Labels:'
            for label in global_component['labels']:
                print ''.join(['\t', label['name']])

        if global_component['upstream']:
            print 'Upstream:'
            for key in ('homepage', 'scm_type', 'scm_url'):
                print ''.join(['\t', key, ':', '\t', global_component['upstream'][key]])

        if global_component['contacts']:
            print 'Contacts:'
            for global_component_contact in global_component['contacts']:
                print ''.join(['\tRole:\t', global_component_contact['role']])
                for name in ('username', 'mail_name'):
                    if name in global_component_contact['contact']:
                        print ''.join(['\t\tName:\t', global_component_contact['contact'][name]])
                print ''.join(['\t\tEmail:\t', global_component_contact['contact']['email']])

    def global_component_create(self, args):
        data = extract_arguments(args)
        self.logger.debug('Creating global component with data %r', data)
        response = self.client['global-components']._(data)
        self.global_component_info(args, response['id'])

    def global_component_update(self, args):
        data = extract_arguments(args)
        if data:
            self.logger.debug('Updating global component %s with data %r',
                              args.global_component_id, data)
            self.client['global-components'][args.global_component_id]._ += data
        else:
            self.logger.debug('Empty data, skipping request')
        self.global_component_info(args)


class ReleaseComponentPlugin(PDCClientPlugin):
    def register(self):
        self.set_command('release-component')

        list_parser = self.add_action('list', help='list all release components')
        self.add_include_inactive_release_argument(list_parser)
        filters = ('active brew_package bugzilla_component contact_role email global_component name release srpm_name '
                   'type'.split())
        for arg in filters:
            list_parser.add_argument('--' + arg.replace('_', '-'), dest='filter_' + arg)
        list_parser.set_defaults(func=self.list_release_components)

        info_parser = self.add_action('info', help='display details of a release component')
        self.add_include_inactive_release_argument(info_parser)
        info_parser.add_argument('release_component_id', metavar='RELEASE_COMPONENT_ID')
        info_parser.set_defaults(func=self.release_component_info)

        update_parser = self.add_action('update', help='update an existing release component')
        update_parser.add_argument('release', metavar='RELEASE')
        update_parser.add_argument('name', metavar='NAME')
        self.add_release_component_arguments(update_parser)
        update_parser.set_defaults(func=self.release_component_update)

        create_parser = self.add_action('create', help='create new release component')
        self.add_release_component_arguments(create_parser, required=True)
        create_parser.add_argument('--release', dest='release', required=True)
        create_parser.add_argument('--global-component', dest='global_component', required=True)
        create_parser.set_defaults(func=self.release_component_create)

    def add_include_inactive_release_argument(self, parser):
        parser.add_argument('--include-inactive-release', action='store_true',
                            help='show component(s) in both active and inactive releases')

    def add_release_component_arguments(self, parser, required=False):
        group = parser.add_mutually_exclusive_group()
        group.add_argument('--activate', action='store_const', const=True, dest='active')
        group.add_argument('--deactivate', action='store_const', const=False, dest='active')
        add_create_update_args(parser,
                               {'name': {}},
                               {'dist_git_branch': {},
                                'bugzilla_component': {},
                                'brew_package': {},
                                'type': {},
                                'srpm__name': {'arg': 'srpm-name'}},
                               required)

    def list_release_components(self, args):
        filters = extract_arguments(args, prefix='filter_')
        if not filters:
            self.subparsers.choices.get('list').error('At least some filter must be used.')
        if 'include_inactive_release' in args and args.include_inactive_release:
            filters['include_inactive_release'] = True
        release_components = get_paged(self.client['release-components']._, **filters)

        if args.json:
            print json.dumps(list(release_components))
            return

        if release_components:
            for release_component in release_components:
                release_id = self._get_release_id(release_component)
                print '{:<10} {:25} {}'.format(
                      release_component['id'],
                      release_id,
                      release_component['name'])

    def release_component_info(self, args, release_component_id=None):
        release_component_id = release_component_id or args.release_component_id
        if 'include_inactive_release' in args and args.include_inactive_release:
            release_component = self.client['release-components'][release_component_id]._(
                include_inactive_release=args.include_inactive_release)
        else:
            release_component = self.client['release-components'][release_component_id]._()
        release_id = self._get_release_id(release_component)

        component_contacts = get_paged(self.client['release-component-contacts']._,
                                       component=release_component['name'],
                                       release=release_id)
        update_component_contacts(release_component, component_contacts)

        if args.json:
            print json.dumps(release_component)
            return

        fmt = '{:20} {}'
        print fmt.format('ID', release_component['id'])
        print fmt.format('Name', release_component['name'])
        print fmt.format('Release ID', release_id)
        print fmt.format('Global Component', release_component['global_component'])
        print fmt.format('Bugzilla Component',
                         release_component['bugzilla_component']['name']
                         if release_component['bugzilla_component'] else '')
        print fmt.format('Brew Package', release_component['brew_package'] or '')
        print fmt.format('Dist Git Branch', release_component['dist_git_branch'] or '')
        print fmt.format('Dist Git URL', release_component['dist_git_web_url'] or '')
        print fmt.format('Activity', 'active' if release_component['active'] else 'inactive')
        print fmt.format('Type', release_component['type'])
        print fmt.format('Srpm Name', release_component['srpm']['name'] if release_component['srpm'] else 'null')

        if release_component['contacts']:
            print 'Contacts:'
            for release_component_contact in release_component['contacts']:
                print ''.join(['\tRole:\t', release_component_contact['role']])
                for name in ('username', 'mail_name'):
                    if name in release_component_contact['contact']:
                        print ''.join(['\t\tName:\t', release_component_contact['contact'][name]])
                print ''.join(['\t\tEmail:\t', release_component_contact['contact']['email']])

    def release_component_create(self, args):
        data = extract_arguments(args)
        if args.release is not None:
            data['release'] = args.release
        if args.global_component is not None:
            data['global_component'] = args.global_component
        if args.active is not None:
            data['active'] = args.active
        self.logger.debug('Creating release component with data %r', data)
        response = self.client['release-components']._(data)
        self.release_component_info(args, response['id'])

    def _get_release_component_id(self, release, component_name):
        release_components = self.client['release-components']._(name=component_name, release=release)
        if not release_components['count']:
            return None
        return release_components['results'][0]['id']

    def release_component_update(self, args):
        data = extract_arguments(args)
        release_component_id = self._get_release_component_id(args.release, args.name)
        if not release_component_id:
            sys.stderr.write("The specified release component doesn't exist.\n")
            sys.exit(1)
        args.release_component_id = release_component_id
        if args.active is not None:
            data['active'] = args.active
        if data:
            self.logger.debug('Updating release component %d with data %r',
                              release_component_id, data)
            self.client['release-components'][release_component_id]._ += data
        else:
            self.logger.debug('Empty data, skipping request')
        self.release_component_info(args)

    def _get_release_id(self, release_component):
        return (release_component['release']['active'] and release_component['release']['release_id'] or
                ' '.join([release_component['release']['release_id'], '(inactive)']))

PLUGIN_CLASSES = [GlobalComponentPlugin, ReleaseComponentPlugin]
