#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status
from django.core.urlresolvers import reverse
from django.core.exceptions import ValidationError

from pdc.apps.bindings import models as binding_models
from pdc.apps.common.test_utils import TestCaseWithChangeSetMixin
from pdc.apps.component import models as component_models
from pdc.apps.release import models as release_models
from . import models


class RPMSortKeyTestCase(TestCase):
    def test_sort_key_precedence(self):
        data = [((0, "10", "10"), (1, "1", "1")),
                ((0, "1", "10"), (0, "10", "1")),
                ((0, "1", "1"), (0, "1", "10"))]

        for v1, v2 in data:
            p1 = models.RPM(epoch=v1[0], version=v1[1], release=v1[2])
            p2 = models.RPM(epoch=v2[0], version=v2[1], release=v2[2])
            self.assertTrue(p1.sort_key < p2.sort_key)

    def test_complex_version_sort(self):
        data = [((0, "1.0.1", "10"), (1, "1.0.2", "1")),
                ((0, "1.11.1", "10"), (0, "1.100.1", "1")),
                ((0, "1", "1.0.1"), (0, "1", "1.1")),
                ((0, "1", "11"), (0, "1", "101"))]

        for v1, v2 in data:
            p1 = models.RPM(epoch=v1[0], version=v1[1], release=v1[2])
            p2 = models.RPM(epoch=v2[0], version=v2[1], release=v2[2])
            self.assertTrue(p1.sort_key < p2.sort_key, msg="%s < %s" % (v1, v2))

    def test_handle_non_numbers(self):
        data = [((0, "svn24104.0.92", "1"), (1, "svn24104.0.93", "1")),
                ((0, "3.2.5d", "1"), (0, "3.2.5e", "1")),
                ((0, "3.2.5d", "1"), (0, "3.2.6a", "1")),
                ((0, "2.1a15", "1"), (0, "2.1a20", "1")),
                ((0, "2.1a15", "1"), (0, "2.2", "1")),
                ((0, "2.1a15", "1"), (0, "2.1", "1"))]

        for v1, v2 in data:
            p1 = models.RPM(epoch=v1[0], version=v1[1], release=v1[2])
            p2 = models.RPM(epoch=v2[0], version=v2[1], release=v2[2])
            self.assertTrue(p1.sort_key < p2.sort_key, msg="%s < %s" % (v1, v2))


class RPMSaveValidationTestCase(TestCase):
    def test_empty_srpm_nevra_with_arch_is_src(self):
        rpm = models.RPM.objects.create(name='kernel', epoch=0, version='3.19.3', release='100',
                                        arch='src', srpm_name='kernel', filename='kernel-3.19.3-100.src.rpm')
        self.assertIsNotNone(rpm)
        self.assertEqual(1, models.RPM.objects.count())

    def test_non_empty_srpm_nevra_with_arch_is_not_src(self):
        rpm = models.RPM.objects.create(name='kernel', epoch=0, version='3.19.3', release='100',
                                        arch='x86_64', srpm_name='kernel', filename='kernel-3.19.3-100.x86_64.rpm',
                                        srpm_nevra='kernel-0:3.19.3-100.x86_64')
        self.assertIsNotNone(rpm)
        self.assertEqual(1, models.RPM.objects.count())

    def test_non_empty_srpm_nevra_with_arch_is_src(self):
        with self.assertRaises(ValidationError):
            models.RPM.objects.create(name='kernel', epoch=0, version='3.19.3', release='100',
                                      arch='src', srpm_name='kernel', filename='kernel-3.19.3-100.src.rpm',
                                      srpm_nevra='kernel-0:3.19.3-100.src')
        self.assertEqual(0, models.RPM.objects.count())

    def test_empty_srpm_nevra_with_arch_is_not_src(self):
        with self.assertRaises(ValidationError):
            models.RPM.objects.create(name='kernel', epoch=0, version='3.19.3', release='100',
                                      arch='x86_64', srpm_name='kernel', filename='kernel-3.19.3-100.x86_64.rpm')
        self.assertEqual(0, models.RPM.objects.count())


class RPMAPIRESTTestCase(TestCaseWithChangeSetMixin, APITestCase):
    fixtures = [
        'pdc/apps/common/fixtures/test/sigkey.json',
        'pdc/apps/release/fixtures/tests/release.json',
        'pdc/apps/package/fixtures/test/rpm.json',
        'pdc/apps/compose/fixtures/tests/compose.json',
        'pdc/apps/compose/fixtures/tests/compose_composerpm.json',
        'pdc/apps/compose/fixtures/tests/variant_arch.json',
        'pdc/apps/compose/fixtures/tests/variant.json'
    ]

    def test_query_all_rpms(self):
        url = reverse('rpms-list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 3)

    def test_query_with_params(self):
        url = reverse('rpms-list')
        response = self.client.get(url + '?name=bash', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 1)
        response = self.client.get(url + '?epoch=0', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 3)
        response = self.client.get(url + '?version=1.2.3', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 3)
        response = self.client.get(url + '?release=4.b1', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 1)
        response = self.client.get(url + '?arch=x86_64', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 2)
        response = self.client.get(url + '?srpm_name=bash', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 3)
        response = self.client.get(url + '?srpm_nevra=bash-0:1.2.3-4.b1.src', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 1)
        response = self.client.get(url + '?srpm_nevra=null', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 1)

        response = self.client.get(url + '?compose=compose-1', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 2)
        results = response.data.get('results', [])
        ids = []
        for result in results:
            ids.append(result['id'])
        self.assertTrue(1 in ids)

    def test_query_with_multi_value_against_same_key(self):
        url = reverse('rpms-list')
        response = self.client.get(url + '?name=bash&name=bash-doc', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 2)
        response = self.client.get(url + '?srpm_nevra=bash-0:1.2.3-4.b1.src&srpm_nevra=bash-0:1.2.3-4.b2.src',
                                   format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 1)

    def test_query_with_different_key(self):
        url = reverse('rpms-list')
        response = self.client.get(url + '?name=bash&version=1.2.3', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 1)

    def test_query_with_wrong_params(self):
        url = reverse('rpms-list')
        response = self.client.get(url + 'wrong_param/', format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_query_with_only_key(self):
        url = reverse('rpms-list')
        response = self.client.get(url + '?name', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 0)
        response = self.client.get(url + '?name=', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 0)
        response = self.client.get(url + '?epoch', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 0)
        response = self.client.get(url + '?epoch=', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 0)

    def test_retrieve_rpm(self):
        url = reverse('rpms-detail', args=[1])
        response = self.client.get(url, format='json')
        expect_data = {"id": 1, "name": "bash", "version": "1.2.3", "epoch": 0, "release": "4.b1", "arch": "x86_64",
                       "srpm_name": "bash", "srpm_nevra": "bash-0:1.2.3-4.b1.src",
                       "filename": "bash-1.2.3-4.b1.x86_64.rpm", "linked_releases": [],
                       "linked_composes": ["compose-1"]}
        self.assertEqual(response.data, expect_data)

    def test_retrieve_rpm_should_not_have_duplicated_composes(self):
        url = reverse('rpms-detail', args=[2])
        response = self.client.get(url, format='json')
        self.assertEqual(response.data.get("linked_composes"), ['compose-1'])

    def test_create_rpm(self):
        url = reverse('rpms-list')
        data = {"name": "fake_bash", "version": "1.2.3", "epoch": 0, "release": "4.b1", "arch": "x86_64",
                "srpm_name": "bash", "filename": "bash-1.2.3-4.b1.x86_64.rpm", "linked_releases": ['release-1.0'],
                "srpm_nevra": "fake_bash-0:1.2.3-4.b1.src"}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        expected_response_data = {"id": 4, 'linked_composes': [],
                                  "name": "fake_bash", "version": "1.2.3", "epoch": 0, "release": "4.b1",
                                  "arch": "x86_64", "srpm_name": "bash", "filename": "bash-1.2.3-4.b1.x86_64.rpm",
                                  "linked_releases": ['release-1.0'], "srpm_nevra": "fake_bash-0:1.2.3-4.b1.src"}
        self.assertEqual(response.data, expected_response_data)
        self.assertNumChanges([1])

    def test_create_rpm_with_wrong_release(self):
        url = reverse('rpms-list')
        data = {"name": "fake_bash", "version": "1.2.3", "epoch": 0, "release": "4.b1", "arch": "x86_64",
                "srpm_name": "bash", "filename": "bash-1.2.3-4.b1.x86_64.rpm", "linked_releases": ['release-1.0-wrong'],
                "srpm_nevra": "fake_bash-0:1.2.3-4.b1.src"}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_partial_update_rpm_with_assign_release(self):
        url = reverse('rpms-detail', args=[1])
        data = {"linked_releases": ['release-1.0']}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('linked_releases'), ['release-1.0'])
        self.assertNumChanges([1])

    def test_partial_update_rpm_with_assign_wrong_release(self):
        url = reverse('rpms-detail', args=[1])
        data = {"linked_releases": ['release-1.0-fake']}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_rpm(self):
        data = {"name": "fake_bash", "version": "1.2.3", "epoch": 0, "release": "4.b1", "arch": "x86_64",
                "srpm_name": "bash", "filename": "bash-1.2.3-4.b1.x86_64.rpm", "linked_releases": ['release-1.0'],
                "srpm_nevra": "fake_bash-0:1.2.3-4.b1.src"}
        url = reverse('rpms-detail', args=[1])
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data.update({'id': 1, 'linked_composes': [u'compose-1']})
        self.assertEqual(response.data, data)
        self.assertNumChanges([1])

    def test_update_rpm_with_linked_compose_should_read_only(self):
        url = reverse('rpms-detail', args=[3])
        data = {'linked_composes': [u'compose-1']}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.data.get('linked_composes'), [])

    def test_bulk_update_patch(self):
        self.client.patch(reverse('rpms-list'),
                          {1: {"linked_releases": ['release-1.0']}}, format='json')
        url = reverse('rpms-detail', args=[1])
        response = self.client.get(url, format='json')
        self.assertEqual(response.data.get("linked_releases"), ['release-1.0'])
        self.assertNumChanges([1])

    def test_delete_rpm_should_not_be_allowed(self):
        url = reverse('rpms-detail', args=[1])
        response = self.client.delete(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_bulk_delete_rpms_should_not_be_allowed(self):
        url = reverse('rpms-list')
        response = self.client.delete(url, [1, 2], format='json')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


class ImageRESTTestCase(APITestCase):
    fixtures = [
        'pdc/apps/release/fixtures/tests/release.json',
        'pdc/apps/compose/fixtures/tests/compose.json',
        'pdc/apps/compose/fixtures/tests/variant_arch.json',
        'pdc/apps/compose/fixtures/tests/variant.json',
        'pdc/apps/package/fixtures/test/image.json',
        'pdc/apps/compose/fixtures/tests/compose_composeimage.json',
    ]

    def test_list_all(self):
        response = self.client.get(reverse('image-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 3)

    def test_query_file_name(self):
        response = self.client.get(reverse('image-list'), {'file_name': 'image-1'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 1)
        response = self.client.get(reverse('image-list'),
                                   {'file_name': ['image-1', 'image-2']})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 2)

    def test_query_image_format(self):
        response = self.client.get(reverse('image-list'), {'image_format': 'iso'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 1)
        response = self.client.get(reverse('image-list'),
                                   {'image_format': ['iso', 'qcow']})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 2)

    def test_query_image_type(self):
        response = self.client.get(reverse('image-list'), {'image_type': 'dvd'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 1)
        response = self.client.get(reverse('image-list'),
                                   {'image_type': ['dvd', 'boot']})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 2)

    def test_query_disc_number(self):
        response = self.client.get(reverse('image-list'), {'disc_number': 1})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 1)
        response = self.client.get(reverse('image-list'), {'disc_number': [1, 2]})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 2)

    def test_query_disc_count(self):
        response = self.client.get(reverse('image-list'), {'disc_count': 1})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 1)
        response = self.client.get(reverse('image-list'), {'disc_count': [1, 2]})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 2)

    def test_query_arch(self):
        response = self.client.get(reverse('image-list'), {'arch': 'src'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 1)
        response = self.client.get(reverse('image-list'), {'arch': ['src', 'x86_64']})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 2)

    def test_query_mtime(self):
        response = self.client.get(reverse('image-list'), {'mtime': 111111111})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 1)
        response = self.client.get(reverse('image-list'), {'mtime': [111111111, 222222222]})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 2)

    def test_query_size(self):
        response = self.client.get(reverse('image-list'), {'size': 444444444})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 1)
        response = self.client.get(reverse('image-list'), {'size': [444444444, 555555555]})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 2)

    def test_query_bootable(self):
        response = self.client.get(reverse('image-list'), {'bootable': True})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 1)

    def test_query_implant_md5(self):
        response = self.client.get(reverse('image-list'), {'implant_md5': 'a' * 32})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 1)
        response = self.client.get(reverse('image-list'),
                                   {'implant_md5': ['a' * 32, 'b' * 32]})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 2)

    def test_query_volume_id(self):
        response = self.client.get(reverse('image-list'), {'volume_id': 'image-1-volume_id'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 1)
        response = self.client.get(reverse('image-list'),
                                   {'volume_id': ['image-1-volume_id', 'image-2-volume_id']})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 2)

    def test_query_md5(self):
        response = self.client.get(reverse('image-list'), {'md5': '1' * 32})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 1)
        response = self.client.get(reverse('image-list'),
                                   {'md5': ['1' * 32, '2' * 32]})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 2)

    def test_query_sha1(self):
        response = self.client.get(reverse('image-list'), {'sha1': '1' * 40})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 1)
        response = self.client.get(reverse('image-list'),
                                   {'sha1': ['1' * 40, '2' * 40]})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 2)

    def test_query_sha256(self):
        response = self.client.get(reverse('image-list'), {'sha256': '1' * 64})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 1)
        response = self.client.get(reverse('image-list'),
                                   {'sha256': ['1' * 64, '2' * 64]})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 2)

    def test_query_compose(self):
        response = self.client.get(reverse('image-list'), {'compose': 'foo'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 0)
        response = self.client.get(reverse('image-list'),
                                   {'compose': ['compose-1', 'foo']})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 3)


class BuildImageRESTTestCase(TestCaseWithChangeSetMixin, APITestCase):
    fixtures = [
        'pdc/apps/package/fixtures/test/rpm.json',
        'pdc/apps/package/fixtures/test/archive.json',
        'pdc/apps/package/fixtures/test/release.json',
        'pdc/apps/package/fixtures/test/build_image.json',
    ]

    def test_create_with_new_rpms(self):
        url = reverse('buildimage-list')
        data = {'image_id': 'new_build',
                'image_format': 'docker',
                'md5': "0123456789abcdef0123456789abcdef",
                'rpms': [{'name': 'new_rpm', 'epoch': 0, 'version': '1.0.0',
                          'release': '1', 'arch': 'src', 'srpm_name': 'new_srpm'}]
                }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_with_new_incorrect_rpms_1(self):
        url = reverse('buildimage-list')
        # rpm's arch is not src but srpm_nevra is empty
        data = {'image_id': 'new_build',
                'image_format': 'docker',
                'md5': "0123456789abcdef0123456789abcdef",
                'rpms': [{'name': 'new_rpm', 'epoch': 0, 'version': '1.0.0',
                          'release': '1', 'arch': 'x86-64', 'srpm_name': 'new_srpm'}]
                }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data.get('rpms'), ["RPM's srpm_nevra should be empty if and only if arch is src"])

    def test_create_with_new_incorrect_rpms_2(self):
        url = reverse('buildimage-list')
        # rpm's arch is src but srpm_nevra is not empty
        data = {'image_id': 'new_build',
                'image_format': 'docker',
                'md5': "0123456789abcdef0123456789abcdef",
                'rpms': [{'name': 'new_rpm', 'epoch': 0, 'version': '1.0.0',
                          'release': '1', 'arch': 'src', 'srpm_name': 'new_srpm', 'srpm_nevra': 'fake_srpm_nevra'}]
                }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data.get('rpms'), ["RPM's srpm_nevra should be empty if and only if arch is src"])

    def test_create_with_exist_rpms(self):
        url = reverse('buildimage-list')
        data = {'image_id': 'new_build',
                'image_format': 'docker',
                'md5': "0123456789abcdef0123456789abcdef",
                'rpms': [{
                    "name": "bash-doc",
                    "epoch": 0,
                    "version": "1.2.3",
                    "release": "4.b2",
                    "arch": "x86_64",
                    "srpm_name": "bash",
                    "srpm_nevra": "bash-0:1.2.3-4.b2.src"}]
                }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertNumChanges([1])
        self.assertIn('bash-doc', response.content)

    def test_create_with_exist_rpm_nevra(self):
        url = reverse('buildimage-list')
        data = {'image_id': 'new_build',
                'image_format': 'docker',
                'md5': "0123456789abcdef0123456789abcdef",
                'rpms': [{
                    "name": "bash-doc",
                    "epoch": 0,
                    "version": "1.2.3",
                    "release": "4.b2",
                    "arch": "x86_64",
                    "srpm_name": "bash",
                    "srpm_nevra": "new_bash-0:1.2.3-4.b2.src"}]
                }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertNumChanges([1])
        self.assertIn('bash-doc', response.content)

    def test_create_with_new_archives(self):
        url = reverse('buildimage-list')
        data = {'image_id': 'new_build',
                'image_format': 'docker',
                'md5': "0123456789abcdef0123456789abcdef",
                'rpms': [],
                'archives': [{'build_nvr': 'new_build', 'name': 'new_name',
                              'size': 123, 'md5': '1111222233334444aaaabbbbccccdddd'}]
                }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertNumChanges([2])

    def test_create_with_exist_release_id(self):
        url = reverse('buildimage-list')
        data = {'image_id': 'new_build',
                'image_format': 'docker',
                'md5': "0123456789abcdef0123456789abcdef",
                'releases': ["release-1.0", "release-2.0"]}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_with_non_exist_release_id(self):
        url = reverse('buildimage-list')
        data = {'image_id': 'new_build',
                'image_format': 'docker',
                'md5': "0123456789abcdef0123456789abcdef",
                'releases': ["release-1.0-fake-name"]}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_with_exist_archives(self):
        url = reverse('buildimage-list')
        data = {'image_id': 'new_build',
                'image_format': 'docker',
                'md5': "0123456789abcdef0123456789abcdef",
                'rpms': [{
                    "name": "bash-doc",
                    "epoch": 0,
                    "version": "1.2.3",
                    "release": "4.b2",
                    "arch": "x86_64",
                    "srpm_name": "bash",
                    "srpm_nevra": "bash-0:1.2.3-4.b2.src"}],
                'archives': [{'build_nvr': 'my-server-docker-1.0-27', 'name': 'tdl-x86_64.xml',
                              'size': 641, 'md5': '22222222222222222222222222222222'}]
                }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertNumChanges([1])
        self.assertIn('bash-doc', response.content)

    def test_create_with_wrong_field(self):
        url = reverse('buildimage-list')
        data = {'image_id': 'new_build',
                'image_format': 'docker',
                'md5': "0123456789abcdef0123456789abcdef",
                'rpms': [],
                'archives': [{'build_name': 'new_build', 'name': 'new_name',
                              'size': 123, 'md5': '1111222233334444aaaabbbbccccdddd'}]
                }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('archives', response.content)
        self.assertIn('build_nvr', response.content)

    def test_create_with_exist_rpms_missing_fields(self):
        url = reverse('buildimage-list')
        data = {'image_id': 'new_build',
                'image_format': 'docker',
                'md5': "0123456789abcdef0123456789abcdef",
                'rpms': [{'name': 'bash-doc'}],
                'archives': []}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('rpms', response.content)
        self.assertIn('epoch', response.content)
        self.assertIn('version', response.content)
        self.assertIn('release', response.content)
        self.assertIn('arch', response.content)
        self.assertIn('srpm_name', response.content)

    def test_create_with_new_rpms_missing_fields(self):
        url = reverse('buildimage-list')
        data = {'image_id': 'new_build',
                'image_format': 'docker',
                'md5': "0123456789abcdef0123456789abcdef",
                'rpms': [{'name': 'new_rpm'}],
                'archives': []}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('rpms', response.content)
        self.assertIn('epoch', response.content)
        self.assertIn('version', response.content)
        self.assertIn('release', response.content)
        self.assertIn('arch', response.content)
        self.assertIn('srpm_name', response.content)

    def test_create_with_exist_archives_missing_fields(self):
        url = reverse('buildimage-list')
        data = {'image_id': 'new_build',
                'image_format': 'docker',
                'md5': "0123456789abcdef0123456789abcdef",
                'rpms': [],
                'archives': [{'build_nvr': 'my-server-docker-1.0-27'}]
                }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('archives', response.content)
        self.assertIn('name', response.content)
        self.assertIn('size', response.content)
        self.assertIn('md5', response.content)

    def test_create_with_new_archives_missing_fields(self):
        url = reverse('buildimage-list')
        data = {'image_id': 'new_build',
                'image_format': 'docker',
                'md5': "0123456789abcdef0123456789abcdef",
                'rpms': [],
                'archives': [{'build_nvr': 'new_build'}]
                }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('archives', response.content)
        self.assertIn('name', response.content)
        self.assertIn('size', response.content)
        self.assertIn('md5', response.content)

    def test_get(self):
        url = reverse('buildimage-detail', args=[1])
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_list(self):
        url = reverse('buildimage-list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 2)

    def test_query_with_component_name(self):
        url = reverse('buildimage-list')
        response = self.client.get(url + '?component_name=bash', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 1)

    def test_query_component_name_with_srpm_name_mapping(self):
        rpm = models.RPM.objects.create(
            name='kernel', epoch=0, version='3.19.3', release='100',
            arch='src', srpm_name='kernel', filename='kernel-3.19.3-100.src.rpm')
        build_image = models.BuildImage.objects.first()
        build_image.rpms.add(rpm)

        global_component = component_models.GlobalComponent.objects.create(name='bash')
        release = release_models.Release.objects.create(
            release_type=release_models.ReleaseType.objects.get(short='ga'),
            short='release',
            version='1.1',
            name='Awesome Release')
        release_component = component_models.ReleaseComponent.objects.create(
            global_component=global_component,
            release=release,
            name='bash')
        binding_models.ReleaseComponentSRPMNameMapping.objects.create(
            srpm_name='kernel',
            release_component=release_component)

        url = reverse('buildimage-list')
        response = self.client.get(url + '?component_name=bash', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 1)
        self.assertIn('kernel', response.content)

    def test_query_component_name_without_srpm_name_mapping(self):
        rpm = models.RPM.objects.create(
            name='kernel', epoch=0, version='3.19.3', release='100',
            arch='src', srpm_name='kernel', filename='kernel-3.19.3-100.src.rpm')
        build_image = models.BuildImage.objects.first()
        build_image.rpms.add(rpm)

        global_component = component_models.GlobalComponent.objects.create(name='kernel')
        release = release_models.Release.objects.create(
            release_type=release_models.ReleaseType.objects.get(short='ga'),
            short='release',
            version='7.1',
            name='Awesome Release')
        component_models.ReleaseComponent.objects.create(
            global_component=global_component,
            release=release,
            name='kernel')

        url = reverse('buildimage-list')
        response = self.client.get(url + '?component_name=kernel', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 1)
        self.assertIn('kernel', response.content)

    def test_query_with_rpm_version(self):
        url = reverse('buildimage-list')
        response = self.client.get(url + '?rpm_version=1.2.3', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 1)

    def test_query_with_rpm_release(self):
        url = reverse('buildimage-list')
        response = self.client.get(url + '?rpm_release=4.b1', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 1)

    def test_query_with_image_id(self):
        url = reverse('buildimage-list')
        response = self.client.get(url + '?image_id=my-server-docker-1.0-27', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 1)
        self.assertEqual(response.data.get('results')[0].get('image_id'), 'my-server-docker-1.0-27')

    def test_query_with_archive_build_nvr(self):
        url = reverse('buildimage-list')
        response = self.client.get(url + '?archive_build_nvr=my-server-docker-1.0-27', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 2)

    def test_query_with_image_format(self):
        url = reverse('buildimage-list')
        response = self.client.get(url + '?image_format=docker', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 2)

    def test_query_with_md5(self):
        url = reverse('buildimage-list')
        response = self.client.get(url + '?md5=0123456789abcdef0123456789abcdef',
                                   format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 1)

    def test_query_with_archive_name(self):
        url = reverse('buildimage-list')
        response = self.client.get(url + '?archive_name=archive_1', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 1)

    def test_query_with_archive_size(self):
        url = reverse('buildimage-list')
        response = self.client.get(url + '?archive_size=666', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 1)

    def test_query_with_archive_md5(self):
        url = reverse('buildimage-list')
        response = self.client.get(url + '?archive_md5=22222222222222222222222222222222', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 2)

    def test_query_with_release_id(self):
        url = reverse('buildimage-list')
        response = self.client.get(url + '?release_id=release-1.0', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 2)

        response = self.client.get(url + '?release_id=release-2.0', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 1)

    def test_update_image_with_release_id(self):
        url = reverse('buildimage-detail', args=[1])
        data = {"releases": ["release-1.0", "release-2.0"]}
        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('releases'), ["release-1.0", "release-2.0"])
        self.assertNumChanges([1])

    def test_patch_update(self):
        url = reverse('buildimage-detail', args=[1])
        data = {'image_id': 'new_build'}
        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('image_id'), 'new_build')

    def test_partial_update_empty(self):
        response = self.client.patch(reverse('buildimage-detail', args=[1]), {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_patch_update_failed(self):
        url = reverse('buildimage-detail', args=[1])
        data = {'image_format': 'new_format'}
        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data.get('image_format'), ["Object with name=new_format does not exist."])

    def test_put_update(self):
        url = reverse('buildimage-detail', args=[1])
        data = {'image_id': 'new_build',
                'image_format': 'docker',
                'md5': "0123456789abcdef0123456789abcdef",
                'rpms': [{
                    "name": "new_rpm",
                    "epoch": 0,
                    "version": "0.1.0",
                    "release": "1",
                    "arch": "x86_64",
                    "srpm_name": "new_srpm",
                    "srpm_nevra": "new_srpm_nevra"}],
                'archives': [{'build_nvr': 'new_build', 'name': 'new_name',
                              'size': 123, 'md5': '1111222233334444aaaabbbbccccdddd'}]
                }
        response = self.client.put(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNumChanges([3])
        self.assertIn('new_rpm', response.content)

    def test_delete(self):
        url = reverse('buildimage-detail', args=[1])
        response = self.client.delete(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertNumChanges([1])
