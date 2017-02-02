# -*- coding: utf-8 -*-
#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
from rest_framework.test import APITestCase
from django.core.urlresolvers import reverse
from rest_framework import status

from . import models
from . import serializers
from pdc.apps.common.test_utils import TestCaseWithChangeSetMixin
from pdc.apps.release import models as release_models


class RepositorySerializerTestCase(APITestCase):
    fixtures = [
        "pdc/apps/release/fixtures/tests/release.json",
        "pdc/apps/release/fixtures/tests/variant.json",
        "pdc/apps/release/fixtures/tests/variant_arch.json",
        "pdc/apps/repository/fixtures/tests/repo.json",
    ]

    def setUp(self):
        self.fixture_data = {'content_format': 'rpm', 'content_category': 'binary',
                             'release_id': 'release-1.0', 'name': 'test_repo', 'service': 'rhn',
                             'arch': 'x86_64', 'shadow': False, 'variant_uid': 'Server',
                             'repo_family': 'dist', 'product_id': 22, 'id': 1}
        self.data = {'content_format': 'rpm', 'content_category': 'binary',
                     'release_id': 'release-1.0', 'name': 'test_repo_2', 'service': 'rhn',
                     'arch': 'x86_64', 'variant_uid': 'Server', 'repo_family': 'dist',
                     'shadow': True}

    def test_serialize(self):
        repo = models.Repo.objects.get(pk=1)
        serializer = serializers.RepoSerializer(repo)
        self.assertEqual(serializer.data, self.fixture_data)

    def test_deserialize_valid(self):
        serializer = serializers.RepoSerializer(data=self.data)
        self.assertTrue(serializer.is_valid())
        obj = serializer.save()
        self.assertEqual(obj.name, "test_repo_2")
        self.assertEqual(obj.variant_arch.variant.variant_uid, "Server")
        self.assertEqual(obj.service.name, "rhn")
        self.assertTrue(obj.shadow)

    def test_deserialize_without_optional_field(self):
        del self.data['shadow']
        serializer = serializers.RepoSerializer(data=self.data)
        self.assertTrue(serializer.is_valid())
        obj = serializer.save()
        self.assertFalse(obj.shadow)

    def test_deserialize_invalid_shadow(self):
        self.data['shadow'] = 'very shadow'
        serializer = serializers.RepoSerializer(data=self.data)
        self.assertFalse(serializer.is_valid())
        self.assertIn(u'"very shadow" is not a valid boolean', serializer.errors['shadow'][0])

    def test_deserialize_missing_value(self):
        for field in self.data.keys():
            if field == 'shadow':
                continue
            old_val = self.data.pop(field)
            serializer = serializers.RepoSerializer(data=self.data)
            self.assertFalse(serializer.is_valid())
            self.assertEqual(serializer.errors, {field: ["This field is required."]})
            self.data[field] = old_val

    def test_deserialize_duplicit(self):
        del self.fixture_data['id']
        serializer = serializers.RepoSerializer(data=self.fixture_data)
        self.assertFalse(serializer.is_valid())
        self.assertEqual(serializer.errors,
                         {'detail': [
                             # Following is a single string
                             'Repo with this Variant arch, Service, Repo family, Content format, '
                             'Content category, Name and Shadow already exists.']})

    def test_deserialize_with_bad_directly_related_field_value(self):
        for key in ('content_category', 'content_format', 'repo_family', 'service'):
            old_val = self.data.pop(key)
            self.data[key] = 'foo'
            serializer = serializers.RepoSerializer(data=self.data)
            self.assertFalse(serializer.is_valid())
            self.assertIn(key, serializer.errors)
            self.assertEqual(len(serializer.errors[key]), 1)
            self.assertRegexpMatches(serializer.errors[key][0],
                                     r"^'[^']*' is not allowed value. Use one of .*$")
            self.data[key] = old_val

    def test_deserialize_with_bad_indirectly_related_field_value(self):
        for key in ('arch', 'variant_uid', 'release_id'):
            old_val = self.data.pop(key)
            self.data[key] = 'foo'
            serializer = serializers.RepoSerializer(data=self.data)
            self.assertFalse(serializer.is_valid())
            self.assertIn('detail', serializer.errors)
            self.assertEqual(len(serializer.errors['detail']), 1)
            self.assertRegexpMatches(serializer.errors['detail'][0],
                                     r'^No VariantArch .*')
            self.data[key] = old_val


class RepositoryRESTTestCase(TestCaseWithChangeSetMixin, APITestCase):
    fixtures = [
        "pdc/apps/release/fixtures/tests/release.json",
        "pdc/apps/release/fixtures/tests/variant.json",
        "pdc/apps/release/fixtures/tests/variant_arch.json",
        "pdc/apps/repository/fixtures/tests/repo.json",
    ]

    def setUp(self):
        self.data = {"release_id": "release-1.0", "variant_uid": "Server", "arch": "x86_64",
                     "name": "repo-x86_64-server-7", "service": "rhn", "content_format": "rpm",
                     "content_category": "binary", "repo_family": "dist", "product_id": 11}
        self.existing = {
            'id': 1,
            'release_id': 'release-1.0', 'variant_uid': 'Server', 'arch': 'x86_64',
            'service': 'rhn', 'repo_family': 'dist', 'content_format': 'rpm',
            'content_category': 'binary', 'name': 'test_repo', 'shadow': False, 'product_id': 22
        }

    def test_retrieve(self):
        response = self.client.get(reverse('contentdeliveryrepos-detail', args=[1]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertDictEqual(dict(response.data), self.existing)

    def test_update(self):
        variant = release_models.Variant.objects.create(
            release=release_models.Release.objects.get(release_id='release-1.0'),
            variant_type=release_models.VariantType.objects.get(name='variant'),
            variant_uid='Client', variant_name='Client', variant_id='Client'
        )
        release_models.VariantArch.objects.create(
            variant=variant,
            arch_id=47  # x86_64
        )
        data = {
            'release_id': 'release-1.0', 'variant_uid': 'Client', 'arch': 'x86_64',
            'service': 'rhn', 'repo_family': 'dist', 'content_format': 'rpm',
            'content_category': 'debug', 'name': 'test_repo-debug', 'shadow': False, 'product_id': 33
        }
        response = self.client.put(reverse('contentdeliveryrepos-detail', args=[1]),
                                   data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNumChanges([1])

    def test_update_without_product_id(self):
        """The repo has product_id, update tries to change name with product_id unspecified in request."""
        self.existing.pop('product_id')
        self.existing['name'] = 'new_name'
        id = self.existing.pop('id')
        response = self.client.put(reverse('contentdeliveryrepos-detail', args=[1]), self.existing, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.existing['product_id'] = None
        self.existing['id'] = id
        self.assertDictEqual(dict(response.data), self.existing)
        self.assertNumChanges([1])

    def test_update_partial(self):
        response = self.client.patch(reverse('contentdeliveryrepos-detail', args=[1]),
                                     {'shadow': True},
                                     format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.existing['shadow'] = True
        self.assertDictEqual(dict(response.data), self.existing)
        self.assertNumChanges([1])

    def test_update_partial_correct_variant(self):
        variant = release_models.Variant.objects.create(
            release=release_models.Release.objects.get(release_id='release-1.0'),
            variant_type=release_models.VariantType.objects.get(name='variant'),
            variant_uid='Client', variant_name='Client', variant_id='Client'
        )
        release_models.VariantArch.objects.create(
            variant=variant,
            arch_id=47  # x86_64
        )
        response = self.client.patch(reverse('contentdeliveryrepos-detail', args=[1]),
                                     {'variant_uid': 'Client'},
                                     format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.existing['variant_uid'] = 'Client'
        self.assertDictEqual(dict(response.data), self.existing)
        self.assertNumChanges([1])

    def test_update_partial_bad_variant(self):
        response = self.client.patch(reverse('contentdeliveryrepos-detail', args=[1]),
                                     {'variant_uid': 'foo', 'arch': 'bar'},
                                     format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNumChanges([])

    def test_update_missing_optional_fields_are_erased(self):
        variant = release_models.Variant.objects.create(
            release=release_models.Release.objects.get(release_id='release-1.0'),
            variant_type=release_models.VariantType.objects.get(name='variant'),
            variant_uid='Client', variant_name='Client', variant_id='Client'
        )
        release_models.VariantArch.objects.create(
            variant=variant,
            arch_id=47  # x86_64
        )
        data = {
            'release_id': 'release-1.0', 'variant_uid': 'Client', 'arch': 'x86_64',
            'service': 'rhn', 'repo_family': 'dist', 'content_format': 'rpm',
            'content_category': 'debug', 'name': 'test_repo-debug', 'shadow': True
        }
        response = self.client.put(reverse('contentdeliveryrepos-detail', args=[1]),
                                   data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['shadow'], True)
        self.assertEqual(response.data['product_id'], None)

        data = {
            'release_id': 'release-1.0', 'variant_uid': 'Client', 'arch': 'x86_64',
            'service': 'rhn', 'repo_family': 'dist', 'content_format': 'rpm',
            'content_category': 'debug', 'name': 'test_repo-debug', 'product_id': 33
        }
        response = self.client.put(reverse('contentdeliveryrepos-detail', args=[1]),
                                   data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['product_id'], 33)
        self.assertEqual(response.data['shadow'], False)

    def test_create_duplicit(self):
        response = self.client.post(reverse('contentdeliveryrepos-list'), self.existing)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create(self):
        response = self.client.post(reverse('contentdeliveryrepos-list'), self.data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.data.update({"name": "repo-x86_64-server-7-debug", "content_category": "debug"})
        response = self.client.post(reverse('contentdeliveryrepos-list'), self.data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(3, models.Repo.objects.count())
        self.assertNumChanges([1, 1])

    def test_create_extra_fields(self):
        self.data['foo'] = 'bar'
        response = self.client.post(reverse('contentdeliveryrepos-list'), self.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data.get('detail'), 'Unknown fields: "foo".')
        self.assertNumChanges([])

    def test_query_existing(self):
        expected_results = {}
        real_results = {}

        for key, value in self.existing.iteritems():
            if key == 'id':
                continue
            response = self.client.get(reverse('contentdeliveryrepos-list'), {key: value})
            self.assertEqual(response.status_code, status.HTTP_200_OK,
                             msg='Query on %s failed' % key)
            expected_results[key] = [self.existing]
            real_results[key] = [dict(x) for x in response.data['results']]

        self.assertDictEqual(real_results, expected_results)

    def test_query_invalid_filter(self):
        response = self.client.get(reverse('contentdeliveryrepos-list'), {'variant_arch': 'whatever'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_query_shadow_invalid_filter(self):
        response = self.client.get(reverse('contentdeliveryrepos-list'), {'shadow': 'abcde'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_query_non_existing(self):
        response = self.client.get(reverse('contentdeliveryrepos-list'), {"release_id": "release-1.1"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['results'], [])

    def test_delete(self):
        response = self.client.delete(reverse('contentdeliveryrepos-detail', args=[self.existing['id']]))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertNumChanges([1])
        self.assertEqual(0, models.Repo.objects.count())

    def test_delete_no_match(self):
        response = self.client.delete(reverse('contentdeliveryrepos-detail', args=[999]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertNumChanges([])


class RepositoryMultipleFilterTestCase(APITestCase):
    fixtures = [
        "pdc/apps/release/fixtures/tests/release.json",
        "pdc/apps/release/fixtures/tests/variant.json",
        "pdc/apps/release/fixtures/tests/variant_arch.json",
    ]

    def setUp(self):
        self.url = reverse('contentdeliveryrepos-list')
        services = ['pulp', 'ftp', 'rhn']
        families = ['beta', 'htb', 'dist']
        formats = ['rpm', 'iso', 'kickstart']
        categories = ['debug', 'binary', 'source']
        for service in services:
            for family in families:
                for format in formats:
                    for category in categories:
                        name = 'repo-%s-%s-%s-%s' % (service, family, format, category)
                        data = {
                            'release_id': 'release-1.0', 'variant_uid': 'Server',
                            'arch': 'x86_64', 'service': service, 'repo_family': family,
                            'content_format': format, 'content_category': category,
                            'name': name, 'shadow': False, 'product_id': 33
                        }
                        self.client.post(self.url, data, format='json')

    def test_query_multiple_services(self):
        response = self.client.get(reverse('contentdeliveryrepos-list') + '?service=pulp&service=ftp')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2 * 27)

    def test_multiple_families(self):
        response = self.client.get(reverse('contentdeliveryrepos-list') + '?repo_family=beta&repo_family=htb')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2 * 27)

    def test_multiple_formats(self):
        response = self.client.get(reverse('contentdeliveryrepos-list') + '?content_format=rpm&content_format=iso')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2 * 27)

    def test_multiple_categories(self):
        response = self.client.get(reverse('contentdeliveryrepos-list') + '?content_category=debug&content_category=binary')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2 * 27)

    def test_multiple_names(self):
        response = self.client.get(reverse('contentdeliveryrepos-list') + '?name=repo-pulp-beta-rpm-debug&name=repo-ftp-htb-iso-source')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)

    def test_multiple_combination(self):
        query = ('?service=pulp&service=ftp' +
                 '&repo_family=beta&repo_family=htb' +
                 '&content_format=rpm&content_format=iso' +
                 '&content_category=debug&content_category=binary')
        response = self.client.get(reverse('contentdeliveryrepos-list') + query)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 16)

    def test_multiple_product_id(self):
        response = self.client.patch(reverse('contentdeliveryrepos-detail', args=[1]),
                                     {'product_id': 32},
                                     format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['product_id'], 32)

        response = self.client.patch(reverse('contentdeliveryrepos-detail', args=[2]),
                                     {'product_id': 31},
                                     format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['product_id'], 31)

        response = self.client.get(reverse('contentdeliveryrepos-list') + '?product_id=32&product_id=31')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)


class RepositoryCloneTestCase(TestCaseWithChangeSetMixin, APITestCase):
    fixtures = [
        "pdc/apps/release/fixtures/tests/release.json",
        "pdc/apps/release/fixtures/tests/variant.json",
        "pdc/apps/release/fixtures/tests/variant_arch.json",
        "pdc/apps/repository/fixtures/tests/multiple_repos.json",
    ]

    def setUp(self):
        self.repo1 = {"shadow": False,
                      "release_id": "release-1.1",
                      "variant_uid": "Server",
                      "arch": "x86_64",
                      "service": "rhn",
                      "repo_family": "dist",
                      "content_format": "rpm",
                      "content_category": "binary",
                      "name": "test_repo_1",
                      "product_id": 11}
        self.repo2 = {"shadow": True,
                      "release_id": "release-1.1",
                      "variant_uid": "Client",
                      "arch": "x86_64",
                      "service": "pulp",
                      "repo_family": "beta",
                      "content_format": "iso",
                      "content_category": "debug",
                      "name": "test_repo_2-debug",
                      "product_id": 12}

    def test_missing_data(self):
        response = self.client.post(reverse('repoclone-list'), {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertDictEqual(response.data,
                             {'release_id_from': ['This field is required.'],
                              'release_id_to': ['This field is required.']})
        self.assertNumChanges([])

    def test_extra_data(self):
        response = self.client.post(reverse('repoclone-list'),
                                    {'foo': 'bar', 'release_id_from': 'release-1.0',
                                     'release_id_to': 'release-1.1'},
                                    format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data.get('detail'), 'Unknown fields: "foo".')
        self.assertNumChanges([])

    def test_non_existing_release(self):
        args = {'release_id_from': 'foo', 'release_id_to': 'release-1.1'}
        response = self.client.post(reverse('repoclone-list'), args, format='json')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('detail', response.data)

        args = {'release_id_from': 'release-1.0', 'release_id_to': 'foo'}
        response = self.client.post(reverse('repoclone-list'), args, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertNumChanges([])

    def test_clone(self):
        args = {'release_id_from': 'release-1.0', 'release_id_to': 'release-1.1'}
        response = self.client.post(reverse('repoclone-list'), args, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Drop ids, they are not easily predictable on PostgreSQL
        for repo in response.data:
            del repo['id']
        self.assertItemsEqual(response.data, [self.repo1, self.repo2])
        repos = models.Repo.objects.filter(variant_arch__variant__release__release_id='release-1.1')
        self.assertEqual(len(repos), 3)
        self.assertNumChanges([2])

    def test_clone_with_explicit_includes(self):
        args = {'release_id_from': 'release-1.0', 'release_id_to': 'release-1.1',
                'include_service': ['pulp', 'rhn'],
                'include_repo_family': ['beta', 'dist'],
                'include_content_format': ['iso', 'rpm'],
                'include_content_category': ['debug', 'binary']}
        response = self.client.post(reverse('repoclone-list'), args, format='json')
        for repo in response.data:
            del repo['id']
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertItemsEqual(response.data, [self.repo1, self.repo2])
        repos = models.Repo.objects.filter(variant_arch__variant__release__release_id='release-1.1')
        self.assertEqual(len(repos), 3)
        self.assertNumChanges([2])

    def test_skipping_non_existing_variants(self):
        release_models.VariantArch.objects.get(pk=4).delete()
        args = {'release_id_from': 'release-1.0', 'release_id_to': 'release-1.1'}
        response = self.client.post(reverse('repoclone-list'), args, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        repos = models.Repo.objects.filter(variant_arch__variant__release__release_id='release-1.1')
        self.assertEqual(len(repos), 2)
        self.assertNumChanges([1])

    def test_skip_on_include_service(self):
        args = {'release_id_from': 'release-1.0', 'release_id_to': 'release-1.1',
                'include_service': ['pulp']}
        response = self.client.post(reverse('repoclone-list'), args, format='json')
        for repo in response.data:
            del repo['id']
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertItemsEqual(response.data, [self.repo2])
        self.assertNumChanges([1])

    def test_skip_on_include_repo_family(self):
        args = {'release_id_from': 'release-1.0', 'release_id_to': 'release-1.1',
                'include_repo_family': ['beta']}
        response = self.client.post(reverse('repoclone-list'), args, format='json')
        for repo in response.data:
            del repo['id']
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertItemsEqual(response.data, [self.repo2])
        self.assertNumChanges([1])

    def test_skip_on_include_content_format(self):
        args = {'release_id_from': 'release-1.0', 'release_id_to': 'release-1.1',
                'include_content_format': ['iso']}
        response = self.client.post(reverse('repoclone-list'), args, format='json')
        for repo in response.data:
            del repo['id']
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertItemsEqual(response.data, [self.repo2])
        self.assertNumChanges([1])

    def test_skip_on_include_content_category(self):
        args = {'release_id_from': 'release-1.0', 'release_id_to': 'release-1.1',
                'include_content_category': ['debug']}
        response = self.client.post(reverse('repoclone-list'), args, format='json')
        for repo in response.data:
            del repo['id']
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertItemsEqual(response.data, [self.repo2])
        self.assertNumChanges([1])

    def test_skip_on_include_shadow(self):
        args = {'release_id_from': 'release-1.0', 'release_id_to': 'release-1.1',
                'include_shadow': 'true'}
        response = self.client.post(reverse('repoclone-list'), args, format='json')
        for repo in response.data:
            del repo['id']
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertItemsEqual(response.data, [self.repo2])
        self.assertNumChanges([1])

    def test_skip_on_include_product_id(self):
        args = {'release_id_from': 'release-1.0', 'release_id_to': 'release-1.1',
                'include_product_id': 12}
        response = self.client.post(reverse('repoclone-list'), args, format='json')
        for repo in response.data:
            del repo['id']
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertItemsEqual(response.data, [self.repo2])
        self.assertNumChanges([1])

    def test_with_product_id_value_null(self):
        args = {'release_id_from': 'release-1.1', 'release_id_to': 'release-1.0',
                'include_product_id': None}
        response = self.client.post(reverse('repoclone-list'), args, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]['product_id'], None)
        self.assertNumChanges([1])

    def test_fail_on_bad_include_shadow(self):
        args = {'release_id_from': 'release-1.0', 'release_id_to': 'release-1.1',
                'include_shadow': 'yes please'}
        response = self.client.post(reverse('repoclone-list'), args, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_clone_should_not_create_duplicate(self):
        self.client.post(reverse('contentdeliveryrepos-list'), self.repo1, format='json')
        self.assertNumChanges([1])
        args = {'release_id_from': 'release-1.0', 'release_id_to': 'release-1.1'}
        response = self.client.post(reverse('repoclone-list'), args, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNumChanges([1])
        self.assertEqual(
            models.Repo.objects.filter(variant_arch__variant__release__release_id='release-1.1').count(),
            2
        )

    def test_clone_bad_argument(self):
        args = {'release_id_from': 'release-1.0', 'release_id_to': 'release-1.1',
                'include_service': 'pulp'}
        response = self.client.post(reverse('repoclone-list'), args, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('include_service: "pulp" is not a list', response.data.get('detail'))
        self.assertNumChanges([])


class RepoFamilyTestCase(TestCaseWithChangeSetMixin, APITestCase):
    def test_list_all(self):
        response = self.client.get(reverse('contentdeliveryrepofamily-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 3)

    def test_filter(self):
        response = self.client.get(reverse('contentdeliveryrepofamily-list'), data={"name": "di"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['name'], 'dist')


class RepoBulkTestCase(TestCaseWithChangeSetMixin, APITestCase):
    fixtures = [
        "pdc/apps/release/fixtures/tests/release.json",
        "pdc/apps/release/fixtures/tests/variant.json",
        "pdc/apps/release/fixtures/tests/variant_arch.json",
    ]

    def test_create(self):
        args = [{'release_id': 'release-1.0',
                 'variant_uid': 'Server',
                 'arch': 'x86_64',
                 'service': 'rhn',
                 'repo_family': 'htb',
                 'content_format': 'rpm',
                 'content_category': 'binary',
                 'name': 'repo-1.0-htb-rpms',
                 'shadow': False},
                {'release_id': 'release-1.0',
                 'variant_uid': 'Server',
                 'arch': 'x86_64',
                 'service': 'rhn',
                 'repo_family': 'beta',
                 'content_format': 'rpm',
                 'content_category': 'binary',
                 'name': 'repo-1.0-beta-rpms',
                 'shadow': False}]
        response = self.client.post(reverse('contentdeliveryrepos-list'), args, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertNumChanges([2])
        self.assertEqual(models.Repo.objects.all().count(), 2)

    def test_create_is_atomic(self):
        args = [{'release_id': 'release-1.0',
                 'variant_uid': 'Server',
                 'arch': 'x86_64',
                 'service': 'rhn',
                 'repo_family': 'htb',
                 'content_format': 'rpm',
                 'content_category': 'binary',
                 'name': 'repo-1.0-htb-rpms',
                 'shadow': False},
                {'release_id': 'release-1.0',
                 'variant_uid': 'Server',
                 'arch': 'x86_64',
                 'service': 'rhn',
                 'repo_family': 'beta',
                 'content_format': 'foo',
                 'content_category': 'binary',
                 'name': 'repo-1.0-beta-rpms',
                 'shadow': False}]
        response = self.client.post(reverse('contentdeliveryrepos-list'), args, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.maxDiff = None
        self.assertRegexpMatches(response.data.get('detail', {}).pop('content_format')[0],
                                 "'foo' is not allowed value. Use one of .*")
        self.assertEqual(response.data,
                         {'detail': {},
                          'invalid_data': {'release_id': 'release-1.0',
                                           'variant_uid': 'Server',
                                           'arch': 'x86_64',
                                           'service': 'rhn',
                                           'repo_family': 'beta',
                                           'content_format': 'foo',
                                           'content_category': 'binary',
                                           'name': 'repo-1.0-beta-rpms',
                                           'shadow': False},
                          'id_of_invalid_data': 1})
        self.assertNumChanges([])
        self.assertEqual(models.Repo.objects.all().count(), 0)

    def test_delete_by_ids(self):
        args = [{'release_id': 'release-1.0',
                 'variant_uid': 'Server',
                 'arch': 'x86_64',
                 'service': 'rhn',
                 'repo_family': 'htb',
                 'content_format': 'rpm',
                 'content_category': 'binary',
                 'name': 'repo-1.0-htb-rpms',
                 'product_id': 0,
                 'shadow': False},
                {'release_id': 'release-1.0',
                 'variant_uid': 'Server',
                 'arch': 'x86_64',
                 'service': 'rhn',
                 'repo_family': 'beta',
                 'content_format': 'rpm',
                 'content_category': 'binary',
                 'name': 'repo-1.0-beta-rpms',
                 'product_id': 0,
                 'shadow': False}]
        response = self.client.post(reverse('contentdeliveryrepos-list'), args, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response = self.client.delete(reverse('contentdeliveryrepos-list'),
                                      [r['id'] for r in response.data],
                                      format='json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(models.Repo.objects.count(), 0)
        self.assertNumChanges([2, 2])


class VariantUpdateTestCase(APITestCase):
    fixtures = [
        "pdc/apps/release/fixtures/tests/variants_standalone.json",
    ]

    def setUp(self):
        self.client.post(reverse('contentdeliveryrepos-list'),
                         {'release_id': 'release-1.0', 'name': 'test-repo',
                          'service': 'pulp', 'arch': 'x86_64', 'content_format': 'rpm',
                          'content_category': 'binary', 'variant_uid': 'Server-UID',
                          'repo_family': 'htb'},
                         format='json')

    def test_deleting_variant_with_repos_fails(self):
        response = self.client.delete(reverse('variant-detail', args=['release-1.0/Server-UID']))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(models.Repo.objects.count(), 1)
        self.assertEqual(release_models.Variant.objects.count(), 2)
        self.assertEqual(release_models.VariantArch.objects.count(), 4)

    def test_changing_variants_with_repos_fails(self):
        response = self.client.patch(reverse('variant-detail', args=['release-1.0/Server-UID']),
                                     {'arches': ['ia64']},
                                     format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response = self.client.get(reverse('variant-detail', args=['release-1.0/Server-UID']))
        self.assertDictEqual(dict(response.data),
                             {'release': 'release-1.0', 'name': 'Server name', 'type': 'variant',
                              'id': 'Server', 'uid': 'Server-UID', 'arches': ['ppc64', 'x86_64'],
                              'variant_version': None, 'variant_release': None})

    def test_removing_arch_with_repos_fails(self):
        response = self.client.patch(reverse('variant-detail', args=['release-1.0/Server-UID']),
                                     {'remove_arches': ['x86_64']},
                                     format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response = self.client.get(reverse('variant-detail', args=['release-1.0/Server-UID']))
        self.assertDictEqual(dict(response.data),
                             {'release': 'release-1.0', 'name': 'Server name', 'type': 'variant',
                              'id': 'Server', 'uid': 'Server-UID', 'arches': ['ppc64', 'x86_64'],
                              'variant_version': None, 'variant_release': None})

    def test_adding_another_variant_succeeds(self):
        response = self.client.patch(reverse('variant-detail', args=['release-1.0/Server-UID']),
                                     {'arches': ['ia64', 'ppc64', 'x86_64']},
                                     format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get(reverse('variant-detail', args=['release-1.0/Server-UID']))
        self.assertDictEqual(dict(response.data),
                             {'release': 'release-1.0', 'name': 'Server name', 'type': 'variant',
                              'id': 'Server', 'uid': 'Server-UID', 'arches': ['ia64', 'ppc64', 'x86_64'],
                              'variant_version': None, 'variant_release': None})

    def test_removing_non_relevant_variant_succeeds(self):
        response = self.client.patch(reverse('variant-detail', args=['release-1.0/Server-UID']),
                                     {'arches': ['x86_64']},
                                     format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get(reverse('variant-detail', args=['release-1.0/Server-UID']))
        self.assertDictEqual(dict(response.data),
                             {'release': 'release-1.0', 'name': 'Server name', 'type': 'variant',
                              'id': 'Server', 'uid': 'Server-UID', 'arches': ['x86_64'],
                              'variant_version': None, 'variant_release': None})

    def test_removing_non_relevant_variant_by_patch_succeeds(self):
        response = self.client.patch(reverse('variant-detail', args=['release-1.0/Server-UID']),
                                     {'remove_arches': ['ppc64']},
                                     format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get(reverse('variant-detail', args=['release-1.0/Server-UID']))
        self.assertDictEqual(dict(response.data),
                             {'release': 'release-1.0', 'name': 'Server name', 'type': 'variant',
                              'id': 'Server', 'uid': 'Server-UID', 'arches': ['x86_64'],
                              'variant_version': None, 'variant_release': None})


class ContentCategoryTestCase(APITestCase):
    def test_list_all(self):
        response = self.client.get(reverse('contentdeliverycontentcategory-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 3)


class ContentFormatTestCase(APITestCase):
    def test_list_all(self):
        response = self.client.get(reverse('contentdeliverycontentformat-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 6)


class ServiceTestCase(APITestCase):
    def test_list_all(self):
        response = self.client.get(reverse('contentdeliveryservice-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 3)
