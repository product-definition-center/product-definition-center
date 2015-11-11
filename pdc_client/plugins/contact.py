# -*- coding: utf-8 -*-
#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
import json
import sys

from pdc_client import get_paged
from pdc_client.plugin_helpers import (PDCClientPlugin,
                                       extract_arguments,
                                       add_create_update_args)


class GlobalComponentContactPlugin(PDCClientPlugin):
    def register(self):
        self.set_command('global-component-contact')

        list_parser = self.add_action('list', help='list all global component contacts')
        self.add_query_arguments(list_parser)
        list_parser.set_defaults(func=self.list_global_component_contacts)

        info_parser = self.add_action('info', help='display details of a global component contact')
        info_parser.add_argument('global_component_contact_id', metavar='GLOBAL_COMPONENT_CONTACT_ID')
        info_parser.set_defaults(func=self.info_global_component_contact)

        create_parser = self.add_action('create', help='create new global component contact')
        self.add_create_arguments(create_parser, required=True)
        create_parser.set_defaults(func=self.create_global_component_contact)

        delete_parser = self.add_action('delete', help='delete a global component contact')
        delete_parser.add_argument('global_component_contact_id', metavar='GLOBAL_COMPONENT_CONTACT_ID')
        delete_parser.set_defaults(func=self.delete_global_component_contact)

        query_delete_parser = self.add_action('delete-match', help='delete unique matched global component contact')
        self.add_query_arguments(query_delete_parser)
        query_delete_parser.set_defaults(func=self.delete_matched_global_component_contact)

    def add_query_arguments(self, parser, required=False):
        filters = ('component contact role email'.split())
        for arg in filters:
            parser.add_argument('--' + arg.replace('_', '-'), dest='filter_' + arg)

    def add_create_arguments(self, parser, required=True):
        add_create_update_args(parser,
                               {'component': {},
                                'role': {},
                                'contact__email': {'arg': 'email'}},
                               {'contact__username': {'arg': 'username'},
                                'contact__mail_name': {'arg': 'mail-name'},
                                },
                               required)

    def list_global_component_contacts(self, args):
        filters = extract_arguments(args, prefix='filter_')
        if not filters:
            sys.stderr.write('At least some filter must be used.\n')
            sys.exit(1)
        global_component_contacts = get_paged(self.client['global-component-contacts']._, **filters)

        if args.json:
            print json.dumps(list(global_component_contacts))
            return
        if global_component_contacts:
            self.print_component_contacts(global_component_contacts)

    def print_component_contacts(self, global_component_contacts):
        fmt = '{:<10} {:25} {:10} {:25} {}'
        print fmt.format('ID', 'Component', 'Role', 'Email', 'Name')
        for global_component_contact in global_component_contacts:
            print fmt.format(
                global_component_contact['id'],
                global_component_contact['component'],
                global_component_contact['role'],
                global_component_contact['contact']['email'],
                'username' in global_component_contact['contact'] and
                global_component_contact['contact']['username'] or
                global_component_contact['contact']['mail_name']
            )

    def info_global_component_contact(self, args, global_component_contact_id=None):
        global_component_contact_id = global_component_contact_id or args.global_component_contact_id
        global_component_contact = self.client['global-component-contacts'][global_component_contact_id]._()

        if args.json:
            print json.dumps(global_component_contact)
            return

        fmt = '{:20} {}'
        print fmt.format('ID:', global_component_contact['id'])
        print fmt.format('Component:', global_component_contact['component'])
        print fmt.format('Role:', global_component_contact['role'])
        print 'Contact:'
        for name in ('username', 'mail_name'):
            if name in global_component_contact['contact']:
                print ''.join(['\tName:\t', global_component_contact['contact'][name]])
        print ''.join(['\tEmail:\t', global_component_contact['contact']['email']])

    def create_global_component_contact(self, args):
        data = extract_arguments(args)
        self.logger.debug('Creating global component contact with data %r', data)
        response = self.client['global-component-contacts']._(data)
        self.info_global_component_contact(args, response['id'])

    def delete_global_component_contact(self, args):
        data = extract_arguments(args)
        self.logger.debug('Deleting global component contact: %s',
                          args.global_component_contact_id)
        self.client['global-component-contacts'
                    ][args.global_component_contact_id]._("DELETE", data)

    def delete_matched_global_component_contact(self, args):
        filters = extract_arguments(args, prefix='filter_')
        if not filters:
            sys.stderr.write('At least some filter must be used.\n')
            sys.exit(1)
        global_component_contacts = get_paged(self.client['global-component-contacts']._, **filters)

        global_component_contacts = list(global_component_contacts)
        match_count = len(global_component_contacts)
        if match_count == 1:
            self.client['global-component-contacts'
                        ][global_component_contacts[0]['id']]._("DELETE", {})
        elif match_count < 1:
            print "No match, nothing to do."
        else:
            print "Multi matches, please delete via ID or provide more restrictions."
            self.print_component_contacts(global_component_contacts)


PLUGIN_CLASSES = [GlobalComponentContactPlugin]
