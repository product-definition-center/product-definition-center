#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
import argparse

from beanbag import BeanBagException
from pdc_client import PDCClient


RELEASES_RESOURCE = 'releases'
RPMS_RESOURCE = 'rpms'
GLOBAL_COMPONENTS_RESOURCE = 'global-components'
RELEASE_COMPONENTS_RESOURCE = 'release-components'
BATCH_NUM = 200


def _find_latest_compose_id_for_release(release):
    try:
        release_info = client[RELEASES_RESOURCE][release]._()
        if release_info['compose_set']:
            return release_info['compose_set'][-1]

    except BeanBagException as e:
        if e.response.status_code == 404:
            return None
        raise


def _find_src_rpm_names_for_compose(compose_id):
    condition = {'arch': 'src', 'compose': compose_id, 'page_size': -1}
    return set([item['name'] for item in client[RPMS_RESOURCE]._(**condition)])


def _bulk_insert_resource(resource_name, data_list):
    data_list_len = len(data_list)
    current_index = 0
    while data_list_len > current_index + BATCH_NUM:
        inserting_data = data_list[current_index: current_index + BATCH_NUM]
        client[resource_name]._(inserting_data)
        current_index += BATCH_NUM

    if current_index < data_list_len:
        inserting_data = data_list[current_index:]
        client[resource_name]._(inserting_data)


def _generate_global_components(name_set):
    condition = {'page_size': -1}
    existing_gc_name_set = set([item['name'] for item in client[GLOBAL_COMPONENTS_RESOURCE]._(**condition)])
    non_existing_set = name_set - existing_gc_name_set
    if non_existing_set:
        print "About to insert %d global components." % len(non_existing_set)
        _bulk_insert_resource(GLOBAL_COMPONENTS_RESOURCE, [{'name': item} for item in non_existing_set])
        print "Inserted %d global components." % len(non_existing_set)


def _generate_release_components(release, name_set):
    condition = {'page_size': -1, 'release': release}
    existing_rc_name_set = set([item['name'] for item in client[RELEASE_COMPONENTS_RESOURCE]._(**condition)])
    non_existing_set = name_set - existing_rc_name_set
    if non_existing_set:
        print "About to insert %d release components." % len(non_existing_set)
        _bulk_insert_resource(RELEASE_COMPONENTS_RESOURCE,
                              [{'name': item, 'release': release, 'global_component': item}
                               for item in non_existing_set])
        print "Inserted %d release components." % len(non_existing_set)


def main(release):
    compose_id = _find_latest_compose_id_for_release(release)
    if not compose_id:
        print "The release %s doesn't exist or no compose in it." % release
        exit(1)
    srpm_name_result = _find_src_rpm_names_for_compose(compose_id)
    if srpm_name_result:
        _generate_global_components(srpm_name_result)
        _generate_release_components(release, srpm_name_result)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Create release components according release id')
    parser.add_argument('-s', '--server', help='PDC instance url or shortcut.', required=True)
    parser.add_argument("-r", "--release", help="release id for a release.", required=True)

    options = parser.parse_args()
    try:
        client = PDCClient(options.server)
        main(options.release)
    except BeanBagException as e:
        print "%d %s" % (e.response.status_code, e.response.content)
    except Exception as e:
        print str(e)
