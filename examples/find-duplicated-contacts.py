#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Find components defining more than one contact with the same role.

In older versions of PDC, it was possible to have multiple contacts with the
same role. When limits for cardinality of this relationship were introduced, we
need to find all components that would not pass the new rules.

This script does exactly that. It iterates over all global and release
components and prints details about any component with duplicate contacts.
"""

import pdc_client

client = pdc_client.PDCClient('prod')


def run(resource):
    print 'Running tests for {}'.format(resource)
    for component in pdc_client.get_paged(client[resource]._):
        pk = component['id']
        name = component['name']
        release = component.get('release', {}).get('release_id', '[global]')

        seen_roles = set()
        for contact in component['contacts']:
            if contact['contact_role'] in seen_roles:
                print 'Duplicated roles for {}:{}/{}'.format(pk, release, name)
            seen_roles.add(contact['contact_role'])
    print ''

run('global-components')
run('release-components')
