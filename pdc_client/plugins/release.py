# -*- coding: utf-8 -*-
#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
import json

from pdc_client import get_paged
from pdc_client.plugin_helpers import (PDCClientPlugin,
                                       extract_arguments,
                                       add_create_update_args)


class ReleasePlugin(PDCClientPlugin):
    def register(self):
        self.set_command('release')

        list_parser = self.add_action('list', help='list all releases')
        list_parser.add_argument('--inactive', action='store_true',
                                 help='show only inactive releases')
        list_parser.add_argument('--all', action='store_true',
                                 help='show both active and inactive releases')
        list_parser.set_defaults(func=self.list_releases)

        info_parser = self.add_action('info', help='display details of a release')
        info_parser.add_argument('release_id', metavar='RELEASE_ID')
        info_parser.set_defaults(func=self.release_info)

        update_parser = self.add_action('update', help='update an existing release')
        update_parser.add_argument('release_id', metavar='RELEASE_ID')
        self.add_release_arguments(update_parser)
        update_parser.set_defaults(func=self.release_update)

        create_parser = self.add_action('create', help='create new release')
        self.add_release_arguments(create_parser, required=True)
        create_parser.set_defaults(func=self.release_create)

        clone_parser = self.add_action('clone', help='clone new release from an existed one',
                                       description=('NOTE: At least one of `short`, `version`, '
                                                    '`base_product` or `release_type` '
                                                    'is required.'))
        clone_parser.add_argument('old_release_id', metavar='OLD_RELEASE_ID')
        self.add_clone_arguments(clone_parser, required=False)
        clone_parser.set_defaults(func=self.release_clone)

    def add_release_arguments(self, parser, required=False):
        group = parser.add_mutually_exclusive_group()
        group.add_argument('--activate', action='store_const', const=True, dest='active')
        group.add_argument('--deactivate', action='store_const', const=False, dest='active')

        required_args = {
            'version': {},
            'short': {},
            'release_type': {},
            'name': {}}
        optional_args = {
            'product_version': {},
            'base_product': {},
            'bugzilla__product': {'arg': 'bugzilla-product'},
            'dist_git__branch': {'arg': 'dist-git-branch'}}
        add_create_update_args(parser, required_args, optional_args, required)

        self.run_hook('release_parser_setup', parser)

    def add_clone_arguments(self, parser, required=False):
        active_group = parser.add_mutually_exclusive_group()
        active_group.add_argument('--activate', action='store_const', const=True, dest='active')
        active_group.add_argument('--deactivate', action='store_const', const=False, dest='active')

        optional_args = {
            'short': {},
            'version': {},
            'release_type': {},
            'base_product': {},
            'name': {},
            'product_version': {},
            'bugzilla__product': {'arg': 'bugzilla-product'},
            'dist_git__branch': {'arg': 'dist-git-branch'},
            'component_dist_git_branch': {},
            'include_inactive': {},
            'include_trees': {},
            'integrated_with': {}
        }
        add_create_update_args(parser, {}, optional_args, required)

        self.run_hook('release_parser_setup', parser)

    def list_releases(self, args):
        filters = {}
        if args.inactive:
            filters['active'] = False
        elif not args.all:
            filters['active'] = True

        releases = get_paged(self.client.releases._, **filters)
        if args.json:
            print json.dumps(list(releases))
            return

        fmt = '{:25} {:35} {}'
        for release in releases:
            print fmt.format(release['release_id'], release['name'],
                             'active' if release['active'] else 'inactive')

    def release_info(self, args, release_id=None):
        release_id = release_id or args.release_id
        release = self.client.releases[release_id]._()
        variants = get_paged(self.client['release-variants']._, release=release_id)
        if args.json:
            release['variants'] = list(variants)
            print json.dumps(release)
            return

        fmt = '{:20} {}'
        print fmt.format('Release ID', release['release_id'])
        print fmt.format('Name', release['name'])
        print fmt.format('Short Name', release['short'])
        print fmt.format('Version', release['version'])
        print fmt.format('Release Type', release['release_type'])
        print fmt.format('Product Version', release['product_version'] or '')
        print fmt.format('Base Product', release['base_product'] or '')
        print fmt.format('Activity', 'active' if release['active'] else 'inactive')
        print fmt.format('Integrated With', release['integrated_with'] or '')

        # Call plugins
        self.run_hook('release_info', release)

        if release['bugzilla']:
            print '\nBugzilla'
            print fmt.format('Product', release['bugzilla']['product'])

        if release['dist_git']:
            print '\nDist Git'
            print fmt.format('Branch', release['dist_git']['branch'])

        print '\nVariants'
        fmt = '{:25} {:20} {:20} {:15} {}'
        print fmt.format('UID', 'ID', 'Name', 'Type', 'Arches')
        for variant in variants:
            print fmt.format(variant['uid'], variant['id'], variant['name'],
                             variant['type'], ', '.join(variant['arches']))

    def release_update(self, args):
        data = self.get_release_data(args)

        release_id = None
        if data:
            self.logger.debug('Updating release {} with data {}'.format(args.release_id, data))
            response = self.client.releases[args.release_id]._('PATCH', data)
            release_id = response['release_id']
        else:
            self.logger.info('No change required, not making a request')

        self.release_info(args, release_id)

    def release_create(self, args):
        data = self.get_release_data(args)
        self.logger.debug('Creating release with data {}'.format(data))
        response = self.client.releases._(data)
        self.release_info(args, response['release_id'])

    def release_clone(self, args):
        data = self.get_release_data(args)
        if not any(key in data for key in ['short', 'version', 'base_product', 'release_type']):
            self.subparsers.choices.get('clone').error(
                ('At least one of `short`, `version`, `base_product` '
                 'or `release_type` is required.'))
        data['old_release_id'] = args.old_release_id
        self.logger.debug('Clone release with data {}'.format(data))
        response = self.client.rpc.release.clone._(data)
        self.release_info(args, response['release_id'])

    def get_release_data(self, args):
        data = extract_arguments(args)
        if args.active is not None:
            data['active'] = args.active

        self.run_hook('release_update_prepare', args, data)

        return data


PLUGIN_CLASSES = [ReleasePlugin]
