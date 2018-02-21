#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
import mock
import json

from django.test import TestCase
from django.core.exceptions import ValidationError
from django.utils.datastructures import MultiValueDict
from django.core.urlresolvers import reverse

from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework import serializers

from contrib.drf_introspection.serializers import DynamicFieldsSerializerMixin
from .models import Label, SigKey
from pdc.apps.common import validators
from .test_utils import TestCaseWithChangeSetMixin
from . import renderers, views


class ValidatorTestCase(TestCase):
    def test_generic_validator_fail_wrong_chars(self):
        self.assertRaises(ValidationError, validators._validate_hex_string, "wrong-md5", 9)

    def test_generic_validator_fail_wrong_length(self):
        self.assertRaises(ValidationError, validators._validate_hex_string, "abcdef0123456789", 10)

    def test_validate_md5(self):
        try:
            validators.validate_md5('9aa71fd0d510520acbc13542be5c127f')
        except ValidationError:
            self.fail('Unexpected ValidationError')

    def test_validate_sha1(self):
        try:
            validators.validate_sha1('bda6fa42aef769cc6c2ae2cddd9f8ea93dee0a3f')
        except ValidationError:
            self.fail('Unexpected ValidationError')

    def test_validate_sha256(self):
        try:
            validators.validate_sha256('e1186e900b934e3d125cacd2f96ee768a1906f8ca2033f5a8acf3231652d459d')
        except ValidationError:
            self.fail('Unexpected ValidationError')

    def test_validate_sigkey(self):
        try:
            validators.validate_sigkey('fd431d51')
        except ValidationError:
            self.fail('Unexpected ValidationError')


class DynamicFieldsSerializerMixinTestCase(TestCase):
    def setUp(self):
        class fakeSerializer(object):
            def __init__(self, context=None):
                self.fields = {'a': 'a',
                               'b': 'b',
                               'c': 'c'}
                self.context = context

        class mockSerializer(DynamicFieldsSerializerMixin,
                             fakeSerializer):
            pass

        self.mock_request = mock.Mock()
        self.context = {
            'request': self.mock_request
        }
        self.serializer = mockSerializer

    def test_fields(self):
        serializer = self.serializer(fields=['a', 'b'])
        self.assertEqual(['a', 'b'], serializer.fields.keys())
        serializer = self.serializer(fields=['a', 'b', 'd'])
        self.assertEqual(['a', 'b'], serializer.fields.keys())

    def test_exclude_fields(self):
        serializer = self.serializer(exclude_fields=['b'])
        self.assertEqual(['a', 'c'], serializer.fields.keys())
        serializer = self.serializer(exclude_fields=['b', 'd'])
        self.assertEqual(['a', 'c'], serializer.fields.keys())

    def test_fields_and_exclude(self):
        serializer = self.serializer(fields=['a', 'c'], exclude_fields=['b'])
        self.assertEqual(['a', 'c'], serializer.fields.keys())
        serializer = self.serializer(fields=['a', 'b'], exclude_fields=['b'])
        self.assertEqual(['a'], serializer.fields.keys())

    def test_fields_from_context(self):
        param_dict = {'fields': ['a', 'b'], 'exclude_fields': []}
        self.mock_request.query_params = MultiValueDict(param_dict)
        serializer = self.serializer(context=self.context)
        self.assertEqual(['a', 'b'], serializer.fields.keys())
        param_dict = {'fields': ['d'], 'exclude_fields': []}
        self.mock_request.query_params = MultiValueDict(param_dict)
        serializer = self.serializer(context=self.context)
        self.assertEqual(['a', 'b', 'c'], sorted(serializer.fields.keys()))
        param_dict = {'fields': ['a', 'b', 'd'], 'exclude_fields': []}
        self.mock_request.query_params = MultiValueDict(param_dict)
        serializer = self.serializer(context=self.context)
        self.assertEqual(['a', 'b'], serializer.fields.keys())

    def test_exclude_fields_from_context(self):
        param_dict = {'fields': [], 'exclude_fields': ['b']}
        self.mock_request.query_params = MultiValueDict(param_dict)
        serializer = self.serializer(context=self.context)
        self.assertEqual(['a', 'c'], serializer.fields.keys())
        param_dict = {'fields': [], 'exclude_fields': ['b', 'd']}
        self.mock_request.query_params = MultiValueDict(param_dict)
        serializer = self.serializer(context=self.context)
        self.assertEqual(['a', 'c'], serializer.fields.keys())

    def test_fields_and_exclude_from_context(self):
        param_dict = {'fields': ['a', 'c'], 'exclude_fields': ['b']}
        self.mock_request.query_params = MultiValueDict(param_dict)
        serializer = self.serializer(context=self.context)
        self.assertEqual(['a', 'c'], serializer.fields.keys())
        param_dict = {'fields': ['a', 'b'], 'exclude_fields': ['b']}
        self.mock_request.query_params = MultiValueDict(param_dict)
        serializer = self.serializer(context=self.context)
        self.assertEqual(['a'], serializer.fields.keys())

    def test_both_init_and_context(self):
        param_dict = {'fields': ['a'], 'exclude_fields': ['b']}
        self.mock_request.query_params = MultiValueDict(param_dict)
        serializer = self.serializer(fields=['c'], exclude_fields=['b'],
                                     context=self.context)
        self.assertEqual(['a', 'c'], serializer.fields.keys())


class LabelRESTTestCase(TestCaseWithChangeSetMixin, APITestCase):
    def setUp(self):
        super(LabelRESTTestCase, self).setUp()
        self.args_label1 = {'name': 'label1', 'description': 'label1 description'}
        self.args_label2 = {'name': 'label2', 'description': 'label2 description'}
        self.args_label3 = {'name': 'label3', 'description': 'label3 description'}
        Label.objects.create(**self.args_label1)
        Label.objects.create(**self.args_label2)

    def test_list_labels(self):
        url = reverse('label-list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 2)
        self.assertEqual(response.data.get('results')[0].get('name'), self.args_label1.get('name'))
        self.assertEqual(response.data.get('results')[1].get('name'), self.args_label2.get('name'))

    def test_query_label_with_name(self):
        url = reverse('label-list') + '?name=label1'
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 1)
        self.assertEqual(response.data.get('results')[0].get('name'), self.args_label1.get('name'))
        self.assertEqual(response.data.get('results')[0].get('description'), self.args_label1.get('description'))

    def test_query_labels_with_multiple_names(self):
        url = reverse('label-list') + '?name=label1&name=label2'
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 2)
        self.assertEqual(response.data.get('results')[0].get('name'), self.args_label1.get('name'))
        self.assertEqual(response.data.get('results')[1].get('name'), self.args_label2.get('name'))

    def test_bulk_partial_update(self):
        data = {'1': {'description': 'desc 1'},
                '2': {'description': 'desc 2'}}
        response = self.client.patch(reverse('label-list'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNumChanges([2])

    def test_bulk_delete(self):
        response = self.client.delete(reverse('label-list'), [1, 2], format='json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertNumChanges([2])
        self.assertEqual(Label.objects.count(), 0)

    def test_query_labels_with_none_existing_name(self):
        url = reverse('label-list') + '?name=other'
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 0)

    def test_create_label(self):
        url = reverse('label-list')
        response = self.client.post(url, format='json', data=self.args_label3)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response = self.client.get(url, format='json')
        self.assertEqual(response.data.get('count'), 3)
        self.assertEqual(response.data.get('results')[0].get('name'), self.args_label1.get('name'))
        self.assertEqual(response.data.get('results')[1].get('name'), self.args_label2.get('name'))
        self.assertEqual(response.data.get('results')[2].get('name'), self.args_label3.get('name'))

    def test_create_label_extra_fields(self):
        url = reverse('label-list')
        self.args_label3['foo'] = 'bar'
        response = self.client.post(url, format='json', data=self.args_label3)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data.get('detail'), 'Unknown fields: "foo".')

    def test_create_label_only_name(self):
        url = reverse('label-list')
        response = self.client.post(url, format='json', data={'name': 'label4'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {"description": ["This field is required."]})

    def test_create_label_with_empty(self):
        url = reverse('label-list')
        response = self.client.post(url, format='json', data={})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {"name": ["This field is required."],
                                         "description": ["This field is required."]})

    def test_create_label_with_only_description(self):
        url = reverse('label-list')
        response = self.client.post(url, format='json', data={'description': 'description'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {"name": ["This field is required."]})

    def test_create_existing_label(self):
        url = reverse('label-list')
        response = self.client.post(url, format='json', data=self.args_label1)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(response.data, [{"name": ["This field must be unique."]},  # DRF v3.2 its own UniqueValidator,
                                      {"name": ["Label with this name already exists."]}])  # v3.3 use Django's default.

    def test_put_update(self):
        url = reverse('label-detail', kwargs={'pk': 1})
        args = {'name': 'new name', 'description': 'new description'}
        response = self.client.put(url, format='json', data=args)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('name'), args.get('name'))
        self.assertEqual(response.data.get('description'), args.get('description'))

    def test_update_non_existing_label(self):
        url = reverse('label-detail', kwargs={'pk': 9999})
        args = {'name': 'new name', 'description': 'new description'}
        response = self.client.put(url, format='json', data=args)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data, {"detail": "Not found."})

    def test_patch_update_description(self):
        url = reverse('label-detail', kwargs={'pk': 1})
        args = {'description': 'new description'}
        response = self.client.patch(url, format='json', data=args)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('name'), self.args_label1.get('name'))
        self.assertEqual(response.data.get('description'), args.get('description'))

    def test_patch_update_description_name(self):
        url = reverse('label-detail', kwargs={'pk': 1})
        args = {'name': 'new name'}
        response = self.client.patch(url, format='json', data=args)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('name'), args.get('name'))
        self.assertEqual(response.data.get('description'), self.args_label1.get('description'))

    def test_partial_update_empty(self):
        url = reverse('label-detail', kwargs={'pk': 1})
        response = self.client.patch(url, format='json', data={})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_to_existing_label(self):
        url = reverse('label-detail', kwargs={'pk': 1})
        response = self.client.put(url, format='json', data=self.args_label2)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_delete_label(self):
        url = reverse('label-detail', kwargs={'pk': 1})
        response = self.client.delete(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        response = self.client.get(url, format='json')
        self.assertEqual(response.data.get('detail'), 'Not found.')

    def test_delete_none_existing_label(self):
        url = reverse('label-detail', kwargs={'pk': 9999})
        response = self.client.delete(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data.get('detail'), 'Not found.')


class ArchRESTTestCase(APITestCase):
    def test_list_all_arches(self):
        url = reverse('arch-list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 48)

    def test_create_arch(self):
        url = reverse('arch-list')
        response = self.client.post(url, format='json', data={"name": "arm"})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], "arm")

    def test_create_arch_with_long_name(self):
        url = reverse('arch-list')
        response = self.client.post(url, format='json', data={"name": "a" * 100})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class SigKeyRESTTestCase(TestCaseWithChangeSetMixin, APITestCase):
    def setUp(self):
        SigKey.objects.bulk_create([SigKey(key_id="1234adbf", name="A",
                                           description="icontains_A"),
                                    SigKey(key_id="f2134bca", name="B",
                                           description="icontains_B"),
                                    SigKey(key_id="d343aaaa", name="C",
                                           description="icontains_C")])
        super(SigKeyRESTTestCase, self).setUp()

    def test_list_all_sigkeys(self):
        url = reverse('sigkey-list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 3)

    def test_query_sigkey(self):
        url = reverse('sigkey-list')
        response = self.client.get(url, format='json', data={"name": "B"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    def test_query_icontains_sigkey_(self):
        url = reverse('sigkey-list')
        response = self.client.get(url, format='json', data={
            "description": "ns_c"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['key_id'], 'd343aaaa')

    def test_query_multi_value(self):
        response = self.client.get(reverse('sigkey-list') + '?key_id=1234adbf&key_id=f2134bca')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)

    def test_retrieve_sigkey(self):
        url = reverse('sigkey-detail', kwargs={'key_id': '1234adbf'})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['key_id'], '1234adbf')

    def test_update_sigkey(self):
        url = reverse('sigkey-detail', kwargs={'key_id': '1234adbf'})
        response = self.client.put(url, format='json',
                                   data={'key_id': '1234adbf', 'name': "TEST"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNumChanges([1])
        self.assertEqual(response.data['name'], 'TEST')

    def test_partial_update_sigkey(self):
        url = reverse('sigkey-detail', kwargs={'key_id': '1234adbf'})
        response = self.client.patch(url, format='json', data={'name': "TEST"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'TEST')

    def test_can_update_key_id(self):
        response = self.client.patch(reverse('sigkey-detail', args=['1234adbf']),
                                     {'key_id': 'cafebabe'},
                                     format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('key_id'), 'cafebabe')
        self.assertNumChanges([1])
        response = self.client.get(reverse('sigkey-detail', args=['1234adbf']))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        response = self.client.get(reverse('sigkey-detail', args=['cafebabe']))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_can_bulk_update(self):
        data = {'1234adbf': {'name': 'A',
                             'description': 'icontains_a',
                             'key_id': '1234adbf'}}
        response = self.client.put(reverse('sigkey-list'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNumChanges([1])
        self.assertDictEqual(dict(response.data), data)

    def test_bulk_partial_update(self):
        response = self.client.patch(reverse('sigkey-list'),
                                     {'1234adbf': {'name': 'Key A'},
                                      'f2134bca': {'description': 'icontains b'}},
                                     format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNumChanges([2])
        self.assertDictEqual(dict(response.data),
                             {'1234adbf': {'key_id': '1234adbf',
                                           'name': 'Key A',
                                           'description': 'icontains_A'},
                              'f2134bca': {'key_id': 'f2134bca',
                                           'name': 'B',
                                           'description': 'icontains b'}})

    def test_partial_update_empty(self):
        url = reverse('sigkey-detail', kwargs={'key_id': '1234adbf'})
        response = self.client.patch(url, format='json', data={})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_missing_optional_fields_are_erased(self):
        url = reverse('sigkey-detail', kwargs={'key_id': '1234adbf'})
        response = self.client.put(url, format='json',
                                   data={'key_id': '1234adbf', 'name': "TEST"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'TEST')
        self.assertEqual(response.data['description'], '')
        response = self.client.put(url, format='json',
                                   data={'key_id': '1234adbf', 'description': "TEST"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], None)
        self.assertEqual(response.data['description'], 'TEST')
        self.assertNumChanges([1, 1])

    def test_delete_sigkey(self):
        url = reverse('sigkey-detail', kwargs={'key_id': '1234adbf'})
        response = self.client.delete(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_create_sigkey(self):
        url = reverse('sigkey-list')
        data = {"key_id": "abcd1234", "name": "test", "description": "test"}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertDictEqual(dict(response.data), data)
        self.assertNumChanges([1])


class CachedByArgumentClassTestCase(TestCase):
    @renderers.cached_by_argument_class
    def cached(self, arg, call_id):
        return (arg, call_id)

    def test_same_argument(self):
        class A:
            pass

        a = A()
        self.assertEqual(self.cached(a, 1), (a, 1))
        self.assertEqual(self.cached(a, 2), (a, 1))

    def test_different_instances_same_class(self):
        class A:
            pass

        a1 = A()
        a2 = A()
        self.assertEqual(self.cached(a1, 1), (a1, 1))
        self.assertEqual(self.cached(a2, 2), (a1, 1))

    def test_different_class(self):
        class A:
            pass

        class B:
            pass

        a = A()
        b = B()
        self.assertEqual(self.cached(a, 1), (a, 1))
        self.assertEqual(self.cached(b, 2), (b, 2))

    def test_different_instances_and_classes(self):
        class A:
            pass

        class B:
            pass

        a1 = A()
        a2 = A()
        b1 = B()
        b2 = B()
        self.assertEqual(self.cached(a1, 1), (a1, 1))
        self.assertEqual(self.cached(b1, 2), (b1, 2))
        self.assertEqual(self.cached(a2, 3), (a1, 1))
        self.assertEqual(self.cached(b2, 4), (b1, 2))


class FilterDocumentingTestCase(TestCase):
    def test_filter_fields_have_no_type(self):
        class TestViewset(object):
            filter_fields = ('c', 'b', 'a')
        res = renderers.get_filters(TestViewset())
        self.assertEqual(res, ' * `a`\n * `b`\n * `c`')

    def test_filter_extra_query_params_have_no_type(self):
        class TestViewset(object):
            extra_query_params = ('c', 'b', 'a')
        res = renderers.get_filters(TestViewset())
        self.assertEqual(res, ' * `a`\n * `b`\n * `c`')

    def test_filter_set_has_details(self):
        res = renderers.get_filters(views.SigKeyViewSet())
        self.assertEqual(
            res,
            ' * `description` (string, case insensitive, substring match)\n'
            ' * `key_id` (string)\n'
            ' * `name` (string)'
        )


class SerializerDocumentingTestCase(TestCase):
    def test_describe_by_class_attr(self):
        class DummySerializer(object):
            doc_format = {"foo": "bar"}

        instance = DummySerializer()
        result = renderers.describe_serializer(instance, False)
        self.assertEqual(result, {'foo': 'bar'})

    def test_describe_fields(self):
        class DummySerializer(serializers.Serializer):
            str = serializers.CharField()
            int = serializers.IntegerField()

        instance = DummySerializer()
        result = renderers.describe_serializer(instance, False)
        self.assertEqual(result, {'str': 'string', 'int': 'int'})

    def test_describe_read_only_field(self):
        class DummySerializer(serializers.Serializer):
            field = serializers.CharField(read_only=True)

        instance = DummySerializer()
        result = renderers.describe_serializer(instance, True)
        self.assertEqual(result, {'field (read-only)': 'string'})

    def test_describe_read_only_field_can_be_excluded(self):
        class DummySerializer(serializers.Serializer):
            field = serializers.CharField(read_only=True)

        instance = DummySerializer()
        result = renderers.describe_serializer(instance, False)
        self.assertEqual(result, {})

    def test_describe_nullable_field(self):
        class DummySerializer(serializers.Serializer):
            field = serializers.CharField(allow_null=True)

        instance = DummySerializer()
        result = renderers.describe_serializer(instance, True)
        self.assertEqual(result, {'field (nullable)': 'string'})

    def test_describe_field_with_default_value(self):
        class DummySerializer(serializers.Serializer):
            field = serializers.CharField(required=False, default='foo')

        instance = DummySerializer()
        result = renderers.describe_serializer(instance, True)
        self.assertEqual(result, {'field (optional, default="foo")': 'string'})

    def test_describe_field_with_default_from_model(self):
        default = mock.Mock()
        default.default = True
        DummyModel = mock.Mock()
        DummyModel._meta.get_field = lambda _: default

        class DummySerializer(serializers.Serializer):
            field = serializers.CharField(required=False)

            class Meta:
                model = DummyModel

        instance = DummySerializer()
        result = renderers.describe_serializer(instance, True)
        self.assertEqual(result, {'field (optional, default=true)': 'string'})

    def test_describe_field_with_complex_default(self):
        class DummyDefault(object):
            doc_format = 'some string format'

        class DummySerializer(serializers.Serializer):
            field = serializers.CharField(required=False, default=DummyDefault)

        instance = DummySerializer()
        result = renderers.describe_serializer(instance, True)
        self.assertEqual(result, {'field (optional, default="some string format")': 'string'})

    def test_describe_field_with_custom_type(self):
        class DummyField(serializers.Field):
            doc_format = '{"foo": "bar"}'
            writable_doc_format = '{"baz": "quux"}'

        class DummySerializer(serializers.Serializer):
            field = DummyField()

        instance = DummySerializer()
        result = renderers.describe_serializer(instance, True)
        self.assertEqual(result, {'field': {'foo': 'bar'}})
        result = renderers.describe_serializer(instance, False)
        self.assertEqual(result, {'field': {'baz': 'quux'}})

    def test_describe_nested_serializer(self):
        class DummyNestedSerializer(serializers.Serializer):
            field = serializers.CharField()

        class DummySerializer(serializers.Serializer):
            top_level = DummyNestedSerializer()

        instance = DummySerializer()
        result = renderers.describe_serializer(instance, True)
        self.assertEqual(result, {'top_level': {'field': 'string'}})

    def test_describe_nested_serializer_many(self):
        class DummyNestedSerializer(serializers.Serializer):
            field = serializers.CharField()

        class DummySerializer(serializers.Serializer):
            top_level = DummyNestedSerializer(many=True)

        instance = DummySerializer()
        result = renderers.describe_serializer(instance, True)
        self.assertEqual(result, {'top_level': [{'field': 'string'}]})


class JSONResponseFor404(APITestCase):
    def test_returns_html_without_header(self):
        response = self.client.get('/foo/bar')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('<html>', response.content)

    def test_respects_accept_header(self):
        response = self.client.get('/foo/bar', HTTP_ACCEPT='application/json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        try:
            json.loads(response.content)
        except ValueError:
            self.fail('Response was not JSON')


class OrderingTestCase(APITestCase):
    fixtures = ['pdc/apps/common/fixtures/test/sigkeys.json']

    def test_ordering_single(self):
        response = self.client.get(reverse('sigkey-list'), data={'ordering': 'name'}, format='json')
        self.assertEqual(response.data['count'], 3)
        results = response.data.get('results')
        self.assertLess(results[0].get('name'), results[1].get('name'))
        self.assertLess(results[1].get('name'), results[2].get('name'))

    def test_ordering_single_reverse(self):
        response = self.client.get(reverse('sigkey-list'), data={'ordering': '-key_id'}, format='json')
        self.assertEqual(response.data['count'], 3)
        results = response.data.get('results')
        self.assertGreater(results[0].get('key_id'), results[1].get('key_id'))
        self.assertGreater(results[1].get('key_id'), results[2].get('key_id'))

    def test_ordering_multiple(self):
        response = self.client.get(reverse('sigkey-list'), data={'ordering': 'description,name'}, format='json')
        self.assertEqual(response.data['count'], 3)
        results = response.data.get('results')
        self.assertEqual(results[0].get('description'), 'A')
        self.assertEqual(results[1].get('description'), 'A')
        self.assertLess(results[0].get('name'), results[1].get('name'))
        self.assertLess(results[1].get('description'), results[2].get('description'))

    def test_ordering_bad_key(self):
        response = self.client.get(reverse('sigkey-list'), data={'ordering': 'description_,name'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue('Unknown query key' in response.data.get('detail'))
        self.assertTrue('description_' in response.data.get('detail'))

        response = self.client.get(reverse('sigkey-list'), data={'ordering': 'description,name_'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue('Unknown query key' in response.data.get('detail'))
        self.assertTrue('name_' in response.data.get('detail'))
