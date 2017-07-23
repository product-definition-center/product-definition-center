#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#

from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase

from pdc.apps.common.test_utils import TestCaseWithChangeSetMixin
from pdc.apps.component import models as component_models
from .models import ContactRole, Person, Maillist, GlobalComponentContact, ReleaseComponentContact


class ContactRoleRESTTestCase(TestCaseWithChangeSetMixin, APITestCase):
    fixtures = ['pdc/apps/component/fixtures/tests/global_component.json',
                'pdc/apps/contact/fixtures/tests/contact_role.json',
                'pdc/apps/contact/fixtures/tests/person.json',
                'pdc/apps/component/fixtures/tests/upstream.json'
                ]

    def test_create(self):
        url = reverse('contactrole-list')
        data = {'name': 'test_role'}
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data.get('name'), 'test_role')
        self.assertNumChanges([1])

    def test_create_with_wrong_field(self):
        url = reverse('contactrole-list')
        data = {'wrong_name': 'test_role'}
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'detail': 'Unknown fields: "wrong_name".'})
        self.assertNumChanges([])

    def test_create_with_missing_field(self):
        url = reverse('contactrole-list')
        response = self.client.post(url, {}, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {"name": ["This field is required."]})
        self.assertNumChanges([])

    def test_create_with_wrong_value(self):
        url = reverse('contactrole-list')
        data = {'name': None}
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {"name": ["This field may not be null."]})
        self.assertNumChanges([])

    def test_get(self):
        url = reverse('contactrole-detail', args=['qe_ack'])
        response = self.client.get(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('name'), 'qe_ack')

    def test_query(self):
        url = reverse('contactrole-list')
        response = self.client.get(url + '?name=qe_ack', format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('results')[0].get('name'), 'qe_ack')

    def test_update(self):
        url = reverse('contactrole-detail', args=['qe_ack'])
        data = {'name': 'new_role'}
        response = self.client.put(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('name'), 'new_role')
        self.assertNumChanges([1])

    def test_delete(self):
        url = reverse('contactrole-detail', args=['qe_ack'])
        response = self.client.delete(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertNumChanges([1])

    def test_delete_protect(self):
        GlobalComponentContact.objects.create(
            component=component_models.GlobalComponent.objects.get(name='MySQL-python'),
            role=ContactRole.objects.get(name='qe_ack'),
            contact=Person.objects.get(username='person1'))

        url = reverse('contactrole-detail', args=['qe_ack'])
        response = self.client.delete(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("protected", response.content)
        self.assertNumChanges([])

    def test_update_limit_unlimited(self):
        response = self.client.patch(reverse('contactrole-detail', args=['allow_3_role']),
                                     {'count_limit': 'unlimited'},
                                     format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNumChanges([1])
        role = ContactRole.objects.get(name='allow_3_role')
        self.assertEqual(role.count_limit, ContactRole.UNLIMITED)

    def test_update_limit_with_random_string(self):
        response = self.client.patch(reverse('contactrole-detail', args=['allow_3_role']),
                                     {'count_limit': 'many'},
                                     format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNumChanges([])

    def test_update_limit_to_negative(self):
        response = self.client.patch(reverse('contactrole-detail', args=['allow_3_role']),
                                     {'count_limit': -1},
                                     format='json')
        self.assertIn('greater than or equal to 0',
                      response.data.get('count_limit')[0])
        self.assertNumChanges([])

    def test_update_missing_optional_fields_are_erased(self):
        response = self.client.put(reverse('contactrole-detail', args=['allow_3_role']),
                                   {'name': 'new_name'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count_limit'], 1)
        self.assertNumChanges([1])


class PersonRESTTestCase(TestCaseWithChangeSetMixin, APITestCase):
    fixtures = ['pdc/apps/component/fixtures/tests/global_component.json',
                'pdc/apps/contact/fixtures/tests/contact_role.json',
                'pdc/apps/contact/fixtures/tests/person.json',
                'pdc/apps/component/fixtures/tests/upstream.json'
                ]

    def test_create(self):
        url = reverse('person-list')
        data = {'username': 'test_person', 'email': 'test@test.com'}
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data.get('username'), 'test_person')
        self.assertEqual(response.data.get('email'), 'test@test.com')
        self.assertNumChanges([1])

    def test_create_with_wrong_field(self):
        url = reverse('person-list')
        data = {'wrong_name': 'test'}
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'detail': 'Unknown fields: "wrong_name".'})
        self.assertNumChanges([])

    def test_create_with_missing_field(self):
        url = reverse('person-list')
        response = self.client.post(url, {}, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {"username": ["This field is required."],
                                         "email": ["This field is required."]})
        self.assertNumChanges([])

    def test_create_with_wrong_value(self):
        url = reverse('person-list')
        data = {'username': None, 'email': None}
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {"username": ["This field may not be null."],
                                         "email": ["This field may not be null."]})
        self.assertNumChanges([])

    def test_get(self):
        url = reverse('person-detail', args=[3])
        response = self.client.get(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('username'), 'person1')

    def test_get_second_page(self):
        url = reverse('person-list')
        for i in range(50):
            self.client.post(url,
                             {'username': 'Dude %d' % i,
                              'email': 'dude%d@example.com' % i},
                             format='json')
        response = self.client.get(url, {'page': 2}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(response.data.get('next'))
        self.assertIsNotNone(response.data.get('previous'))

    def test_query(self):
        url = reverse('person-list')
        response = self.client.get(url + '?username=person2', format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('results')[0].get('username'), 'person2')

    def test_query_with_multiple_values(self):
        url = reverse('person-list')
        response = self.client.get(url + '?username=person2&username=person1', format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)
        self.assertEqual(response.data.get('results')[0].get('username'), 'person1')
        self.assertEqual(response.data.get('results')[1].get('username'), 'person2')

    def test_query_with_wrong_username(self):
        url = reverse('person-list')
        response = self.client.get(url + '?username=person3', format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 0)

    def test_query_combine_with_wrong_username(self):
        url = reverse('person-list')
        response = self.client.get(url + '?username=person1&username=person3', format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data.get('results')[0].get('username'), 'person1')

    def test_query_with_incorrect_combination(self):
        url = reverse('person-list')
        response = self.client.get(url + '?username=person1&email=person2@test.com', format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 0)

    def test_query_with_correct_combination(self):
        url = reverse('person-list')
        response = self.client.get(url + '?username=person1&email=person1@test.com', format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data.get('results')[0].get('username'), 'person1')

    def test_patch_update(self):
        url = reverse('person-detail', args=[3])
        data = {'username': 'new_name'}
        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('username'), 'new_name')
        self.assertNumChanges([1])

    def test_put_update(self):
        url = reverse('person-detail', args=[3])
        data = {'username': 'new_name', 'email': 'new@test.com'}
        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('username'), 'new_name')
        self.assertEqual(response.data.get('email'), 'new@test.com')
        self.assertNumChanges([1])

    def test_partial_update_empty(self):
        response = self.client.patch(reverse('person-detail', args=[1]), {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNumChanges([])

    def test_delete(self):
        url = reverse('person-detail', args=[3])
        response = self.client.delete(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertNumChanges([1])

    def test_delete_protect(self):
        GlobalComponentContact.objects.create(
            component=component_models.GlobalComponent.objects.get(name='MySQL-python'),
            role=ContactRole.objects.get(name='qe_ack'),
            contact=Person.objects.get(username='person1'))

        url = reverse('person-detail', args=[3])
        response = self.client.delete(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("protected", response.content)
        self.assertNumChanges([])


class MaillistRESTTestCase(TestCaseWithChangeSetMixin, APITestCase):
    fixtures = ['pdc/apps/component/fixtures/tests/global_component.json',
                'pdc/apps/contact/fixtures/tests/contact_role.json',
                'pdc/apps/contact/fixtures/tests/maillist.json',
                'pdc/apps/component/fixtures/tests/upstream.json'
                ]

    def test_create(self):
        url = reverse('maillist-list')
        data = {'mail_name': 'test_person', 'email': 'test@test.com'}
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data.get('mail_name'), 'test_person')
        self.assertEqual(response.data.get('email'), 'test@test.com')
        self.assertNumChanges([1])

    def test_create_with_wrong_field(self):
        url = reverse('maillist-list')
        data = {'wrong_name': 'test'}
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'detail': 'Unknown fields: "wrong_name".'})
        self.assertNumChanges([])

    def test_create_with_missing_field(self):
        url = reverse('maillist-list')
        response = self.client.post(url, {}, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {"mail_name": ["This field is required."],
                                         "email": ["This field is required."]})
        self.assertNumChanges([])

    def test_create_with_extra_field(self):
        url = reverse('maillist-list')
        data = {'mail_name': 'test_person', 'email': 'test@test.com', 'foo': 'bar'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data.get('detail'), 'Unknown fields: "foo".')
        self.assertNumChanges([])

    def test_create_with_wrong_value(self):
        url = reverse('maillist-list')
        data = {'mail_name': None, 'email': None}
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {"mail_name": ["This field may not be null."],
                                         "email": ["This field may not be null."]})
        self.assertNumChanges([])

    def test_get(self):
        url = reverse('maillist-detail', args=[1])
        response = self.client.get(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('mail_name'), 'maillist1')

    def test_query(self):
        url = reverse('maillist-list')
        response = self.client.get(url + '?mail_name=maillist2', format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('results')[0].get('mail_name'), 'maillist2')

    def test_patch_update(self):
        url = reverse('maillist-detail', args=[1])
        data = {'mail_name': 'new_name'}
        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('mail_name'), 'new_name')
        self.assertNumChanges([1])

    def test_put_update(self):
        url = reverse('maillist-detail', args=[1])
        data = {'mail_name': 'new_name', 'email': 'new@test.com'}
        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('mail_name'), 'new_name')
        self.assertEqual(response.data.get('email'), 'new@test.com')
        self.assertNumChanges([1])

    def test_partial_update_empty(self):
        response = self.client.patch(reverse('maillist-detail', args=[1]), {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNumChanges([])

    def test_delete(self):
        url = reverse('maillist-detail', args=[1])
        response = self.client.delete(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertNumChanges([1])

    def test_delete_protect(self):
        GlobalComponentContact.objects.create(
            component=component_models.GlobalComponent.objects.get(name='MySQL-python'),
            role=ContactRole.objects.get(name='qe_ack'),
            contact=Maillist.objects.get(mail_name='maillist1'))

        url = reverse('maillist-detail', args=[1])
        response = self.client.delete(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("protected", response.content)
        self.assertNumChanges([])

    def test_multi_delete_protect_no_change_set(self):
        GlobalComponentContact.objects.create(
            component=component_models.GlobalComponent.objects.get(name='MySQL-python'),
            role=ContactRole.objects.get(name='qe_ack'),
            contact=Maillist.objects.get(mail_name='maillist1'))

        url = reverse('maillist-detail', args=[1])
        #  try to delete it multi times, verify changes count
        self.client.delete(url, format='json')
        self.client.delete(url, format='json')
        self.client.delete(url, format='json')
        self.assertNumChanges([])


class PersonBulkRESTTestCase(TestCaseWithChangeSetMixin, APITestCase):
    def setUp(self):
        self.eve = Person.objects.create(username='Eve', email='eve@example.com').pk
        self.mal = Person.objects.create(username='Mal', email='mal@example.com').pk
        self.non_exist_1 = self.mal + 1
        self.non_exist_2 = self.mal + 2
        self.eve = str(self.eve)
        self.mal = str(self.mal)
        self.persons = [{'username': 'Eve', 'email': 'eve@example.com'},
                        {'username': 'Mal', 'email': 'mal@example.com'}]

    def test_create_successful(self):
        args = [
            {'username': 'Alice',
             'email': 'alice@example.com'},
            {'username': 'Bob',
             'email': 'bob@example.com'}
        ]
        ids = [self.non_exist_1, self.non_exist_2]
        response = self.client.post(reverse('person-list'), args, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        for data, id in zip(args, ids):
            data['id'] = id
        self.assertEqual(response.data, args)
        self.assertNumChanges([2])
        self.assertEqual(Person.objects.all().count(), 4)

    def test_create_with_error(self):
        args = [
            {'username': 'Alice'},
            {'username': 'Bob',
             'email': 'bob@example.com'}
        ]
        response = self.client.post(reverse('person-list'), args, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data,
                         {'detail': {'email': ['This field is required.']},
                          'invalid_data': {'username': 'Alice'},
                          'id_of_invalid_data': 0})
        self.assertNumChanges([])
        self.assertEqual(Person.objects.all().count(), 2)

    def test_destroy_successful(self):
        response = self.client.delete(reverse('person-list'), [self.eve, self.mal], format='json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertNumChanges([2])
        self.assertEqual(Person.objects.all().count(), 0)

    def test_destroy_non_found(self):
        response = self.client.delete(reverse('person-list'),
                                      [self.eve, self.mal, self.non_exist_1],
                                      format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertNumChanges()
        self.assertEqual(Person.objects.all().count(), 2)

    def test_update_successful(self):
        args = {
            self.eve: {'username': 'Alice',
                       'email': 'alice@example.com'},
            self.mal: {'username': 'Bob',
                       'email': 'bob@example.com'}
        }
        expected = {
            self.eve: {'username': 'Alice',
                       'email': 'alice@example.com',
                       'url': 'http://testserver/rest_api/v1/persons/%s/' % self.eve},
            self.mal: {'username': 'Bob',
                       'email': 'bob@example.com',
                       'url': 'http://testserver/rest_api/v1/persons/%s/' % self.mal}
        }
        response = self.client.put(reverse('person-list'), args, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertItemsEqual(response.data, expected)
        self.assertNumChanges([2])
        persons = Person.objects.all()
        self.assertItemsEqual(args.values(), [person.export() for person in persons])

    def test_update_error_bad_data(self):
        args = {
            self.eve: {'username': 'Alice',
                       'email': 'alice@example.com'},
            self.mal: {'username': 'Bob'}
        }
        response = self.client.put(reverse('person-list'), args, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data,
                         {'detail': {'email': ['This field is required.']},
                          'invalid_data': {'username': 'Bob'},
                          'id_of_invalid_data': self.mal})
        self.assertNumChanges([])
        persons = Person.objects.all()
        self.assertItemsEqual(self.persons, [person.export() for person in persons])

    def test_update_error_not_found(self):
        args = {
            self.eve: {'username': 'Alice',
                       'email': 'alice@example.com'},
            self.non_exist_1: {'username': 'Jim',
                               'email': 'jim@example.com'}
        }
        response = self.client.put(reverse('person-list'), args, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data,
                         {'detail': 'Not found.',
                          'invalid_data': {'username': 'Jim',
                                           'email': 'jim@example.com'},
                          'id_of_invalid_data': str(self.non_exist_1)})
        self.assertNumChanges([])
        persons = Person.objects.all()
        self.assertItemsEqual(self.persons, [person.export() for person in persons])

    def test_partial_update_successful(self):
        args = {self.eve: {'username': 'Alice'},
                self.mal: {'username': 'Bob'}}
        expected = {
            self.eve: {'username': 'Alice',
                       'email': 'eve@example.com',
                       'url': 'http://testserver/rest_api/v1/persons/%s/' % self.eve},
            self.mal: {'username': 'Bob',
                       'email': 'mal@example.com',
                       'url': 'http://testserver/rest_api/v1/persons/%s/' % self.mal}
        }
        response = self.client.patch(reverse('person-list'), args, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertItemsEqual(response.data, expected)
        self.assertNumChanges([2])
        for ident in expected.keys():
            expected[ident].pop('url')
        persons = Person.objects.all()
        self.assertItemsEqual(expected.values(), [person.export() for person in persons])

    def test_partial_update_error_bad_data(self):
        args = {self.eve: {'username': 'Alice'},
                self.mal: {'email': 'not-an-email-address'}}
        response = self.client.patch(reverse('person-list'), args, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data,
                         {'detail': {'email': ['Enter a valid email address.']},
                          'invalid_data': {'email': 'not-an-email-address'},
                          'id_of_invalid_data': self.mal})
        self.assertNumChanges([])
        persons = Person.objects.all()
        self.assertItemsEqual(self.persons, [person.export() for person in persons])

    def test_partial_update_error_not_found(self):
        args = {self.eve: {'username': 'Alice'},
                self.non_exist_1: {'email': 'not-an-email-address'}}
        response = self.client.patch(reverse('person-list'), args, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data,
                         {'detail': 'Not found.',
                          'invalid_data': {'email': 'not-an-email-address'},
                          'id_of_invalid_data': str(self.non_exist_1)})
        self.assertNumChanges([])
        persons = Person.objects.all()
        self.assertItemsEqual(self.persons, [person.export() for person in persons])

    def test_partial_update_empty(self):
        response = self.client.patch(reverse('person-list'), {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class GlobalComponentContactRESTTestCase(TestCaseWithChangeSetMixin, APITestCase):
    fixtures = [
        "pdc/apps/component/fixtures/tests/global_component.json",
        "pdc/apps/contact/fixtures/tests/contact_role.json",
        "pdc/apps/contact/fixtures/tests/maillist.json",
        "pdc/apps/contact/fixtures/tests/person.json",
        "pdc/apps/component/fixtures/tests/upstream.json"
    ]

    @classmethod
    def setUpTestData(cls):
        GlobalComponentContact.objects.create(
            component=component_models.GlobalComponent.objects.get(name='MySQL-python'),
            role=ContactRole.objects.get(name='pm'),
            contact=Person.objects.get(username='person1'))
        GlobalComponentContact.objects.create(
            component=component_models.GlobalComponent.objects.get(name='java'),
            role=ContactRole.objects.get(name='qe_ack'),
            contact=Maillist.objects.get(mail_name="maillist2"))

    def setUp(self):
        self.list_url = reverse('globalcomponentcontacts-list')

    def test_list_global_component_contacts(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 2)
        results = response.data.get('results')
        self.assertEqual(results[0]['role'], 'pm')
        self.assertEqual(results[0]['contact']['email'], 'person1@test.com')

        self.assertEqual(results[1]['role'], 'qe_ack')
        self.assertEqual(results[1]['contact']['mail_name'], 'maillist2')

    def test_retrieve_global_component_contacts(self):
        response = self.client.get(self.list_url)
        results = response.data.get('results')
        response = self.client.get(reverse('globalcomponentcontacts-detail', args=[results[1]['id']]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['role'], 'qe_ack')
        self.assertEqual(response.data['contact']['mail_name'], 'maillist2')
        self.assertEqual(response.data['contact']['email'], 'maillist2@test.com')

    def test_destroy_global_component_contacts(self):
        self.client.delete(reverse('globalcomponentcontacts-detail', args=[2]))
        self.assertEqual(0, GlobalComponentContact.objects.filter(pk=2).count())

    def test_filter_global_component_contacts(self):
        response = self.client.get(self.list_url, {'role': 'pm'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

        response = self.client.get(self.list_url, {'role': 'no_such_role'})
        self.assertEqual(response.data['count'], 0)

        response = self.client.get(self.list_url,
                                   {'role': 'qe_ack', 'contact': 'maillist2'})
        self.assertEqual(response.data['count'], 1)

        # should not get anything
        response = self.client.get(self.list_url,
                                   {'role': 'qe_ack', 'contact': 'person1'})
        self.assertEqual(response.data['count'], 0)

        # should not get anything
        response = self.client.get(self.list_url,
                                   {'role': 'pm', 'contact': 'maillist2'})
        self.assertEqual(response.data['count'], 0)

        response = self.client.get(self.list_url, {'component': 'java'})
        self.assertEqual(response.data['count'], 1)

        response = self.client.get(self.list_url, {'component': 'no_component'})
        self.assertEqual(response.data['count'], 0)

    def test_filter_global_component_contacts_by_component_name(self):
        GlobalComponentContact.objects.create(
            component=component_models.GlobalComponent.objects.get(name='python'),
            role=ContactRole.objects.get(name='qe_ack'),
            contact=Maillist.objects.get(mail_name="maillist2"))
        response = self.client.get(self.list_url, {'component': 'java*'})
        self.assertEqual(response.data['count'], 1)

        response = self.client.get(self.list_url, {'component': 'python'})
        self.assertEqual(response.data['count'], 2)

        response = self.client.get(self.list_url, {'component': '^python'})
        self.assertEqual(response.data['count'], 1)

        response = self.client.get(self.list_url, {'component': '.+python'})
        self.assertEqual(response.data['count'], 1)

        response = self.client.get(self.list_url + '?component=java&component=python')
        self.assertEqual(response.data['count'], 3)

        response = self.client.get(self.list_url + '?component=^jav.*&component=^python$')
        self.assertEqual(response.data['count'], 2)

    def test_filter_global_component_contacts_with_empty_component_name(self):
        response = self.client.get(self.list_url + '?component=')
        self.assertEqual(response.data['count'], 0)

    def test_filter_global_component_contacts_with_regexp(self):
        response = self.client.get(self.list_url, {'component': '*abc'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response = self.client.get(self.list_url, {'component': '(abcd'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_global_component_contacts(self):
        data = {'component': 'python', 'role': 'pm', 'contact': {'mail_name': 'maillist2'}}
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(3, GlobalComponentContact.objects.count())

    def test_patch_global_component_contacts(self):
        data = {"contact": {"username": "person2", "email": "person2@test.com"}}
        response = self.client.patch(reverse('globalcomponentcontacts-detail', args=[2]),
                                     data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response.data['contact'].pop('id')
        self.assertEqual(response.data['contact'], data['contact'])
        self.assertNumChanges([1])

    def test_create_global_component_contacts_exceed_count_limit(self):
        data = {'component': 'python', 'role': 'cc', 'contact': {'mail_name': 'maillist2'}}
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        data = {'component': 'python', 'role': 'cc', 'contact': {'mail_name': 'maillist1'}}
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_global_component_contacts_for_unlimited_role(self):
        data = {'component': 'python', 'role': 'watcher', 'contact': {'mail_name': 'maillist2'}}
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        data = {'component': 'python', 'role': 'watcher', 'contact': {'mail_name': 'maillist1'}}
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        data = {'component': 'python', 'role': 'watcher',
                'contact': {"username": "person1", "email": "person1@test.com"}}
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        data = {'component': 'python', 'role': 'watcher',
                'contact': {"username": "person2", "email": "person2@test.com"}}
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_global_component_contacts_for_role_limit_3(self):
        data = {'component': 'python', 'role': 'allow_3_role', 'contact': {'mail_name': 'maillist2'}}
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        data = {'component': 'python', 'role': 'allow_3_role', 'contact': {'mail_name': 'maillist1'}}
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        data = {'component': 'python', 'role': 'allow_3_role',
                'contact': {"username": "person1", "email": "person1@test.com"}}
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        data = {'component': 'python', 'role': 'allow_3_role',
                'contact': {"username": "person2", "email": "person2@test.com"}}
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_patch_global_component_contact_exceed_count_limit(self):
        data = {'component': 'python', 'role': 'cc', 'contact': {'mail_name': 'maillist2'}}
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = {'component': 'python', 'role': 'watcher', 'contact': {'mail_name': 'maillist2'}}
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        pk = response.data['id']
        url = reverse('globalcomponentcontacts-detail', args=[pk])
        data = {'role': 'cc'}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_patch_global_component_contacts_for_role_limit_3(self):
        data = {'component': 'python', 'role': 'allow_3_role', 'contact': {'mail_name': 'maillist2'}}
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        data = {'component': 'python', 'role': 'allow_3_role', 'contact': {'mail_name': 'maillist1'}}
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        data = {'component': 'python', 'role': 'cc',
                'contact': {"username": "person1", "email": "person1@test.com"}}
        response = self.client.post(self.list_url, data, format='json')
        pk_cc = response.data['id']
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        data = {'component': 'python', 'role': 'watcher',
                'contact': {"username": "person2", "email": "person2@test.com"}}
        response = self.client.post(self.list_url, data, format='json')
        pk_watcher = response.data['id']

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # fourth for allow_3_role
        url = reverse('globalcomponentcontacts-detail', args=[pk_cc])
        data = {'role': 'allow_3_role'}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        url = reverse('globalcomponentcontacts-detail', args=[pk_watcher])
        data = {'role': 'allow_3_role'}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # remove one and patch again
        response = self.client.delete(reverse('globalcomponentcontacts-detail', args=[pk_cc]))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        url = reverse('globalcomponentcontacts-detail', args=[pk_watcher])
        data = {'role': 'allow_3_role'}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_constraint_to_contact_role_count_limit_change(self):
        data = {'component': 'python', 'role': 'allow_3_role', 'contact': {'mail_name': 'maillist2'}}
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        data = {'component': 'python', 'role': 'allow_3_role', 'contact': {'mail_name': 'maillist1'}}
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        data = {'component': 'python', 'role': 'allow_3_role',
                'contact': {"username": "person1", "email": "person1@test.com"}}
        response = self.client.post(self.list_url, data, format='json')
        pk = response.data['id']
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        contact_role_url = reverse('contactrole-detail', args=['allow_3_role'])
        data = {'count_limit': '4'}
        response = self.client.patch(contact_role_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        contact_role_url = reverse('contactrole-detail', args=['allow_3_role'])
        data = {'count_limit': '2'}
        response = self.client.patch(contact_role_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # remove one role contact and try again
        response = self.client.delete(reverse('globalcomponentcontacts-detail', args=[pk]))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        data = {'count_limit': '2'}
        response = self.client.patch(contact_role_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_constraint_to_contact_role_count_limit_change_from_unlimited(self):
        # Add 3 contacts for the role
        data = {'component': 'python', 'role': 'allow_unlimited_role', 'contact': {'mail_name': 'maillist2'}}
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        data = {'component': 'python', 'role': 'allow_unlimited_role', 'contact': {'mail_name': 'maillist1'}}
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        data = {'component': 'python', 'role': 'allow_unlimited_role',
                'contact': {"username": "person1", "email": "person1@test.com"}}
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # should not change to 2
        contact_role_url = reverse('contactrole-detail', args=['allow_unlimited_role'])
        data = {'count_limit': '2'}
        response = self.client.patch(contact_role_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # could change it to 3
        contact_role_url = reverse('contactrole-detail', args=['allow_unlimited_role'])
        data = {'count_limit': '3'}
        response = self.client.patch(contact_role_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_constraint_to_contact_role_count_limit_change_for_different_roles(self):
        data = {'component': 'python', 'role': 'allow_3_role', 'contact': {'mail_name': 'maillist2'}}
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        data = {'component': 'python', 'role': 'allow_3_role', 'contact': {'mail_name': 'maillist1'}}
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        data = {'component': 'python', 'role': 'allow_3_role',
                'contact': {"username": "person1", "email": "person1@test.com"}}
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        data = {'component': 'python', 'role': 'cc',
                'contact': {"username": "person1", "email": "person1@test.com"}}
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        contact_role_url = reverse('contactrole-detail', args=['allow_3_role'])
        data = {'count_limit': '2'}
        response = self.client.patch(contact_role_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        contact_role_url = reverse('contactrole-detail', args=['cc'])
        data = {'count_limit': '2'}
        response = self.client.patch(contact_role_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        contact_role_url = reverse('contactrole-detail', args=['cc'])
        data = {'count_limit': '1'}
        response = self.client.patch(contact_role_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class ReleaseComponentContactRESTTestCase(TestCaseWithChangeSetMixin, APITestCase):
    fixtures = [
        "pdc/apps/component/fixtures/tests/global_component.json",
        "pdc/apps/release/fixtures/tests/release.json",
        "pdc/apps/component/fixtures/tests/release_component.json",
        "pdc/apps/contact/fixtures/tests/contact_role.json",
        "pdc/apps/contact/fixtures/tests/maillist.json",
        "pdc/apps/contact/fixtures/tests/person.json",
        "pdc/apps/component/fixtures/tests/upstream.json"
    ]

    @classmethod
    def setUpTestData(cls):
        ReleaseComponentContact.objects.create(
            component=component_models.ReleaseComponent.objects.get(name='MySQL-python'),
            role=ContactRole.objects.get(name='pm'),
            contact=Person.objects.get(username='person1'))
        ReleaseComponentContact.objects.create(
            component=component_models.ReleaseComponent.objects.get(name='python27'),
            role=ContactRole.objects.get(name='qe_ack'),
            contact=Maillist.objects.get(mail_name='maillist2'))

    def setUp(self):
        self.list_url = reverse('releasecomponentcontacts-list')

    def test_list_release_component_contacts(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 2)
        results = response.data.get('results')
        for result in results:
            if result['id'] == 1:
                self.assertEqual(result['role'], 'pm')
                self.assertEqual(result['contact']['email'], 'person1@test.com')
            else:
                self.assertEqual(result['role'], 'qe_ack')
                self.assertEqual(result['contact']['mail_name'], 'maillist2')

    def test_retrieve_release_component_contacts(self):
        response = self.client.get(reverse('releasecomponentcontacts-detail', args=[2]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['role'], 'qe_ack')
        self.assertEqual(response.data['contact']['mail_name'], 'maillist2')
        self.assertEqual(response.data['contact']['email'], 'maillist2@test.com')

    def test_destroy_release_component_contact(self):
        response = self.client.delete(reverse('releasecomponentcontacts-detail', args=[2]))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(0, ReleaseComponentContact.objects.filter(pk=2).count())

    def test_filter_release_component_contacts(self):
        response = self.client.get(self.list_url, {'role': 'pm'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

        response = self.client.get(self.list_url, {'role': 'no_such_role'})
        self.assertEqual(response.data['count'], 0)

        response = self.client.get(self.list_url, {'role': 'qe_ack', 'contact': 'maillist2'})
        self.assertEqual(response.data['count'], 1)

        # should not get anything
        response = self.client.get(self.list_url, {'role': 'qe_ack', 'contact': 'person1'})
        self.assertEqual(response.data['count'], 0)

        # should not get anything
        response = self.client.get(self.list_url, {'role': 'pm', 'contact': 'maillist2'})
        self.assertEqual(response.data['count'], 0)

        response = self.client.get(self.list_url, {'component': 'python27'})
        self.assertEqual(response.data['count'], 1)

        response = self.client.get(self.list_url, {'component': 'missing'})
        self.assertEqual(response.data['count'], 0)

    def test_filter_by_global_component(self):
        response = self.client.get(self.list_url, {'global_component': 'python'})
        self.assertEqual(response.data['count'], 1)

    def test_filter_by_email(self):
        response = self.client.get(self.list_url, {'email': 'person1@test.com'})
        self.assertEqual(response.data['count'], 1)

        response = self.client.get(self.list_url, {'email': 'maillist2@test.com'})
        self.assertEqual(response.data['count'], 1)

        response = self.client.get(self.list_url,
                                   {'email': ['maillist2@test.com', 'person1@test.com']})
        self.assertEqual(response.data['count'], 2)

        response = self.client.get(self.list_url, {'email': 'bad@test.com'})
        self.assertEqual(response.data['count'], 0)

    def test_filter_release_component_contacts_by_component_name(self):
        # component names are python27 and MySQL-python
        response = self.client.get(self.list_url, {'component': 'python'})
        self.assertEqual(response.data['count'], 2)

        response = self.client.get(self.list_url, {'component': '^python'})
        self.assertEqual(response.data['count'], 1)

        response = self.client.get(self.list_url, {'component': 'python$'})
        self.assertEqual(response.data['count'], 1)

        response = self.client.get(self.list_url, {'component': 'python.'})
        self.assertEqual(response.data['count'], 1)

        response = self.client.get(self.list_url + '?component=python27&component=MySQL-python')
        self.assertEqual(response.data['count'], 2)

        response = self.client.get(self.list_url + '?component=^python&component=python$')
        self.assertEqual(response.data['count'], 2)

    def test_filter_release_component_contacts_with_empty_component_name(self):
        response = self.client.get(self.list_url + '?component=')
        self.assertEqual(response.data['count'], 0)

    def test_filter_release_component_contacts_with_regexp(self):
        response = self.client.get(self.list_url, {'component': '*abc'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response = self.client.get(self.list_url, {'component': '(abcd'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_release_component_contacts(self):
        data = {'component': {'id': 2}, 'role': 'cc', 'contact': {'mail_name': 'maillist2'}}
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(3, ReleaseComponentContact.objects.count())

    def test_patch_release_component_contacts(self):
        url = reverse('releasecomponentcontacts-detail', args=[2])
        data = {"contact": {"username": "person2", "email": "person2@test.com"}}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response.data['contact'].pop('id')
        self.assertEqual(response.data['contact'], data['contact'])
        self.assertNumChanges([1])

    def test_create_release_component_contacts_exceed_count_limit(self):
        data = {'component': {'id': 2}, 'role': 'cc', 'contact': {'mail_name': 'maillist2'}}
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        data = {'component': {'id': 2}, 'role': 'cc', 'contact': {'mail_name': 'maillist1'}}
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_release_component_contacts_for_unlimited_role(self):
        data = {'component': {'id': 2}, 'role': 'watcher', 'contact': {'mail_name': 'maillist2'}}
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        data = {'component': {'id': 2}, 'role': 'watcher', 'contact': {'mail_name': 'maillist1'}}
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        data = {'component': {'id': 2}, 'role': 'watcher',
                'contact': {"username": "person1", "email": "person1@test.com"}}
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        data = {'component': {'id': 2}, 'role': 'watcher',
                'contact': {"username": "person2", "email": "person2@test.com"}}
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_release_component_contacts_for_role_limit_3(self):
        data = {'component': {'id': 2}, 'role': 'allow_3_role', 'contact': {'mail_name': 'maillist2'}}
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        data = {'component': {'id': 2}, 'role': 'allow_3_role', 'contact': {'mail_name': 'maillist1'}}
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        data = {'component': {'id': 2}, 'role': 'allow_3_role',
                'contact': {"username": "person1", "email": "person1@test.com"}}
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        data = {'component': {'id': 2}, 'role': 'allow_3_role',
                'contact': {"username": "person2", "email": "person2@test.com"}}
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_patch_release_component_contact_exceed_count_limit(self):
        data = {'component': {'id': 2}, 'role': 'cc', 'contact': {'mail_name': 'maillist2'}}
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = {'component': {'id': 2}, 'role': 'watcher', 'contact': {'mail_name': 'maillist2'}}
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        pk = response.data['id']
        url = reverse('releasecomponentcontacts-detail', args=[pk])
        data = {'role': 'cc'}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_patch_release_component_contacts_for_role_limit_3(self):
        data = {'component': {'id': 2}, 'role': 'allow_3_role', 'contact': {'mail_name': 'maillist2'}}
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        data = {'component': {'id': 2}, 'role': 'allow_3_role', 'contact': {'mail_name': 'maillist1'}}
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        data = {'component': {'id': 2}, 'role': 'cc',
                'contact': {"username": "person1", "email": "person1@test.com"}}
        response = self.client.post(self.list_url, data, format='json')
        pk_cc = response.data['id']
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        data = {'component': {'id': 2}, 'role': 'watcher',
                'contact': {"username": "person2", "email": "person2@test.com"}}
        response = self.client.post(self.list_url, data, format='json')
        pk_watcher = response.data['id']

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # fourth for allow_3_role
        url = reverse('releasecomponentcontacts-detail', args=[pk_cc])
        data = {'role': 'allow_3_role'}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        url = reverse('releasecomponentcontacts-detail', args=[pk_watcher])
        data = {'role': 'allow_3_role'}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # remove one and patch again
        response = self.client.delete(reverse('releasecomponentcontacts-detail', args=[pk_cc]))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        url = reverse('releasecomponentcontacts-detail', args=[pk_watcher])
        data = {'role': 'allow_3_role'}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_constraint_to_contact_role_count_limit_change(self):
        data = {'component': {'id': 2}, 'role': 'allow_3_role', 'contact': {'mail_name': 'maillist2'}}
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        data = {'component': {'id': 2}, 'role': 'allow_3_role', 'contact': {'mail_name': 'maillist1'}}
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        data = {'component': {'id': 2}, 'role': 'allow_3_role',
                'contact': {"username": "person1", "email": "person1@test.com"}}
        response = self.client.post(self.list_url, data, format='json')
        pk = response.data['id']
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        contact_role_url = reverse('contactrole-detail', args=['allow_3_role'])
        data = {'count_limit': '4'}
        response = self.client.patch(contact_role_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        contact_role_url = reverse('contactrole-detail', args=['allow_3_role'])
        data = {'count_limit': '2'}
        response = self.client.patch(contact_role_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # remove one role contact and try again
        response = self.client.delete(reverse('releasecomponentcontacts-detail', args=[pk]))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        data = {'count_limit': '2'}
        response = self.client.patch(contact_role_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_constraint_to_contact_role_count_limit_change_for_different_roles(self):
        data = {'component': {'id': 2}, 'role': 'allow_3_role', 'contact': {'mail_name': 'maillist2'}}
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        data = {'component': {'id': 2}, 'role': 'allow_3_role', 'contact': {'mail_name': 'maillist1'}}
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        data = {'component': {'id': 2}, 'role': 'allow_3_role',
                'contact': {"username": "person1", "email": "person1@test.com"}}
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        data = {'component': {'id': 2}, 'role': 'cc',
                'contact': {"username": "person1", "email": "person1@test.com"}}
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        contact_role_url = reverse('contactrole-detail', args=['allow_3_role'])
        data = {'count_limit': '2'}
        response = self.client.patch(contact_role_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        contact_role_url = reverse('contactrole-detail', args=['cc'])
        data = {'count_limit': '2'}
        response = self.client.patch(contact_role_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        contact_role_url = reverse('contactrole-detail', args=['cc'])
        data = {'count_limit': '1'}
        response = self.client.patch(contact_role_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_should_not_instruct_client_cache_result(self):
        response = self.client.get(self.list_url)
        self.assertTrue(response.has_header('Cache-Control'))
        self.assertTrue('max-age=0' in response['Cache-Control'])

        data = {'component': {'id': 2}, 'role': 'watcher', 'contact': {'mail_name': 'maillist2'}}
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        resuld_id = response.data.get('id')
        response = self.client.get(reverse('releasecomponentcontacts-detail', args=[resuld_id]))
        self.assertTrue(response.has_header('Cache-Control'))
        self.assertTrue('max-age=0' in response['Cache-Control'])
