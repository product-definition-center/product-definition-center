#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
import mock

from django.core.urlresolvers import reverse
from django.db.models import ProtectedError

from rest_framework import status
from rest_framework.test import APITestCase

from pdc.apps.common.test_utils import TestCaseWithChangeSetMixin
from .models import RoleContact, Person


class ContactRoleRESTTestCase(TestCaseWithChangeSetMixin, APITestCase):
    fixtures = ['pdc/apps/contact/fixtures/tests/contact_role.json', ]

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
        RoleContact.specific_objects.create(username='person1', email='person1@test.com',
                                            contact_role='qe_ack')

        url = reverse('contactrole-detail', args=['qe_ack'])
        response = self.client.delete(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("protected", response.content)
        self.assertNumChanges([])


class PersonRESTTestCase(TestCaseWithChangeSetMixin, APITestCase):
    fixtures = ['pdc/apps/contact/fixtures/tests/person.json', ]

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
        RoleContact.specific_objects.create(username='person1', email='person1@test.com',
                                            contact_role='qe_ack')

        url = reverse('person-detail', args=[3])
        response = self.client.delete(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("protected", response.content)
        self.assertNumChanges([])


class MaillistRESTTestCase(TestCaseWithChangeSetMixin, APITestCase):
    fixtures = ['pdc/apps/contact/fixtures/tests/maillist.json', ]

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
        RoleContact.specific_objects.create(mail_name='maillist1', email='maillist1@test.com',
                                            contact_role='qe_ack')

        url = reverse('maillist-detail', args=[1])
        response = self.client.delete(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("protected", response.content)
        self.assertNumChanges([])

    def test_multi_delete_protect_no_change_set(self):
        RoleContact.specific_objects.create(mail_name='maillist1', email='maillist1@test.com',
                                            contact_role='qe_ack')

        url = reverse('maillist-detail', args=[1])
        #  try to delete it multi times, verify changes count
        self.client.delete(url, format='json')
        self.client.delete(url, format='json')
        self.client.delete(url, format='json')
        self.assertNumChanges([])


class RoleContactRESTTestCase(TestCaseWithChangeSetMixin, APITestCase):

    def setUp(self):
        super(RoleContactRESTTestCase, self).setUp()

        RoleContact.specific_objects.create(username='person1', email='person1@test.com', contact_role='qe_ack')
        RoleContact.specific_objects.create(username='person2', email='person2@test.com', contact_role='pm')
        RoleContact.specific_objects.create(mail_name='maillist1', email='maillist1@test.com', contact_role='qe_team')
        RoleContact.specific_objects.create(mail_name='maillist2', email='maillist2@test.com', contact_role='devel_team')

    def test_create_with_new_type_should_not_be_allowed(self):
        url = reverse('rolecontact-list')
        data = {'contact': {'username': 'person1', 'email': 'person1@test.com'},
                'contact_role': 'new_type'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_changeset_with_new_person(self):
        url = reverse('rolecontact-list')
        data = {'contact': {'username': 'new_person', 'email': 'new_person@test.com'},
                'contact_role': 'pm'}
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data.get('contact').get('username'), 'new_person')
        self.assertEqual(response.data.get('contact').get('email'), 'new_person@test.com')
        self.assertEqual(response.data.get('contact_role'), 'pm')
        self.assertNumChanges([2])

    def test_create_with_person(self):
        url = reverse('rolecontact-list')
        data = {'contact': {'username': 'test_person', 'email': 'test@test.com'},
                'contact_role': 'qe_ack'}
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data.get('contact').get('username'), 'test_person')
        self.assertEqual(response.data.get('contact').get('email'), 'test@test.com')
        self.assertEqual(response.data.get('contact_role'), 'qe_ack')
        self.assertNumChanges([2])

    def test_create_with_maillist(self):
        url = reverse('rolecontact-list')
        data = {'contact': {'mail_name': 'test_mail', 'email': 'test@test.com'},
                'contact_role': 'qe_ack'}
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data.get('contact').get('mail_name'), 'test_mail')
        self.assertEqual(response.data.get('contact').get('email'), 'test@test.com')
        self.assertEqual(response.data.get('contact_role'), 'qe_ack')
        self.assertNumChanges([2])

    def test_create_with_wrong_field(self):
        url = reverse('rolecontact-list')
        data = {'wrong_name': 'test_type'}
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'detail': 'Unknown fields: "wrong_name".'})
        self.assertNumChanges([])

    def test_create_with_missing_field(self):
        url = reverse('rolecontact-list')
        response = self.client.post(url, {}, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {"contact_role": ["This field is required."],
                                         "contact": ["This field is required."]})
        self.assertNumChanges([])

    def test_create_with_invalid_object_field(self):
        url = reverse('rolecontact-list')
        data = {'contact': {'username': 'person1', 'invalid_key': 'person1@test.com'},
                'contact_role': 'qe_ack'}

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('invalid_key', response.content)
        self.assertNumChanges([])

    def test_create_with_exists_value(self):
        url = reverse('rolecontact-list')
        data = {'contact': {'username': 'person1', 'email': 'person1@test.com'},
                'contact_role': 'qe_ack'}
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {"non_field_errors": ["The fields (\'contact\', \'contact_role\') must make a unique set."]})
        self.assertNumChanges([])

    def test_create_with_bad_type(self):
        url = reverse('rolecontact-list')
        data = {'contact': {'person_name': 'person1', 'e-mail': 'person1@test.com'},
                'contact_role': 'qe_ack'}
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {"contact": ["Could not determine type of contact."]})
        self.assertNumChanges([])

    def test_get(self):
        url = reverse('rolecontact-detail', args=[1])
        response = self.client.get(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('contact').get('username'), 'person1')
        self.assertEqual(response.data.get('contact').get('email'), 'person1@test.com')
        self.assertEqual(response.data.get('contact_role'), 'qe_ack')

    def test_query_with_username(self):
        url = reverse('rolecontact-list')
        response = self.client.get(url + '?username=person2', format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('results')[0].get('contact').get('username'), 'person2')

    def test_query_with_mail_name(self):
        url = reverse('rolecontact-list')
        response = self.client.get(url + '?mail_name=maillist2', format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('results')[0].get('contact').get('mail_name'), 'maillist2')

    def test_query_with_email(self):
        url = reverse('rolecontact-list')
        response = self.client.get(url + '?email=person2@test.com', format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('results')[0].get('contact').get('email'), 'person2@test.com')

    def test_query_with_contact_role(self):
        url = reverse('rolecontact-list')
        response = self.client.get(url + '?contact_role=pm', format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('results')[0].get('contact_role'), 'pm')

    def test_query_with_username_list(self):
        url = reverse('rolecontact-list')
        response = self.client.get(url + '?username=person1&username=person2', format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 2)
        self.assertEqual(response.data.get('results')[0].get('contact').get('username'), 'person1')
        self.assertEqual(response.data.get('results')[1].get('contact').get('username'), 'person2')

    def test_query_with_mail_name_list(self):
        url = reverse('rolecontact-list')
        response = self.client.get(url + '?mail_name=maillist1&mail_name=maillist2', format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 2)
        self.assertEqual(response.data.get('results')[0].get('contact').get('mail_name'), 'maillist1')
        self.assertEqual(response.data.get('results')[1].get('contact').get('mail_name'), 'maillist2')

    def test_query_with_email_list(self):
        url = reverse('rolecontact-list')
        response = self.client.get(url + '?email=person1@test.com&email=maillist2@test.com', format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 2)
        self.assertEqual(response.data.get('results')[0].get('contact').get('email'), 'person1@test.com')
        self.assertEqual(response.data.get('results')[1].get('contact').get('email'), 'maillist2@test.com')

    def test_query_with_contact_role_list(self):
        url = reverse('rolecontact-list')
        response = self.client.get(url + '?contact_role=qe_ack&contact_role=qe_team', format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 2)
        self.assertEqual(response.data.get('results')[0].get('contact_role'), 'qe_ack')
        self.assertEqual(response.data.get('results')[1].get('contact_role'), 'qe_team')

    def test_query_with_username_mail_name_mixup(self):
        url = reverse('rolecontact-list')
        response = self.client.get(url + '?username=person1&mail_name=maillist2', format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 2)
        self.assertEqual(response.data.get('results')[0].get('contact').get('username'), 'person1')
        self.assertEqual(response.data.get('results')[1].get('contact').get('mail_name'), 'maillist2')

    def test_query_with_username_email_mixup(self):
        url = reverse('rolecontact-list')
        response = self.client.get(url + '?username=person1&email=maillist2@test.com', format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 0)

        response = self.client.get(url + '?username=person1&email=person1@test.com', format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 1)
        self.assertEqual(response.data.get('results')[0].get('contact').get('username'), 'person1')

    def test_query_with_username_contact_role_mixup(self):
        url = reverse('rolecontact-list')
        response = self.client.get(url + '?username=person1&contact_role=pm', format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 0)
        response = self.client.get(url + '?username=person1&contact_role=qe_ack', format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 1)
        self.assertEqual(response.data.get('results')[0].get('contact').get('username'), 'person1')
        self.assertEqual(response.data.get('results')[0].get('contact_role'), 'qe_ack')

    def test_query_with_mail_name_email_mixup(self):
        url = reverse('rolecontact-list')
        response = self.client.get(url + '?mail_name=maillist1&email=maillist2@test.com', format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 0)

        response = self.client.get(url + '?mail_name=maillist1&email=maillist1@test.com', format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 1)
        self.assertEqual(response.data.get('results')[0].get('contact').get('mail_name'), 'maillist1')
        self.assertEqual(response.data.get('results')[0].get('contact').get('email'), 'maillist1@test.com')

    def test_query_with_mail_name_contact_role_mixup(self):
        url = reverse('rolecontact-list')
        response = self.client.get(url + '?mail_name=maillist1&contact_role=devel_team', format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 0)

        response = self.client.get(url + '?mail_name=maillist1&contact_role=qe_team', format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 1)
        self.assertEqual(response.data.get('results')[0].get('contact').get('mail_name'), 'maillist1')
        self.assertEqual(response.data.get('results')[0].get('contact_role'), 'qe_team')

    def test_query_with_email_contact_role_mixup(self):
        url = reverse('rolecontact-list')
        response = self.client.get(url + '?email=person1@test.com&contact_role=pm', format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 0)

        response = self.client.get(url + '?email=person1@test.com&contact_role=qe_ack', format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 1)
        self.assertEqual(response.data.get('results')[0].get('contact').get('email'), 'person1@test.com')
        self.assertEqual(response.data.get('results')[0].get('contact_role'), 'qe_ack')

    def test_query_with_multi_key_list(self):
        url = reverse('rolecontact-list')
        response = self.client.get(url + '?username=person1&username=person2&contact_role=pm', format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 1)
        self.assertEqual(response.data.get('results')[0].get('contact').get('username'), 'person2')
        response = self.client.get(url + '?username=person1&username=person2&contact_role=pm&contact_role=qe_ack', format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 2)
        self.assertEqual(response.data.get('results')[0].get('contact').get('username'), 'person1')
        self.assertEqual(response.data.get('results')[1].get('contact').get('username'), 'person2')

    def test_patch_update_with_contact_role(self):
        url = reverse('rolecontact-detail', args=[1])
        data = {'contact_role': 'pm'}
        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('contact_role'), 'pm')
        self.assertNumChanges([1])

    def test_patch_update_with_contact(self):
        url = reverse('rolecontact-detail', args=[1])
        data = {'contact': {'username': 'new_name', 'email': 'new@test.com'}}
        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('contact').get('username'), 'new_name')
        self.assertEqual(response.data.get('contact').get('email'), 'new@test.com')
        self.assertNumChanges([2])

    def test_patch_update_with_bad_contact(self):
        url = reverse('rolecontact-detail', args=[1])
        data = {'contact': {'mali_list': 'new_name', 'email': 'new@test.com'}}
        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {"contact": ["Could not determine type of contact."]})
        self.assertNumChanges([])

    def test_partial_update_empty(self):
        response = self.client.patch(reverse('rolecontact-detail', args=[1]), {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNumChanges([])

    def test_put_update(self):
        url = reverse('rolecontact-detail', args=[1])
        data = {'contact': {'username': 'new_name', 'email': 'new@test.com'},
                'contact_role': 'pm'}
        response = self.client.put(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('contact').get('username'), 'new_name')
        self.assertEqual(response.data.get('contact').get('email'), 'new@test.com')
        self.assertEqual(response.data.get('contact_role'), 'pm')
        self.assertNumChanges([2])

    def test_put_update_with_bad_data(self):
        url = reverse('rolecontact-detail', args=[1])
        data = {'contact': {'user_name': 'new_name', 'email': 'new@test.com'},
                'contact_role': 'pm'}
        response = self.client.put(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'contact': ['Could not determine type of contact.']})
        self.assertNumChanges([])

    def test_delete(self):
        url = reverse('rolecontact-detail', args=[1])
        response = self.client.delete(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertNumChanges([1])

    @mock.patch('rest_framework.mixins.DestroyModelMixin.destroy')
    def test_delete_protect(self, mock_destory):
        mock_destory.side_effect = ProtectedError("fake PE", None)
        url = reverse('rolecontact-detail', args=[1])
        response = self.client.delete(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {"detail": "fake PE None"})
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
