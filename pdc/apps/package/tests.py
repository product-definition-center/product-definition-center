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


class RPMDepsFilterAPITestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        """
        15 packages are created. They all have name test-X, where X is a
        number. Each packages has a dependency of each type with the same
        constraint. They are summarized in the table below.

             0 (=1.0)    1 (<1.0)    2 (>1.0)    3 (<=1.0)   4 (>=1.0)
             5 (=2.0)    6 (<2.0)    7 (>2.0)    8 (<=2.0)   9 (>=2.0)
            10 (=3.0)   11 (<3.0)   12 (>3.0)   13 (<=3.0)  14 (>=3.0)
        """
        counter = 0
        for version in ['1.0', '2.0', '3.0']:
            for op in '= < > <= >='.split():
                name = 'test-{counter}'.format(counter=counter)
                counter += 1
                rpm = models.RPM.objects.create(name=name, epoch=0, version='1.0',
                                                release='1', arch='x86_64', srpm_name='test-pkg',
                                                srpm_nevra='test-pkg-1.0.1.x86_64',
                                                filename='dummy')
                for type in [t[0] for t in models.Dependency.DEPENDENCY_TYPE_CHOICES]:
                    rpm.dependency_set.create(name='pkg', version=version,
                                              type=type, comparison=op)

    #
    # No contraint tests
    #

    def test_filter_without_version_requires(self):
        response = self.client.get(reverse('rpms-list'), {'requires': 'pkg'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 15)

    def test_filter_without_version_suggests(self):
        response = self.client.get(reverse('rpms-list'), {'suggests': 'pkg'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 15)

    def test_filter_without_version_obsoletes(self):
        response = self.client.get(reverse('rpms-list'), {'obsoletes': 'pkg'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 15)

    def test_filter_without_version_recommends(self):
        response = self.client.get(reverse('rpms-list'), {'recommends': 'pkg'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 15)

    def test_filter_without_version_provides(self):
        response = self.client.get(reverse('rpms-list'), {'provides': 'pkg'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 15)

    def test_filter_without_version_conflicts(self):
        response = self.client.get(reverse('rpms-list'), {'conflicts': 'pkg'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 15)

    #
    # Equality contraint tests
    #

    def test_filter_with_version_equality_requires(self):
        response = self.client.get(reverse('rpms-list'), {'requires': 'pkg=2.0'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertItemsEqual([pkg['name'] for pkg in response.data['results']],
                              ['test-{}'.format(i) for i in [2, 4, 5, 8, 9, 11, 13]])

    def test_filter_with_version_equality_suggests(self):
        response = self.client.get(reverse('rpms-list'), {'suggests': 'pkg=2.0'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertItemsEqual([pkg['name'] for pkg in response.data['results']],
                              ['test-{}'.format(i) for i in [2, 4, 5, 8, 9, 11, 13]])

    def test_filter_with_version_equality_obsoletes(self):
        response = self.client.get(reverse('rpms-list'), {'obsoletes': 'pkg=2.0'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertItemsEqual([pkg['name'] for pkg in response.data['results']],
                              ['test-{}'.format(i) for i in [2, 4, 5, 8, 9, 11, 13]])

    def test_filter_with_version_equality_recommends(self):
        response = self.client.get(reverse('rpms-list'), {'recommends': 'pkg=2.0'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertItemsEqual([pkg['name'] for pkg in response.data['results']],
                              ['test-{}'.format(i) for i in [2, 4, 5, 8, 9, 11, 13]])

    def test_filter_with_version_equality_provides(self):
        response = self.client.get(reverse('rpms-list'), {'provides': 'pkg=2.0'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertItemsEqual([pkg['name'] for pkg in response.data['results']],
                              ['test-{}'.format(i) for i in [2, 4, 5, 8, 9, 11, 13]])

    def test_filter_with_version_equality_conflicts(self):
        response = self.client.get(reverse('rpms-list'), {'conflicts': 'pkg=2.0'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertItemsEqual([pkg['name'] for pkg in response.data['results']],
                              ['test-{}'.format(i) for i in [2, 4, 5, 8, 9, 11, 13]])

    #
    # Greater than constraint tests
    #

    def test_filter_with_greater_version_requires(self):
        response = self.client.get(reverse('rpms-list'), {'requires': 'pkg>2.0'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertItemsEqual([pkg['name'] for pkg in response.data['results']],
                              ['test-{}'.format(i) for i in [2, 4, 7, 9, 10, 11, 12, 13, 14]])

    def test_filter_with_greater_version_suggests(self):
        response = self.client.get(reverse('rpms-list'), {'suggests': 'pkg>2.0'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertItemsEqual([pkg['name'] for pkg in response.data['results']],
                              ['test-{}'.format(i) for i in [2, 4, 7, 9, 10, 11, 12, 13, 14]])

    def test_filter_with_greater_version_obsoletes(self):
        response = self.client.get(reverse('rpms-list'), {'obsoletes': 'pkg>2.0'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertItemsEqual([pkg['name'] for pkg in response.data['results']],
                              ['test-{}'.format(i) for i in [2, 4, 7, 9, 10, 11, 12, 13, 14]])

    def test_filter_with_greater_version_recommends(self):
        response = self.client.get(reverse('rpms-list'), {'recommends': 'pkg>2.0'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertItemsEqual([pkg['name'] for pkg in response.data['results']],
                              ['test-{}'.format(i) for i in [2, 4, 7, 9, 10, 11, 12, 13, 14]])

    def test_filter_with_greater_version_provides(self):
        response = self.client.get(reverse('rpms-list'), {'provides': 'pkg>2.0'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertItemsEqual([pkg['name'] for pkg in response.data['results']],
                              ['test-{}'.format(i) for i in [2, 4, 7, 9, 10, 11, 12, 13, 14]])

    def test_filter_with_greater_version_conflicts(self):
        response = self.client.get(reverse('rpms-list'), {'conflicts': 'pkg>2.0'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertItemsEqual([pkg['name'] for pkg in response.data['results']],
                              ['test-{}'.format(i) for i in [2, 4, 7, 9, 10, 11, 12, 13, 14]])

    #
    # Lesser than constraint tests
    #

    def test_filter_with_lesser_version_requires(self):
        response = self.client.get(reverse('rpms-list'), {'requires': 'pkg<2.0'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertItemsEqual([pkg['name'] for pkg in response.data['results']],
                              ['test-{}'.format(i) for i in [0, 1, 2, 3, 4, 6, 8, 11, 13]])

    def test_filter_with_lesser_version_suggests(self):
        response = self.client.get(reverse('rpms-list'), {'suggests': 'pkg<2.0'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertItemsEqual([pkg['name'] for pkg in response.data['results']],
                              ['test-{}'.format(i) for i in [0, 1, 2, 3, 4, 6, 8, 11, 13]])

    def test_filter_with_lesser_version_obsoletes(self):
        response = self.client.get(reverse('rpms-list'), {'obsoletes': 'pkg<2.0'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertItemsEqual([pkg['name'] for pkg in response.data['results']],
                              ['test-{}'.format(i) for i in [0, 1, 2, 3, 4, 6, 8, 11, 13]])

    def test_filter_with_lesser_version_recommends(self):
        response = self.client.get(reverse('rpms-list'), {'recommends': 'pkg<2.0'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertItemsEqual([pkg['name'] for pkg in response.data['results']],
                              ['test-{}'.format(i) for i in [0, 1, 2, 3, 4, 6, 8, 11, 13]])

    def test_filter_with_lesser_version_provides(self):
        response = self.client.get(reverse('rpms-list'), {'provides': 'pkg<2.0'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertItemsEqual([pkg['name'] for pkg in response.data['results']],
                              ['test-{}'.format(i) for i in [0, 1, 2, 3, 4, 6, 8, 11, 13]])

    def test_filter_with_lesser_version_conflicts(self):
        response = self.client.get(reverse('rpms-list'), {'conflicts': 'pkg<2.0'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertItemsEqual([pkg['name'] for pkg in response.data['results']],
                              ['test-{}'.format(i) for i in [0, 1, 2, 3, 4, 6, 8, 11, 13]])

    #
    # Greater than or equal constraint tests
    #

    def test_filter_with_greater_or_equal_version_requires(self):
        response = self.client.get(reverse('rpms-list'), {'requires': 'pkg>=2.0'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertItemsEqual([pkg['name'] for pkg in response.data['results']],
                              ['test-{}'.format(i) for i in [2, 4, 5, 7, 8, 9, 10, 11, 12, 13, 14]])

    def test_filter_with_greater_or_equal_version_suggests(self):
        response = self.client.get(reverse('rpms-list'), {'suggests': 'pkg>=2.0'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertItemsEqual([pkg['name'] for pkg in response.data['results']],
                              ['test-{}'.format(i) for i in [2, 4, 5, 7, 8, 9, 10, 11, 12, 13, 14]])

    def test_filter_with_greater_or_equal_version_recommends(self):
        response = self.client.get(reverse('rpms-list'), {'recommends': 'pkg>=2.0'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertItemsEqual([pkg['name'] for pkg in response.data['results']],
                              ['test-{}'.format(i) for i in [2, 4, 5, 7, 8, 9, 10, 11, 12, 13, 14]])

    def test_filter_with_greater_or_equal_version_obsoletes(self):
        response = self.client.get(reverse('rpms-list'), {'obsoletes': 'pkg>=2.0'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertItemsEqual([pkg['name'] for pkg in response.data['results']],
                              ['test-{}'.format(i) for i in [2, 4, 5, 7, 8, 9, 10, 11, 12, 13, 14]])

    def test_filter_with_greater_or_equal_version_provides(self):
        response = self.client.get(reverse('rpms-list'), {'provides': 'pkg>=2.0'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertItemsEqual([pkg['name'] for pkg in response.data['results']],
                              ['test-{}'.format(i) for i in [2, 4, 5, 7, 8, 9, 10, 11, 12, 13, 14]])

    def test_filter_with_greater_or_equal_version_conflicts(self):
        response = self.client.get(reverse('rpms-list'), {'conflicts': 'pkg>=2.0'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertItemsEqual([pkg['name'] for pkg in response.data['results']],
                              ['test-{}'.format(i) for i in [2, 4, 5, 7, 8, 9, 10, 11, 12, 13, 14]])

    #
    # Lesser than or equal constraint tests
    #

    def test_filter_with_lesser_or_equal_version_requires(self):
        response = self.client.get(reverse('rpms-list'), {'requires': 'pkg<=2.0'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertItemsEqual([pkg['name'] for pkg in response.data['results']],
                              ['test-{}'.format(i) for i in [0, 1, 2, 3, 4, 5, 6, 8, 9, 11, 13]])

    def test_filter_with_lesser_or_equal_version_suggests(self):
        response = self.client.get(reverse('rpms-list'), {'suggests': 'pkg<=2.0'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertItemsEqual([pkg['name'] for pkg in response.data['results']],
                              ['test-{}'.format(i) for i in [0, 1, 2, 3, 4, 5, 6, 8, 9, 11, 13]])

    def test_filter_with_lesser_or_equal_version_recommends(self):
        response = self.client.get(reverse('rpms-list'), {'recommends': 'pkg<=2.0'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertItemsEqual([pkg['name'] for pkg in response.data['results']],
                              ['test-{}'.format(i) for i in [0, 1, 2, 3, 4, 5, 6, 8, 9, 11, 13]])

    def test_filter_with_lesser_or_equal_version_provides(self):
        response = self.client.get(reverse('rpms-list'), {'provides': 'pkg<=2.0'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertItemsEqual([pkg['name'] for pkg in response.data['results']],
                              ['test-{}'.format(i) for i in [0, 1, 2, 3, 4, 5, 6, 8, 9, 11, 13]])

    def test_filter_with_lesser_or_equal_version_conflicts(self):
        response = self.client.get(reverse('rpms-list'), {'conflicts': 'pkg<=2.0'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertItemsEqual([pkg['name'] for pkg in response.data['results']],
                              ['test-{}'.format(i) for i in [0, 1, 2, 3, 4, 5, 6, 8, 9, 11, 13]])

    def test_filter_with_lesser_or_equal_version_obsoletes(self):
        response = self.client.get(reverse('rpms-list'), {'obsoletes': 'pkg<=2.0'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertItemsEqual([pkg['name'] for pkg in response.data['results']],
                              ['test-{}'.format(i) for i in [0, 1, 2, 3, 4, 5, 6, 8, 9, 11, 13]])


class RPMDepsFilterWithReleaseTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.rpm = models.RPM.objects.create(name='test-pkg', epoch=0, version='1.0',
                                            release='1', arch='x86_64', srpm_name='test-pkg',
                                            srpm_nevra='test-pkg-1.0.1.x86_64',
                                            filename='dummy')
        cls.rpm.dependency_set.create(name='pkg', version='3.0-1.fc22',
                                      type=models.Dependency.REQUIRES, comparison='=')

    def test_filter_with_same_release_equal(self):
        response = self.client.get(reverse('rpms-list'), {'requires': 'pkg=3.0-1.fc22'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 1)

    def test_filter_with_same_release_lesser(self):
        response = self.client.get(reverse('rpms-list'), {'requires': 'pkg<3.0-1.fc22'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 0)

    def test_filter_with_same_release_greater(self):
        response = self.client.get(reverse('rpms-list'), {'requires': 'pkg>3.0-1.fc22'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 0)

    def test_filter_with_same_release_lesser_equal(self):
        response = self.client.get(reverse('rpms-list'), {'requires': 'pkg<=3.0-1.fc22'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 1)

    def test_filter_with_same_release_greater_equal(self):
        response = self.client.get(reverse('rpms-list'), {'requires': 'pkg>=3.0-1.fc22'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 1)

    def test_filter_with_different_release_equal(self):
        response = self.client.get(reverse('rpms-list'), {'requires': 'pkg=3.0-2.fc22'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 0)

    def test_filter_with_different_release_lesser(self):
        response = self.client.get(reverse('rpms-list'), {'requires': 'pkg<3.0-2.fc22'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 1)

    def test_filter_with_different_release_greater(self):
        response = self.client.get(reverse('rpms-list'), {'requires': 'pkg>3.0-2.fc22'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 0)

    def test_filter_with_different_release_lesser_equal(self):
        response = self.client.get(reverse('rpms-list'), {'requires': 'pkg<=3.0-2.fc22'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 1)

    def test_filter_with_different_release_greater_equal(self):
        response = self.client.get(reverse('rpms-list'), {'requires': 'pkg>=3.0-2.fc22'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 0)


class RPMDepsFilterWithEpochTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.rpm = models.RPM.objects.create(name='test-pkg', epoch=0, version='1.0',
                                            release='1', arch='x86_64', srpm_name='test-pkg',
                                            srpm_nevra='test-pkg-1.0.1.x86_64',
                                            filename='dummy')
        cls.rpm.dependency_set.create(name='pkg', version='3.0',
                                      type=models.Dependency.REQUIRES, comparison='=')

    def test_filter_with_same_epoch_equal(self):
        response = self.client.get(reverse('rpms-list'), {'requires': 'pkg=0:3.0'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 1)

    def test_filter_with_same_epoch_lesser(self):
        response = self.client.get(reverse('rpms-list'), {'requires': 'pkg<0:4.0'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 1)

    def test_filter_with_same_epoch_greater(self):
        response = self.client.get(reverse('rpms-list'), {'requires': 'pkg>0:2.0'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 1)

    def test_filter_with_same_epoch_lesser_equal(self):
        response = self.client.get(reverse('rpms-list'), {'requires': 'pkg<=0:3.0'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 1)

    def test_filter_with_same_epoch_greater_equal(self):
        response = self.client.get(reverse('rpms-list'), {'requires': 'pkg>=0:3.0'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 1)

    def test_filter_with_different_epoch_equal(self):
        response = self.client.get(reverse('rpms-list'), {'requires': 'pkg=1:3.0'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 0)

    def test_filter_with_different_epoch_lesser(self):
        response = self.client.get(reverse('rpms-list'), {'requires': 'pkg<1:3.0'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 1)

    def test_filter_with_different_epoch_greater(self):
        response = self.client.get(reverse('rpms-list'), {'requires': 'pkg>1:2.0'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 0)

    def test_filter_with_different_epoch_lesser_equal(self):
        response = self.client.get(reverse('rpms-list'), {'requires': 'pkg<=1:3.0'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 1)

    def test_filter_with_different_epoch_greater_equal(self):
        response = self.client.get(reverse('rpms-list'), {'requires': 'pkg>=1:3.0'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 0)


class RPMDepsFilterRangeAPITestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        rpm = models.RPM.objects.create(name='test-pkg', epoch=0, version='1.0',
                                        release='1', arch='x86_64', srpm_name='test-pkg',
                                        srpm_nevra='test-pkg-1.0.1.x86_64',
                                        filename='dummy')
        for type in [t[0] for t in models.Dependency.DEPENDENCY_TYPE_CHOICES]:
            rpm.dependency_set.create(name='pkg', version='1.0',
                                      type=type, comparison='>=')
            rpm.dependency_set.create(name='pkg', version='3.0',
                                      type=type, comparison='<')

    def test_filter_with_range_match_requires(self):
        response = self.client.get(reverse('rpms-list'), {'requires': 'pkg=2.0'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    def test_filter_with_range_no_match_requires(self):
        response = self.client.get(reverse('rpms-list'), {'requires': 'pkg=4.0'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 0)

    def test_filter_with_range_match_obsoletes(self):
        response = self.client.get(reverse('rpms-list'), {'obsoletes': 'pkg=2.0'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    def test_filter_with_range_no_match_obsoletes(self):
        response = self.client.get(reverse('rpms-list'), {'obsoletes': 'pkg=4.0'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 0)

    def test_filter_with_range_match_provides(self):
        response = self.client.get(reverse('rpms-list'), {'provides': 'pkg=2.0'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    def test_filter_with_range_no_match_provides(self):
        response = self.client.get(reverse('rpms-list'), {'provides': 'pkg=4.0'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 0)

    def test_filter_with_range_match_suggests(self):
        response = self.client.get(reverse('rpms-list'), {'suggests': 'pkg=2.0'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    def test_filter_with_range_no_match_suggests(self):
        response = self.client.get(reverse('rpms-list'), {'suggests': 'pkg=4.0'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 0)

    def test_filter_with_range_match_recommends(self):
        response = self.client.get(reverse('rpms-list'), {'recommends': 'pkg=2.0'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    def test_filter_with_range_no_match_recommends(self):
        response = self.client.get(reverse('rpms-list'), {'recommends': 'pkg=4.0'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 0)

    def test_filter_with_range_match_conflicts(self):
        response = self.client.get(reverse('rpms-list'), {'conflicts': 'pkg=2.0'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    def test_filter_with_range_no_match_conflicts(self):
        response = self.client.get(reverse('rpms-list'), {'conflicts': 'pkg=4.0'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 0)


class RPMDepsAPITestCase(TestCaseWithChangeSetMixin, APITestCase):
    fixtures = [
        'pdc/apps/common/fixtures/test/sigkey.json',
        'pdc/apps/release/fixtures/tests/release.json',
        'pdc/apps/package/fixtures/test/rpm.json',
        'pdc/apps/compose/fixtures/tests/compose.json',
        'pdc/apps/compose/fixtures/tests/compose_composerpm.json',
        'pdc/apps/compose/fixtures/tests/variant_arch.json',
        'pdc/apps/compose/fixtures/tests/variant.json'
    ]

    def setUp(self):
        self.maxDiff = None

    def _create_deps(self):
        models.Dependency.objects.create(type=models.Dependency.SUGGESTS,
                                         name='suggested', rpm_id=1)
        models.Dependency.objects.create(type=models.Dependency.CONFLICTS,
                                         name='conflicting', rpm_id=1)

    def test_create_rpm_with_deps(self):
        data = {'name': 'fake_bash', 'version': '1.2.3', 'epoch': 0,
                'release': '4.b1', 'arch': 'x86_64', 'srpm_name': 'bash',
                'filename': 'bash-1.2.3-4.b1.x86_64.rpm',
                'linked_releases': [], 'srpm_nevra': 'fake_bash-0:1.2.3-4.b1.src',
                'dependencies': {'requires': ['required-package'],
                                 'obsoletes': ['obsolete-package'],
                                 'suggests': ['suggested-package >= 1.0.0'],
                                 'recommends': ['recommended = 0.1.0'],
                                 'provides': ['/bin/bash', '/usr/bin/whatever'],
                                 'conflicts': ['nothing']}}
        response = self.client.post(reverse('rpms-list'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response.data.pop('id')
        data.update({'linked_composes': []})
        self.assertDictEqual(dict(response.data), data)
        self.assertEqual(7, models.Dependency.objects.count())
        with_version = models.Dependency.objects.get(name='recommended')
        self.assertEqual(with_version.comparison, '=')
        self.assertEqual(with_version.version, '0.1.0')
        self.assertNumChanges([1])

    def test_create_rpm_with_duplicate_deps(self):
        data = {'name': 'fake_bash', 'version': '1.2.3', 'epoch': 0,
                'release': '4.b1', 'arch': 'x86_64', 'srpm_name': 'bash',
                'filename': 'bash-1.2.3-4.b1.x86_64.rpm',
                'linked_releases': [], 'srpm_nevra': 'fake_bash-0:1.2.3-4.b1.src',
                'dependencies': {'requires': ['required-package', 'required-package'],
                                 'obsoletes': ['obsolete-package'],
                                 'suggests': ['suggested-package >= 1.0.0', 'suggested-package >= 1.0.0'],
                                 'recommends': ['recommended = 0.1.0'],
                                 'provides': ['/bin/bash', '/usr/bin/whatever'],
                                 'conflicts': ['nothing']}}
        response = self.client.post(reverse('rpms-list'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertNumChanges([1])

    def test_put_to_rpm_with_none(self):
        data = {
            'name': 'bash',
            'epoch': 0,
            'version': '1.2.3',
            'release': '4.b1',
            'arch': 'x86_64',
            'srpm_name': 'bash',
            'srpm_nevra': 'bash-0:1.2.3-4.b1.src',
            'filename': 'bash-1.2.3-4.b1.x86_64.rpm',
            'dependencies': {
                'requires': ['required-package']
            }
        }
        response = self.client.put(reverse('rpms-detail', args=[1]), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(1, models.Dependency.objects.count())
        dep = models.Dependency.objects.first()
        self.assertIsNone(dep.comparison)
        self.assertIsNone(dep.version)
        self.assertEqual(dep.rpm.pk, 1)
        self.assertNumChanges([1])

    def test_put_to_overwrite_existing(self):
        models.Dependency.objects.create(type=models.Dependency.SUGGESTS,
                                         name='suggested', rpm_id=1)
        models.Dependency.objects.create(type=models.Dependency.CONFLICTS,
                                         name='conflicting', rpm_id=1)
        data = {'name': 'bash',
                'epoch': 0,
                'version': '1.2.3',
                'release': '4.b1',
                'arch': 'x86_64',
                'srpm_name': 'bash',
                'srpm_nevra': 'bash-0:1.2.3-4.b1.src',
                'filename': 'bash-1.2.3-4.b1.x86_64.rpm',
                'dependencies': {'requires': ['required-package']}}
        response = self.client.put(reverse('rpms-detail', args=[1]), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(1, models.Dependency.objects.count())
        dep = models.Dependency.objects.first()
        self.assertIsNone(dep.comparison)
        self.assertIsNone(dep.version)
        self.assertEqual(dep.rpm.pk, 1)
        self.assertEqual(dep.name, 'required-package')
        self.assertEqual(dep.type, models.Dependency.REQUIRES)
        self.assertNumChanges([1])

    def test_patch_to_rpm_with_none(self):
        data = {'dependencies': {'requires': ['required-package']}}
        response = self.client.patch(reverse('rpms-detail', args=[1]), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(1, models.Dependency.objects.count())
        dep = models.Dependency.objects.first()
        self.assertIsNone(dep.comparison)
        self.assertIsNone(dep.version)
        self.assertEqual(dep.rpm.pk, 1)
        self.assertEqual(dep.name, 'required-package')
        self.assertEqual(dep.type, models.Dependency.REQUIRES)
        self.assertNumChanges([1])

    def test_patch_to_overwrite_existing(self):
        self._create_deps()
        data = {'dependencies': {'requires': ['required-package']}}
        response = self.client.patch(reverse('rpms-detail', args=[1]), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(1, models.Dependency.objects.count())
        dep = models.Dependency.objects.first()
        self.assertIsNone(dep.comparison)
        self.assertIsNone(dep.version)
        self.assertEqual(dep.rpm.pk, 1)
        self.assertEqual(dep.name, 'required-package')
        self.assertEqual(dep.type, models.Dependency.REQUIRES)
        self.assertNumChanges([1])

    def test_put_to_remove(self):
        self._create_deps()
        data = {'name': 'bash',
                'epoch': 0,
                'version': '1.2.3',
                'release': '4.b1',
                'arch': 'x86_64',
                'srpm_name': 'bash',
                'srpm_nevra': 'bash-0:1.2.3-4.b1.src',
                'filename': 'bash-1.2.3-4.b1.x86_64.rpm',
                'dependencies': {}}
        response = self.client.patch(reverse('rpms-detail', args=[1]), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNumChanges([1])
        self.assertEqual(0, models.Dependency.objects.count())

    def test_patch_to_remove(self):
        self._create_deps()
        data = {'dependencies': {}}
        response = self.client.patch(reverse('rpms-detail', args=[1]), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNumChanges([1])
        self.assertEqual(0, models.Dependency.objects.count())

    def test_bad_dependency_format(self):
        data = {'dependencies': {'recommends': ['foo bar']}}
        response = self.client.patch(reverse('rpms-detail', args=[1]), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNumChanges([])

    def test_bad_dependency_type(self):
        data = {'dependencies': {'wants': ['icecream']}}
        response = self.client.patch(reverse('rpms-detail', args=[1]), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNumChanges([])

    def test_deps_are_not_list(self):
        data = {'dependencies': {'suggests': 'pony'}}
        response = self.client.patch(reverse('rpms-detail', args=[1]), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNumChanges([])

    def test_deps_with_too_many_lists(self):
        data = {'dependencies': {'suggests': [['pony']]}}
        response = self.client.patch(reverse('rpms-detail', args=[1]), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNumChanges([])

    def test_patch_without_deps_does_not_delete_existing(self):
        self._create_deps()
        data = {'name': 'new_name'}
        response = self.client.patch(reverse('rpms-detail', args=[1]), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNumChanges([1])
        self.assertEqual(2, models.Dependency.objects.count())

    def test_put_without_deps_deletes_existing(self):
        self._create_deps()
        data = {'name': 'new-name',
                'epoch': 0,
                'version': '1.2.3',
                'release': '4.b1',
                'arch': 'x86_64',
                'srpm_name': 'bash',
                'srpm_nevra': 'bash-0:1.2.3-4.b1.src',
                'filename': 'bash-1.2.3-4.b1.x86_64.rpm'}
        response = self.client.put(reverse('rpms-detail', args=[1]), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNumChanges([1])
        self.assertEqual(0, models.Dependency.objects.count())

    def test_has_no_deps_filter(self):
        self._create_deps()
        response = self.client.get(reverse('rpms-list'), {'has_no_deps': 'true'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 2)
        response = self.client.get(reverse('rpms-list'), {'has_no_deps': 'false'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 1)


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

    def setUp(self):
        self.empty_deps = {'conflicts': [], 'obsoletes': [], 'provides': [],
                           'recommends': [], 'requires': [], 'suggests': []}

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

    def test_query_with_bad_epoch(self):
        url = reverse('rpms-list')
        response = self.client.get(url, {'epoch': 'foo'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('epoch', response.data['detail'][0])

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
        expect_data = {"id": 1, "name": "bash", "version": "1.2.3", "epoch": 0, "release": "4.b1",
                       "arch": "x86_64",
                       "srpm_name": "bash", "srpm_nevra": "bash-0:1.2.3-4.b1.src",
                       "filename": "bash-1.2.3-4.b1.x86_64.rpm", "linked_releases": [],
                       "linked_composes": ["compose-1"], "dependencies": self.empty_deps}
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
                                  "linked_releases": ['release-1.0'], "srpm_nevra": "fake_bash-0:1.2.3-4.b1.src",
                                  "dependencies": self.empty_deps}
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

    def test_partial_update_does_not_break_filename(self):
        url = reverse('rpms-detail', args=[1])
        data = {'linked_releases': ['release-1.0']}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.data.get('filename'), 'bash-1.2.3-4.b1.x86_64.rpm')

    def test_full_update_uses_default_filename(self):
        url = reverse('rpms-detail', args=[1])
        data = {'name': 'fake_bash', 'version': '1.2.3', 'epoch': 0, 'release': '4.b1', 'arch': 'x86_64',
                'srpm_name': 'bash', 'linked_releases': ['release-1.0'],
                'srpm_nevra': 'fake_bash-0:1.2.3-4.b1.src'}
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('filename'), 'fake_bash-1.2.3-4.b1.x86_64.rpm')
        self.assertNumChanges([1])

    def test_full_update_with_missing_fields_does_not_crash_on_default_filename(self):
        url = reverse('rpms-detail', args=[1])
        data = {'epoch': 0,
                'srpm_name': 'bash', 'linked_releases': ['release-1.0'],
                'srpm_nevra': 'fake_bash-0:1.2.3-4.b1.src'}
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNumChanges([])

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
        data.update({'id': 1, 'linked_composes': [u'compose-1'], 'dependencies': self.empty_deps})
        self.assertDictEqual(dict(response.data), data)
        self.assertNumChanges([1])

    def test_update_rpm_with_linked_compose_should_read_only(self):
        url = reverse('rpms-detail', args=[3])
        data = {'linked_composes': [u'compose-1']}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNumChanges([])

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

    def test_negative_bootable(self):
        response = self.client.get(reverse('image-list'), {'bootable': 'false'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 2)

    def test_active_bootable(self):
        response = self.client.get(reverse('image-list'), {'bootable': 'true'})
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

    def test_query_disc_number_with_wrong_value(self):
        key = 'disc_number'
        value = 'wrongvalue'
        response = self.client.get(reverse('image-list'), {key: value})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {"detail": [u'Value [%s] of %s is not an integer' % (value, key)]})

    def test_query_disc_count_with_wrong_value(self):
        key = 'disc_count'
        value = 'wrongvalue'
        response = self.client.get(reverse('image-list'), {key: value})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {"detail": [u'Value [%s] of %s is not an integer' % (value, key)]})

    def test_query_mtime_with_wrong_value(self):
        key = 'mtime'
        value = 'wrongvalue'
        response = self.client.get(reverse('image-list'), {key: value})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {"detail": [u'Value [%s] of %s is not an integer' % (value, key)]})

    def test_query_size_with_wrong_value(self):
        key = 'size'
        value = 'wrongvalue'
        response = self.client.get(reverse('image-list'), {key: value})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {"detail": [u'Value [%s] of %s is not an integer' % (value, key)]})


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

    def test_create_same_image_id_with_different_format(self):
        url = reverse('buildimage-list')
        data = {'image_id': 'new_build',
                'image_format': 'docker',
                'md5': "0123456789abcdef0123456789abcdef",
                'rpms': [{'name': 'new_rpm', 'epoch': 0, 'version': '1.0.0',
                          'release': '1', 'arch': 'src', 'srpm_name': 'new_srpm'}]
                }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        url = reverse('buildimage-list')
        data = {'image_id': 'new_build',
                'image_format': 'iso',
                'md5': "0123456789abcdef0123456789abcabc",
                'rpms': [{'name': 'new_rpm', 'epoch': 0, 'version': '1.0.0',
                          'release': '1', 'arch': 'src', 'srpm_name': 'new_srpm'}]
                }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class BuildImageRTTTestsRESTTestCase(TestCaseWithChangeSetMixin, APITestCase):
    fixtures = [
        'pdc/apps/package/fixtures/test/rpm.json',
        'pdc/apps/package/fixtures/test/archive.json',
        'pdc/apps/package/fixtures/test/release.json',
        'pdc/apps/package/fixtures/test/build_image.json',
    ]

    def test_build_image_default_test_result_should_be_untested(self):
        url = reverse('buildimage-list')
        response = self.client.get(url, format='json')
        total_count = response.data['count']

        url = reverse('buildimagertttests-list')
        response = self.client.get(url + '?test_result=untested', format='json')
        untested_count = response.data['count']
        self.assertEqual(total_count, untested_count)

        url = reverse('buildimage-list')
        data = {'image_id': 'new_build',
                'image_format': 'docker',
                'md5': "0123456789abcdef0123456789abcdef",
                'rpms': [{'name': 'new_rpm', 'epoch': 0, 'version': '1.0.0',
                          'release': '1', 'arch': 'src', 'srpm_name': 'new_srpm'}]
                }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        total_count += 1
        url = reverse('buildimagertttests-list')
        response = self.client.get(url + '?test_result=untested', format='json')
        untested_count = response.data['count']
        self.assertEqual(total_count, untested_count)

    def test_build_image_test_result_should_not_be_created(self):
        url = reverse('buildimagertttests-list')
        data = {'build_nvr': 'fake_nvr', 'format': 'iso', 'test_result': 'untested'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.data, {u'detail': u'Method "POST" not allowed.'})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_build_image_test_result_should_not_be_deleted(self):
        url = reverse('buildimagertttests-detail', args=[1])
        response = self.client.delete(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_filter_build_image_test_results_with_test_result(self):
        url = reverse('buildimagertttests-list')
        response = self.client.get(url + '?test_result=untested', format='json')
        untested_count = response.data['count']
        self.assertGreater(untested_count, 0)

        url = reverse('buildimagertttests-list')
        response = self.client.get(url + '?test_result=passed', format='json')
        untested_count = response.data['count']
        self.assertEqual(0, untested_count)

        url = reverse('buildimagertttests-list')
        response = self.client.get(url + '?test_result=failed', format='json')
        untested_count = response.data['count']
        self.assertEqual(0, untested_count)

    def test_filter_build_image_test_results_with_test_nvr_and_test_result(self):
        url = reverse('buildimagertttests-list')
        response = self.client.get(url + '?build_nvr=my-server-docker-1.0-27', format='json')
        count = response.data['count']
        self.assertEqual(count, 1)

        url = reverse('buildimagertttests-list')
        response = self.client.get(url + '?build_nvr=fake_nvr', format='json')
        count = response.data['count']
        self.assertEqual(count, 0)

        url = reverse('buildimage-list')
        data = {'image_id': 'my-server-docker-1.0-27',
                'image_format': 'iso',
                'md5': "0123456789abcdef0123456789abcdef",
                'rpms': [{'name': 'new_rpm', 'epoch': 0, 'version': '1.0.0',
                          'release': '1', 'arch': 'src', 'srpm_name': 'new_srpm'}]
                }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        url = reverse('buildimagertttests-list')
        response = self.client.get(url + '?build_nvr=my-server-docker-1.0-27', format='json')
        count = response.data['count']
        self.assertEqual(count, 2)

        url = reverse('buildimagertttests-list')
        response = self.client.get(url + '?build_nvr=my-server-docker-1.0-27&test_result=untested', format='json')
        count = response.data['count']
        self.assertEqual(count, 2)

        url = reverse('buildimagertttests-list')
        response = self.client.get(url + '?build_nvr=my-server-docker-1.0-27&test_result=passed', format='json')
        count = response.data['count']
        self.assertEqual(count, 0)

    def test_patch_build_image_test_results(self):
        url = reverse('buildimagertttests-list')
        response = self.client.get(url + '?test_result=untested', format='json')
        ori_untested_count = response.data['count']

        url = reverse('buildimagertttests-detail', args=[1])
        data = {'test_result': 'passed'}
        response = self.client.patch(url, data, format='json')

        url = reverse('buildimagertttests-list')
        response = self.client.get(url + '?test_result=passed', format='json')
        untested_count = response.data['count']
        self.assertEqual(1, untested_count)

        url = reverse('buildimagertttests-list')
        response = self.client.get(url + '?test_result=untested', format='json')
        new_untested_count = response.data['count']
        self.assertEqual(new_untested_count, ori_untested_count - 1)

    def test_update_patch_build_image_test_results_not_allowed_fields(self):
        data = {'build_nvr': 'fake_nvr', 'format': 'iso', 'test_result': 'untested'}
        url = reverse('buildimagertttests-detail', args=[1])
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        data = {'format': 'iso', 'test_result': 'untested'}
        url = reverse('buildimagertttests-detail', args=[1])
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        data = {'build_nvr': 'fake_nvr', 'test_result': 'untested'}
        url = reverse('buildimagertttests-detail', args=[1])
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        data = {'format': 'iso'}
        url = reverse('buildimagertttests-detail', args=[1])
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        data = {'build_nvr': 'fake_nvr'}
        url = reverse('buildimagertttests-detail', args=[1])
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
