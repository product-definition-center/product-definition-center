#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
import mock
import unittest

from django.core.urlresolvers import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from pdc.apps.common.test_utils import TestCaseWithChangeSetMixin
from pdc.apps.contact.models import Person, Maillist, RoleContact, ContactRole
from pdc.apps.release.models import Release, ProductVersion
from . import models


class GlobalComponentRESTTestCase(TestCaseWithChangeSetMixin, APITestCase):
    fixtures = [
        "pdc/apps/component/fixtures/tests/global_component.json",
        "pdc/apps/component/fixtures/tests/upstream.json"
    ]

    def test_list_global_component(self):
        url = reverse('globalcomponent-list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 3)
        names = list(d['name'] for d in response.data['results'])
        self.assertTrue('python' in names)
        self.assertTrue('MySQL-python' in names)

    def test_detail_global_component(self):
        url = reverse('globalcomponent-detail', kwargs={'pk': 1})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'python')
        self.assertIsNone(response.data['dist_git_path'])

    def test_detail_global_component_only_include_name_field(self):
        url = reverse('globalcomponent-detail', kwargs={'pk': 1})
        response = self.client.get(url + '?fields=name', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertDictEqual(response.data, {'name': 'python'})

    def test_detail_global_component_exclude_contacts_fields(self):
        url = reverse('globalcomponent-detail', kwargs={'pk': 1})
        response = self.client.get(url + '?exclude_fields=contacts', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'python')
        self.assertIsNone(response.data['dist_git_path'])
        self.assertNotIn('contacts', response.data)

    def test_create_global_component(self):
        url = reverse('globalcomponent-list')
        data = {'name': 'TestCaseComponent', 'dist_git_path': 'python'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        del response.data['id']
        del response.data['dist_git_web_url']
        data.update({'contacts': []})
        data.update({'labels': []})
        data.update({'upstream': None})
        self.assertEqual(response.data, data)

    def test_create_global_component_extra_fields(self):
        url = reverse('globalcomponent-list')
        data = {'name': 'TestCaseComponent', 'dist_git_path': 'python', 'foo': 'bar'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data.get('detail'), 'Unknown fields: "foo".')

    def test_create_global_component_with_labels(self):
        url = reverse('globalcomponent-list')
        data = {'name': 'TestCaseComponent', 'dist_git_path': 'python', 'labels': [{'name': 'label1', 'description': 'abc'}]}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        del response.data['id']
        del response.data['dist_git_web_url']
        data.update({'contacts': []})
        data.update({'labels': []})
        data.update({'upstream': None})
        self.assertEqual(response.data, data)

    def test_create_global_component_with_upstream(self):
        url = reverse('globalcomponent-list')
        data = {'name': 'TestCaseComponent', 'dist_git_path': 'python',
                'upstream': {'homepage': 'http://python.org', 'scm_type': 'git',
                             'scm_url': 'http://svn.python.org/moduleX'}}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        del response.data['id']
        del response.data['dist_git_web_url']
        data.update({'contacts': []})
        data.update({'labels': []})
        self.assertEqual(response.data, data)

        # for PDC-496
        data = {'name': 'TestCaseComponent2', 'dist_git_path': 'python',
                'upstream': {'homepage': 'http://python.org', 'scm_type': 'svn',
                             'scm_url': 'http://svn.python.org/moduleX22'}}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        del response.data['id']
        del response.data['dist_git_web_url']
        data.update({'contacts': []})
        data.update({'labels': []})
        self.assertEqual(response.data, data)

    def test_update_global_component(self):
        url = reverse('globalcomponent-detail', kwargs={'pk': 1})
        data = {'name': 'Updated', 'dist_git_path': 'python'}
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        del response.data['id']
        del response.data['dist_git_web_url']
        del response.data['contacts']
        del response.data['labels']
        del response.data['upstream']
        self.assertEqual(response.data, data)

    def test_detail_global_component_not_exist(self):
        url = reverse('globalcomponent-detail', kwargs={'pk': 999})
        response = self.client.get(url, format='json')
        data = {'detail': 'Not found.'}
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data, data)

    def test_create_global_component_duplicate(self):
        url = reverse('globalcomponent-list')
        data = {'name': 'python', 'dist_git_path': 'rpm/python'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_global_component_only_with_name(self):
        url = reverse('globalcomponent-list')
        data = {'name': 'OnlyHasName'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_global_component_only_with_dist_path(self):
        url = reverse('globalcomponent-list')
        data = {'dist_git_path': 'rpm/python'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_global_component_with_empty_body(self):
        url = reverse('globalcomponent-list')
        data = {}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_global_component_not_exist(self):
        url = reverse('globalcomponent-detail', kwargs={'pk': 9999})
        data = {'name': 'Updated', 'dist_git_path': 'rpm/python'}
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_global_component_duplicate(self):
        url = reverse('globalcomponent-detail', kwargs={'pk': 1})
        data = {'name': 'MySQL-python'}
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_global_component_only_with_name(self):
        url = reverse('globalcomponent-detail', kwargs={'pk': 1})
        data = {'name': 'OnlyHasName'}
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'OnlyHasName')

    def test_update_global_component_only_with_dist_path(self):
        url = reverse('globalcomponent-detail', kwargs={'pk': 1})
        data = {'dist_git_path': 'rpm/python'}
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_global_component_with_empty_body(self):
        url = reverse('globalcomponent-detail', kwargs={'pk': 1})
        data = {}
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_global_component_without_upstream(self):
        url = reverse('globalcomponent-detail', kwargs={'pk': 3})
        data = {'upstream': {'homepage': 'http://python.org',
                             'scm_type': 'svn', 'scm_url': 'http://svn.python.org/moduleX'}}
        # update by PUT without upstream
        new_data = {'name': 'newName'}
        response = self.client.put(url, new_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['upstream'], data.get('upstream'))
        self.assertNumChanges([1])

    def test_patch_update_global_component(self):
        url = reverse('globalcomponent-detail', kwargs={'pk': 1})
        data = {'dist_git_path': 'rpm/python2'}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['dist_git_path'], 'rpm/python2')
        self.assertNumChanges([1])

    def test_partial_update_empty(self):
        url = reverse('globalcomponent-detail', kwargs={'pk': 1})
        response = self.client.patch(url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_patch_update_global_component_with_upstream(self):
        url = reverse('globalcomponent-detail', kwargs={'pk': 3})
        data = {'upstream': {'homepage': 'http://python.org',
                             'scm_type': 'git', 'scm_url': 'http://git.python.org/moduleX'}}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['upstream'], data.get('upstream'))
        self.assertNumChanges([2])

    def test_query_global_component(self):
        url = reverse('globalcomponent-list')
        url = '%s%s' % (url, '?name=python')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['name'], 'python')

    def test_query_global_component_with_multipl_values(self):
        url = reverse('globalcomponent-list')
        url = '%s%s' % (url, '?name=python&name=MySQL-python')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)
        self.assertEqual(response.data['results'][0]['name'], 'MySQL-python')
        self.assertEqual(response.data['results'][1]['name'], 'python')

    def test_query_global_components_with_upstream(self):
        url = reverse('globalcomponent-list')
        response = self.client.get(url + '?upstream_homepage=http://python.org', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['name'], 'java')
        response = self.client.get(url + '?upstream_scm_type=svn', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['name'], 'java')
        response = self.client.get(url + '?upstream_scm_url=http://svn.python.org/moduleX', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['name'], 'java')


class GlobalComponentContactRESTTestCase(TestCaseWithChangeSetMixin, APITestCase):
    fixtures = [
        "pdc/apps/component/fixtures/tests/upstream.json",
        "pdc/apps/component/fixtures/tests/global_component.json",
        "pdc/apps/contact/fixtures/tests/contact_role.json",
        "pdc/apps/contact/fixtures/tests/maillist.json",
        "pdc/apps/contact/fixtures/tests/person.json",
    ]

    def setUp(self):
        super(GlobalComponentContactRESTTestCase, self).setUp()
        person = Person.objects.get(username='person1')
        person_2 = Person.objects.get(username='person2')
        maillist = Maillist.objects.get(mail_name="maillist2")
        pm_type = ContactRole.objects.get(name='pm')
        qe_type = ContactRole.objects.get(name='qe_ack')

        pm_contact = RoleContact.objects.create(
            contact=person,
            contact_role=pm_type)

        mail_contact = RoleContact.objects.create(
            contact=maillist,
            contact_role=qe_type)

        another_contact = RoleContact.objects.create(
            contact=person,
            contact_role=qe_type)

        pm_contact_2 = RoleContact.objects.create(
            contact=person_2,
            contact_role=pm_type)

        python = models.GlobalComponent.objects.get(name='MySQL-python')
        python.contacts.add(pm_contact, mail_contact)

        self.droplets = [pm_contact, mail_contact, another_contact, pm_contact_2]

    def tearDown(self):
        super(GlobalComponentContactRESTTestCase, self).tearDown()

        python = models.GlobalComponent.objects.get(name='MySQL-python')
        python.contacts.clear()
        for droplet in self.droplets:
            droplet.delete()

    def test_list_global_component_contacts(self):
        url = reverse('globalcomponentcontact-list', kwargs={'instance_pk': 2})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]['contact_role'], 'pm')
        self.assertEqual(response.data[1]['contact_role'], 'qe_ack')

    def test_retrieve_global_component_contacts(self):
        url = reverse('globalcomponentcontact-detail', kwargs={'instance_pk': 2,
                                                               'pk': 1})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['contact_role'], 'pm')
        self.assertEqual(response.data['contact']['username'],
                         'person1')
        self.assertEqual(response.data['contact']['email'],
                         'person1@test.com')

    def test_update_global_component_contact(self):
        url = reverse('globalcomponentcontact-detail', kwargs={'instance_pk': 2,
                                                               'pk': 1})
        response = self.client.put(url, format='json', data={})
        self.assertEqual(response.status_code,
                         status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_delete_global_component_contacts(self):
        url = reverse('globalcomponentcontact-detail', kwargs={'instance_pk': 2,
                                                               'pk': 1})
        response = self.client.delete(url, format='json')
        self.assertEqual(response.status_code,
                         status.HTTP_204_NO_CONTENT)

    def test_create_global_component_contacts(self):
        url = reverse('globalcomponentcontact-list', kwargs={'instance_pk': 2})
        data = {
            "contact_role": "qe_ack",
            "contact": {
                "username": "person1",
                "email": "person1@test.com"
            }
        }
        response = self.client.post(url, format='json', data=data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['contact_role'], 'qe_ack')
        self.assertEqual(response.data['contact']['username'],
                         'person1')
        self.assertEqual(response.data['contact']['email'],
                         'person1@test.com')
        self.assertNumChanges([1])

    def test_create_global_component_contacts_extra_fields(self):
        url = reverse('globalcomponentcontact-list', kwargs={'instance_pk': 2})
        data = {
            "contact_role": "qe_ack",
            "contact": {
                "username": "person1",
                "email": "person1@test.com"
            },
            "foo": "bar",
        }
        response = self.client.post(url, format='json', data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data.get('detail'), 'Unknown fields: "foo".')
        self.assertNumChanges([])

    def test_create_existed_gc_contacts(self):
        url = reverse('globalcomponentcontact-list', kwargs={'instance_pk': 2})
        data = {
            "contact_role": "qe_ack",
            "contact": {
                "username": "person1",
                "email": "person1@test.com"
            }
        }
        response = self.client.post(url, format='json', data=data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response_again = self.client.post(url, format='json', data=data)
        self.assertEqual(response_again.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNumChanges([1])

    def test_create_existed_gc_contacts_in_list(self):
        url = reverse('globalcomponentcontact-list', kwargs={'instance_pk': 2})
        data = {
            "contact_role": "qe_ack",
            "contact": {
                "username": "person1",
                "email": "person1@test.com"
            }
        }
        response = self.client.post(url, format='json', data=data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response_again = self.client.post(url, format='json', data=[data])
        self.assertEqual(response_again.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNumChanges([1])

    def test_create_gc_contacts_with_inexistent_contact(self):
        # PDC-260
        url = reverse('globalcomponentcontact-list', kwargs={'instance_pk': 2})
        data = {
            "contact_role": "new_type",
            "contact": {
                "username": "person3",
                "email": "person3@test.com"
            }
        }
        response = self.client.post(url, format='json', data=data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['contact_role'], 'new_type')
        self.assertEqual(response.data['contact']['username'],
                         'person3')
        self.assertEqual(response.data['contact']['email'],
                         'person3@test.com')
        self.assertNumChanges([4])

    def test_create_multiple_global_component_contacts(self):
        url = reverse('globalcomponentcontact-list', kwargs={'instance_pk': 2})
        data = [{
            "contact_role": "qe_ack",
            "contact": {
                "username": "person1",
                "email": "person1@test.com"
            }
        }, {
            "contact_role": "pm",
            "contact": {
                "mail_name": "maillist2",
                "email": "maillist2@test.com"
            }
        }]
        response = self.client.post(url, format='json', data=data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data[0]['contact_role'], 'qe_ack')
        self.assertEqual(response.data[0]['contact']['username'],
                         'person1')
        self.assertEqual(response.data[0]['contact']['email'],
                         'person1@test.com')
        self.assertEqual(response.data[1]['contact_role'], 'pm')
        self.assertEqual(response.data[1]['contact']['mail_name'],
                         'maillist2')
        self.assertEqual(response.data[1]['contact']['email'],
                         'maillist2@test.com')
        self.assertNumChanges([3])

    def test_query_global_component_contacts(self):
        url = reverse('globalcomponentcontact-list', kwargs={'instance_pk': 2})
        url = '%s%s' % (url, '?contact_role=pm')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['contact_role'], 'pm')
        self.assertEqual(response.data[0]['contact']['username'], 'person1')
        self.assertEqual(response.data[0]['contact']['email'], 'person1@test.com')

    def test_query_with_multiple_values(self):
        url = reverse('globalcomponentcontact-list', kwargs={'instance_pk': 2})
        url = '%s%s' % (url, '?contact_role=pm&contact_role=qe_ack')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_query_with_more_keys(self):
        url = reverse('globalcomponentcontact-list', kwargs={'instance_pk': 2})
        url = '%s%s' % (url, '?contact_role=pm&username=person1')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)


class GlobalComponentLabelRESTTestCase(TestCaseWithChangeSetMixin, APITestCase):
    fixtures = [
        "pdc/apps/component/fixtures/tests/upstream.json",
        "pdc/apps/component/fixtures/tests/global_component.json"
    ]

    def setUp(self):
        super(GlobalComponentLabelRESTTestCase, self).setUp()
        self.args_label1 = {'name': 'label1', 'description': 'label1 description'}
        self.args_label2 = {'name': 'label2', 'description': 'label2 description'}
        self.args_label3 = {'name': 'label3', 'description': 'label3 description'}
        self.label1 = models.Label.objects.create(**self.args_label1)
        self.label2 = models.Label.objects.create(**self.args_label2)
        self.label3 = models.Label.objects.create(**self.args_label3)
        python = models.GlobalComponent.objects.get(name='python')
        python.labels.add(self.label1)

    def test_list_specified_global_component_labels(self):
        url = reverse('globalcomponentlabel-list', kwargs={'instance_pk': 1})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 1)
        self.assertEqual(response.data.get('results')[0].get('name'), self.args_label1.get('name'))
        self.assertEqual(response.data.get('results')[0].get('description'), self.args_label1.get('description'))

    def test_retrieve_specified_global_component_label(self):
        url = reverse('globalcomponentlabel-detail', kwargs={'instance_pk': 1, 'pk': 1})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('name'), self.args_label1.get('name'))
        self.assertEqual(response.data.get('description'), self.args_label1.get('description'))

    def test_add_label_for_specified_global_component(self):
        url = reverse('globalcomponentlabel-list', kwargs={'instance_pk': 1})
        response = self.client.post(url, format='json', data=self.args_label2)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data.get('name'), self.args_label2['name'])
        self.assertEqual(response.data.get('description'), self.args_label2['description'])
        response = self.client.get(url, format='json')
        self.assertEqual(response.data.get('count'), 2)
        self.assertEqual(response.data.get('results')[0].get('name'), self.args_label1.get('name'))
        self.assertEqual(response.data.get('results')[0].get('description'), self.args_label1.get('description'))
        self.assertEqual(response.data.get('results')[1].get('name'), self.args_label2.get('name'))
        self.assertEqual(response.data.get('results')[1].get('description'), self.args_label2.get('description'))
        self.assertNumChanges([1])

    def test_add_label_for_specified_global_component_extra_field(self):
        url = reverse('globalcomponentlabel-list', kwargs={'instance_pk': 1})
        self.args_label2['foo'] = 'bar'
        response = self.client.post(url, format='json', data=self.args_label2)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data.get('detail'), 'Unknown fields: "foo".')
        self.assertNumChanges([])

    def test_add_none_existing_label(self):
        url = reverse('globalcomponentlabel-list', kwargs={'instance_pk': 1})
        response = self.client.post(url, format='json', data={'name': 'none existing label'})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_label_from_specified_global_component(self):
        url_list = reverse('globalcomponentlabel-list', kwargs={'instance_pk': 1})
        url_retrieve = reverse('globalcomponentlabel-detail', kwargs={'instance_pk': 1, 'pk': 1})
        response = self.client.get(url_list, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 1)
        response = self.client.delete(url_retrieve, format='json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        response = self.client.get(url_list, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 0)
        self.assertNumChanges([1])

    def test_query_specified_label_with_name(self):
        url = reverse('globalcomponentlabel-list', kwargs={'instance_pk': 1})
        url = '%s%s' % (url, '?name=label1')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('results')[0].get('name'), self.args_label1.get('name'))
        self.assertEqual(response.data.get('results')[0].get('description'), self.args_label1.get('description'))

    def test_query_global_components_with_specified_label(self):
        mysql = models.GlobalComponent.objects.get(name='MySQL-python')
        mysql.labels.add(self.label1)
        url = reverse('globalcomponent-list') + '?label=label1'
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 2)
        self.assertEqual(response.data.get('results')[0].get('name'), 'python')
        self.assertEqual(response.data.get('results')[1].get('name'), 'MySQL-python')

    def test_bulk_create_global_component_labels(self):
        url = reverse('globalcomponentlabel-list', kwargs={'instance_pk': 1})
        response = self.client.post(url, format='json', data=[self.args_label2, self.args_label3])
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data[0].get('name'), self.args_label2['name'])
        self.assertEqual(response.data[0].get('description'), self.args_label2['description'])
        self.assertEqual(response.data[1].get('name'), self.args_label3['name'])
        self.assertEqual(response.data[1].get('description'), self.args_label3['description'])
        response = self.client.get(url, format='json')
        self.assertEqual(response.data.get('count'), 3)
        self.assertNumChanges([2])


class ReleaseComponentModelTestCase(unittest.TestCase):

    def test_get_inherited_dist_git_branch_from_release(self):
        mock_rc = mock.Mock(spec=models.ReleaseComponent)
        mock_rc.dist_git_branch = None
        mock_rc.release.dist_git_branch = 'release_branch'

        branch = models.ReleaseComponent._get_inherited_dist_git_branch(mock_rc)
        self.assertEqual(branch, 'release_branch')

    def test_get_inherited_dist_git_branch_from_self(self):
        mock_rc = mock.Mock(spec=models.ReleaseComponent)
        mock_rc.dist_git_branch = 'self_branch'
        mock_rc.release.dist_git_branch = 'release_branch'

        branch = models.ReleaseComponent._get_inherited_dist_git_branch(mock_rc)
        self.assertEqual(branch, 'self_branch')

    def test_dist_git_web_url_with_inherited_dist_git_branch(self):
        repo_url = 'http://globalcomponent'
        mock_rc = mock.Mock(spec=models.ReleaseComponent)
        mock_rc.global_component.dist_git_web_url = repo_url
        mock_rc.inherited_dist_git_branch = 'master'

        type(mock_rc).dist_git_web_url = models.ReleaseComponent.dist_git_web_url

        self.assertEqual(mock_rc.dist_git_web_url, '%s?h=%s' % (repo_url, 'master'))

    def test_dist_git_web_url_without_inherited_dist_git_branch(self):
        repo_url = 'http://globalcomponent'
        mock_rc = mock.Mock(spec=models.ReleaseComponent)
        mock_rc.global_component.dist_git_web_url = repo_url
        mock_rc.inherited_dist_git_branch = None

        type(mock_rc).dist_git_web_url = models.ReleaseComponent.dist_git_web_url

        self.assertEqual(mock_rc.dist_git_web_url, repo_url)


class ReleaseComponentRESTTestCase(TestCaseWithChangeSetMixin, APITestCase):

    fixtures = [
        "pdc/apps/release/fixtures/release_type.json",
        "pdc/apps/release/fixtures/tests/release.json",
        "pdc/apps/release/fixtures/tests/product.json",
        "pdc/apps/component/fixtures/tests/upstream.json",
        "pdc/apps/component/fixtures/tests/global_component.json",
        "pdc/apps/component/fixtures/tests/release_component.json",
        "pdc/apps/contact/fixtures/tests/contact_role.json",
        "pdc/apps/contact/fixtures/tests/maillist.json",
        "pdc/apps/contact/fixtures/tests/person.json",
        "pdc/apps/bindings/fixtures/tests/releasedistgitmapping.json"
    ]

    def setUp(self):
        super(ReleaseComponentRESTTestCase, self).setUp()
        # Initialize release_component contact
        person = Person.objects.get(username='person1')
        person_2 = Person.objects.get(username='person2')
        maillist = Maillist.objects.get(mail_name="maillist2")
        pm_type = ContactRole.objects.get(name='pm')
        qe_type = ContactRole.objects.get(name='qe_ack')

        pm_contact = RoleContact.objects.create(
            contact=person,
            contact_role=pm_type)

        mail_contact = RoleContact.objects.create(
            contact=maillist,
            contact_role=qe_type)

        RoleContact.objects.create(
            contact=person_2,
            contact_role=pm_type)

        RoleContact.objects.create(
            contact=person_2,
            contact_role=qe_type)

        gc_python = models.GlobalComponent.objects.get(name='python')
        gc_python.contacts.add(pm_contact, mail_contact)

        rc_python27 = models.ReleaseComponent.objects.get(name='python27')
        # Initialize release component contact
        base_name = 'foo'
        for i in range(2):
            contact = RoleContact.specific_objects.create(
                username=base_name + str(i),
                email=base_name + str(i) + '@example.com',
                contact_role='QE_Group')
            rc_python27.contacts.add(contact)

        # Append a new contact with a new contact_role
        contact = RoleContact.specific_objects.create(
            username='new',
            email=base_name + '@example.com',
            contact_role='type_xx')
        rc_python27.contacts.add(contact)

        # Create an inactive release as well as a release component on top of it.
        pv = ProductVersion.objects.create(
            name='Our Awesome Product',
            short='release',
            version='0',
            product_id=1,
            product_version_id="release-0",
        )
        self.rhel5_inactive = Release.objects.create(
            release_id='release-0.0',
            short='release',
            version='0.0',
            name='Our Awesome Product',
            release_type_id=1,
            active=False,
            product_version_id=pv.pk,
        )
        models.ReleaseComponent.objects.create(
            release=self.rhel5_inactive,
            # global component 'python'
            global_component_id=1,
            name='python24',
        )
        rc_bz = models.ReleaseComponent.objects.get(name='python27')
        bugzilla_component = models.BugzillaComponent.objects.create(name='python27')
        lib = models.BugzillaComponent.objects.create(name='lib', parent_component=bugzilla_component)
        models.BugzillaComponent.objects.create(name='xml', parent_component=lib)
        pyth = models.BugzillaComponent.objects.create(name='python', parent_component=bugzilla_component)
        models.BugzillaComponent.objects.create(name='bin', parent_component=pyth)
        rc_bz.bugzilla_component = bugzilla_component
        rc_bz.save()

    def test_list_active_release_component(self):
        url = reverse('releasecomponent-list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)
        names = list(d['name'] for d in response.data['results'])
        self.assertTrue('python27' in names)
        self.assertTrue('MySQL-python' in names)
        self.assertTrue('python24' not in names)

    def test_list_all_release_component(self):
        url = reverse('releasecomponent-list')
        url += '?include_inactive_release'
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 3)
        names = list(d['name'] for d in response.data['results'])
        self.assertTrue('python27' in names)
        self.assertTrue('MySQL-python' in names)
        self.assertTrue('python24' in names)

    def test_list_release_component_include_field(self):
        url = reverse('releasecomponent-list')
        response = self.client.get(url + '?fields=name', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(['name'], response.data['results'][0].keys())

    def test_detail_release_component_exclude_contacts_fields(self):
        url = reverse('releasecomponent-list')
        response = self.client.get(url + '?exclude_fields=contacts', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn('contacts', response.data)

    def test_filter_release_component_with_params(self):
        url = reverse('releasecomponent-list')
        # Query with specific contact_role,
        # contact_role and email have to be provided together, otherwise the filter will not make sense,
        # but filter out all release_component
        data = {'contact_role': 'pm'}
        response = self.client.get(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)

        # Query both contact_role and email.
        data = {'contact_role': 'QE_Group', 'email': 'foo1@example.com'}
        response = self.client.get(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    def test_filter_release_component_with_brew_package(self):
        self.test_create_release_component()
        url = reverse('releasecomponent-list')
        data = {'brew_package': 'python-pdc'}
        response = self.client.get(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data.get('results')[0].get('name'), 'python26')

    def test_filter_release_component_by_srpm_name(self):
        url = reverse('releasecomponent-list')
        data = {'release': 'release-1.0', 'global_component': 'python',
                'name': 'python26', 'brew_package': 'python-pdc',
                "srpm": {"name": "test"}}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response = self.client.get(url + '?srpm_name=test', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    def test_filter_release_component_by_active(self):
        url = reverse('releasecomponent-list')
        response = self.client.get(url + '?active=True', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)
        response = self.client.get(url + '?active=true', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)
        response = self.client.get(url + '?active=t', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)
        response = self.client.get(url + '?active=1', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)

    def test_filter_fields_not_affect_bugzilla_component(self):
        url = reverse('releasecomponent-list')
        response = self.client.get(url + '?fields=bugzilla_component', format='json')
        self.assertGreater(response.data['results'][0]['bugzilla_component'], 1)

    def test_filter_release_component_by_inactive(self):
        url = reverse('releasecomponent-list')
        response = self.client.get(url + '?active=False', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 0)
        response = self.client.get(url + '?active=false', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 0)
        response = self.client.get(url + '?active=f', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 0)
        response = self.client.get(url + '?active=0', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 0)

    def test_filter_release_component_by_wrong_active(self):
        url = reverse('releasecomponent-list')
        response = self.client.get(url + '?active=abc', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 0)

    def test_detail_release_component(self):
        url = reverse('releasecomponent-detail', kwargs={'pk': 1})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'python27')
        self.assertEqual(response.data['dist_git_branch'], 'release_branch')

    def test_release_component_contacts_url(self):
        url = reverse('releasecomponentcontact-list', kwargs={'instance_pk': 1})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 5)
        self.assertContains(response, 'release-components', 3)
        self.assertContains(response, 'global-components', 2)

    def test_detail_release_component_not_exist(self):
        url = reverse('releasecomponent-detail', kwargs={'pk': 9999})
        response = self.client.get(url, format='json')
        data = {'detail': 'Not found.'}
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data, data)

    def test_create_release_component(self):
        url = reverse('releasecomponent-list')
        data = {'release': 'release-1.0', 'global_component': 'python', 'name': 'python26', 'brew_package': 'python-pdc'}
        response = self.client.post(url, data, format='json')
        del response.data['dist_git_web_url']
        del response.data['srpm']
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data.update({'contacts': [], 'dist_git_branch': "release_branch", 'id': 3,
                     'bugzilla_component': None, 'active': True, 'type': None})
        self.assertEqual(sorted(response.data), sorted(data))
        self.assertNumChanges([1])

    def test_create_release_component_for_non_existing_release(self):
        url = reverse('releasecomponent-list')
        data = {'release': 'hello-1.0',
                'global_component': 'python',
                'name': 'python26',
                'brew_package': 'python-pdc'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'release': ['Object with release_id=hello-1.0 does not exist.']})
        self.assertNumChanges([])

    def test_create_release_component_with_type(self):
        url = reverse('releasecomponent-list')
        data = {'release': 'release-1.0', 'global_component': 'python', 'name': 'python26',
                'brew_package': 'python-pdc', 'type': 'rpm'}
        response = self.client.post(url, data, format='json')
        del response.data['dist_git_web_url']
        del response.data['srpm']
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data.update({'contacts': [], 'dist_git_branch': "release_branch", 'id': 3,
                     'bugzilla_component': None, 'active': True, 'type': 'rpm'})
        self.assertEqual(sorted(response.data), sorted(data))
        self.assertNumChanges([1])

    def test_create_with_srpm(self):
        url = reverse('releasecomponent-list')
        data = {'release': 'release-1.0', 'global_component': 'python',
                'name': 'python26', 'brew_package': 'python-pdc',
                'srpm': {'name': 'test'}}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data.get('srpm').get('name'), 'test')
        self.assertNumChanges([2])

    def test_create_with_null_srpm(self):
        url = reverse('releasecomponent-list')
        data = {'release': 'release-1.0', 'global_component': 'python',
                'name': 'python26', 'brew_package': 'python-pdc',
                'srpm': None}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data.get('srpm'), None)
        self.assertNumChanges([1])

    def test_create_release_component_extra_fields(self):
        url = reverse('releasecomponent-list')
        data = {'release': 'release-1.0', 'global_component': 'python',
                'name': 'python26', 'brew_package': 'python-pdc', 'foo': 'bar'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data.get('detail'), 'Unknown fields: "foo".')
        self.assertNumChanges([])

    def test_create_release_component_with_customize_output(self):
        url = reverse('releasecomponent-list')
        data = {'release': 'release-1.0', 'global_component': 'python', 'name': 'python26', 'brew_package': 'python-pdc'}
        response = self.client.post(url + "?fields=name", data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_release_component_with_bugzillacomponent(self):
        pyth = models.BugzillaComponent.objects.create(name='python')
        models.BugzillaComponent.objects.create(name='python_pdc', parent_component=pyth)
        url = reverse('releasecomponent-list')
        data = {'release': 'release-1.0', 'global_component': 'python', 'name': 'python26', 'brew_package': 'python', 'bugzilla_component': 'python'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        url1 = reverse('releasecomponent-list')
        data1 = {'release': 'release-1.0', 'global_component': 'python', 'name': 'python26-pdc', 'brew_package': 'python-pdc', 'bugzilla_component': 'python/python_pdc'}
        response1 = self.client.post(url1, data1, format='json')
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)
        self.assertNumChanges([1, 1])

    def test_create_release_component_with_wrong_bugzillacomponent(self):
        url = reverse('releasecomponent-list')
        data = {'release': 'release-1.0', 'global_component': 'python', 'name': 'python26', 'brew_package': 'python-pdc', 'bugzilla_component': 'python26/python/python_pdc'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_release_component_with_bugzillacomponent_noexist(self):
        url = reverse('releasecomponent-list')
        data = {'release': 'release-1.0', 'global_component': 'python', 'name': 'python26', 'brew_package': 'python-pdc', 'bugzilla_component': 'foooo'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_release_component_with_duplicate_bugzillacomponent(self):
        # If only bare bugzilla_component is given, the bugzilla_component which parent_component is null will be selected.
        misc = models.BugzillaComponent.objects.create(name='misc')
        models.BugzillaComponent.objects.create(name='other', parent_component=misc)
        filesystem = models.BugzillaComponent.objects.create(name='filesystem')
        models.BugzillaComponent.objects.create(name='misc', parent_component=filesystem)
        url = reverse('releasecomponent-list')
        data = {'release': 'release-1.0', 'global_component': 'python', 'name': 'python26', 'brew_package': 'python-pdc', 'bugzilla_component': 'misc'}
        response = self.client.post(url, data, format='json')
        self.assertIsNone(response.data['bugzilla_component']['parent_component'])

    def test_create_release_component_duplicate(self):
        url = reverse('releasecomponent-list')
        data = {'release': 'release-1.0', 'global_component': 'python', 'name': 'python27', 'bugzilla_component': 'python27'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_release_component_only_with_name(self):
        url = reverse('releasecomponent-list')
        data = {'name': 'Name'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_release_component_only_with_dist_git_branch(self):
        url = reverse('releasecomponent-list')
        data = {'name': 'rpm/python'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_release_component_with_empty_body(self):
        url = reverse('releasecomponent-list')
        data = {}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_release_component(self):
        url = reverse('releasecomponent-detail', kwargs={'pk': 1})
        data = {'name': 'python26'}
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        del response.data['dist_git_web_url']
        del response.data['dist_git_branch']
        del response.data['contacts']
        del response.data['srpm']
        del response.data['id']
        del response.data['bugzilla_component']
        del response.data['brew_package']
        del response.data['type']
        del response.data['release']
        del response.data['global_component']
        data.update({'active': True})
        self.assertEqual(response.data, data)
        self.assertNumChanges([1])

    def test_update_release_component_extra_fields(self):
        url = reverse('releasecomponent-detail', kwargs={'pk': 1})
        data = {'name': 'python26', 'foo': 'bar'}
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data.get('detail'), 'Unknown fields: "foo".')
        self.assertNumChanges([])

    def test_update_specified_release_component_brew_package(self):
        url = reverse('releasecomponent-detail', kwargs={'pk': 1})
        response = self.client.get(url, format='json')
        old_data = response.data
        data = {'brew_package': 'python-pdc'}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        old_data.update({'brew_package': 'python-pdc'})
        self.assertEqual(old_data, response.data)

    def test_partial_update_empty(self):
        url = reverse('releasecomponent-detail', kwargs={'pk': 1})
        response = self.client.patch(url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_release_component_not_existed(self):
        url = reverse('releasecomponent-detail', kwargs={'pk': 9999})
        data = {'name': 'python27'}
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_release_component_name_existed(self):
        url = reverse('releasecomponent-detail', kwargs={'pk': 1})
        data = {'name': 'MySQL-python'}
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_release_component_only_with_name(self):
        url = reverse('releasecomponent-detail', kwargs={'pk': 1})
        data = {'name': 'python30'}
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'python30')
        self.assertNumChanges([1])

    def test_update_release_component_with_dist_git_branch(self):
        url = reverse('releasecomponent-detail', kwargs={'pk': 1})
        data = {'name': 'python27', 'dist_git_branch': 'rpm/python2'}
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['dist_git_branch'], 'rpm/python2')
        self.assertNumChanges([1])

    def test_update_release_component_only_with_empty_body(self):
        url = reverse('releasecomponent-detail', kwargs={'pk': 1})
        data = {}
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_active_release_component(self):
        url = reverse('releasecomponent-list')
        data = {'release': 'release-1.0', 'global_component': 'python', 'name': 'python34', 'brew_package': 'python-pdc', 'active': 'True'}
        response = self.client.post(url, data, format='json')
        del response.data['dist_git_web_url']
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data.update({'contacts': [], 'dist_git_branch': "release_branch", 'id': 3,
                     'bugzilla_component': None, 'srpm': None, 'active': True, 'type': None})
        self.assertEqual(sorted(response.data), sorted(data))
        self.assertNumChanges([1])

        url = reverse('releasecomponent-list')
        data = {'release': 'release-1.0', 'global_component': 'python', 'name': 'python33', 'brew_package': 'python-pdc'}
        response = self.client.post(url, data, format='json')
        del response.data['dist_git_web_url']
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data.update({'contacts': [], 'dist_git_branch': "release_branch", 'id': 3,
                     'bugzilla_component': None, 'srpm': None, 'active': True, 'type': None})
        self.assertEqual(sorted(response.data), sorted(data))
        self.assertNumChanges([1, 1])

    def test_create_inactive_release_component(self):
        url = reverse('releasecomponent-list')
        data = {'release': 'release-1.0', 'global_component': 'python', 'name': 'python35', 'brew_package': 'python-pdc', 'active': 'False'}
        response = self.client.post(url, data, format='json')
        del response.data['dist_git_web_url']
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data.update({'contacts': [], 'dist_git_branch': "release_branch", 'id': 3,
                     'bugzilla_component': None, 'srpm': None, 'active': False, 'type': None})
        self.assertEqual(sorted(response.data), sorted(data))
        self.assertNumChanges([1])

    def test_patch_update_release_component(self):
        url = reverse('releasecomponent-detail', kwargs={'pk': 1})
        data = {'dist_git_branch': 'rpm/python2'}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['dist_git_branch'], 'rpm/python2')
        self.assertNumChanges([1])

    def test_update_release_component_with_bugzilla_component(self):
        url = reverse('releasecomponent-detail', kwargs={'pk': 2})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        pyth = models.BugzillaComponent.objects.create(name='python')
        data = {'name': 'MySQL-python', 'bugzilla_component': 'python'}
        response1 = self.client.put(url, data, format='json')
        self.assertEqual(response1.data['bugzilla_component']['name'], 'python')

        python_lib = models.BugzillaComponent.objects.create(name='lib', parent_component=pyth)
        python_lib64 = models.BugzillaComponent.objects.create(name='lib64', parent_component=python_lib)
        models.BugzillaComponent.objects.create(name='etc', parent_component=python_lib64)
        data2 = {'name': 'MySQL-python-lib', 'bugzilla_component': '/python/lib/lib64/etc/'}
        response2 = self.client.put(url, data2, format='json')
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        self.assertEqual(response2.data['bugzilla_component']['name'], 'etc')
        self.assertEqual(response2.data['bugzilla_component']['parent_component'], 'lib64')
        self.assertNumChanges([1, 1])

    def test_update_release_component_with_bugzilla_component_same_name(self):
        url = reverse('releasecomponent-detail', kwargs={'pk': 2})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        pyth1 = models.BugzillaComponent.objects.create(name='python')
        data1 = {'name': 'MySQL-python', 'bugzilla_component': 'python'}
        response1 = self.client.put(url, data1, format='json')
        self.assertEqual(response1.data['bugzilla_component']['name'], 'python')

        models.BugzillaComponent.objects.create(name='python', parent_component=pyth1)
        data2 = {'name': 'MySQL-python', 'bugzilla_component': 'python/python'}
        response2 = self.client.put(url, data2, format='json')
        # The 2 bugzilla_component have same name but changeset should record the change
        self.assertEqual(response2.data['bugzilla_component']['name'], 'python')
        self.assertNumChanges([1, 1])

    def test_update_release_component_with_null_bugzilla_component(self):
        models.BugzillaComponent.objects.create(name='python')
        url = reverse('releasecomponent-list')
        data = {'release': 'release-1.0', 'global_component': 'python', 'name': 'python26', 'brew_package': 'python', 'bugzilla_component': 'python'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        url1 = reverse('releasecomponent-detail', kwargs={'pk': 4})
        data1 = {'bugzilla_component': None}
        response1 = self.client.patch(url1, data1, format='json')
        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        self.assertIsNone(response1.data['bugzilla_component'])
        self.assertNumChanges([1, 1])

    def test_update_release_component_with_valid_type(self):
        url = reverse('releasecomponent-detail', kwargs={'pk': 2})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = {'name': 'MySQL-python', 'type': 'zip'}
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.data['type'], 'zip')

        data = {'name': 'MySQL-python', 'type': 'rpm'}
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.data['type'], 'rpm')
        self.assertNumChanges([1, 1])

    def test_update_release_component_with_invalid_type(self):
        url = reverse('releasecomponent-detail', kwargs={'pk': 2})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = {'name': 'python27', 'type': 'fake_type'}
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_release_component_with_wrong_bugzilla_component(self):
        url = reverse('releasecomponent-detail', kwargs={'pk': 2})
        pyth = models.BugzillaComponent.objects.create(name='python')
        models.BugzillaComponent.objects.create(name='lib', parent_component=pyth)
        data = {'name': 'MySQL-python-lib', 'bugzilla_component': 'python26/python/lib'}
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_release_component_with_bugzillacomponent_noexist(self):
        url = reverse('releasecomponent-detail', kwargs={'pk': 2})
        data = {'name': 'noexist', 'bugzilla_component': 'foo'}
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_patch_update_release_component_with_bugzilla_component(self):
        url = reverse('releasecomponent-detail', kwargs={'pk': 2})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        pyth = models.BugzillaComponent.objects.create(name='python')
        data = {'bugzilla_component': 'python'}
        response1 = self.client.patch(url, data, format='json')
        self.assertEqual(response1.data['bugzilla_component']['name'], 'python')

        models.BugzillaComponent.objects.create(name='lib', parent_component=pyth)
        data2 = {'bugzilla_component': 'python/lib'}
        response2 = self.client.patch(url, data2, format='json')
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        self.assertEqual(response2.data['bugzilla_component']['name'], 'lib')
        self.assertEqual(response2.data['bugzilla_component']['parent_component'], 'python')
        self.assertNumChanges([1, 1])

    def test_update_release_component_with_duplicate_bugzilla_component(self):
        # If only bare bugzilla_component is given, the bugzilla_component which parent_component is null will be selected.
        misc = models.BugzillaComponent.objects.create(name='misc')
        models.BugzillaComponent.objects.create(name='other', parent_component=misc)
        filesystem = models.BugzillaComponent.objects.create(name='filesystem')
        models.BugzillaComponent.objects.create(name='misc', parent_component=filesystem)
        url = reverse('releasecomponent-detail', kwargs={'pk': 2})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = {'name': 'MySQL-python', 'bugzilla_component': 'misc'}
        response1 = self.client.put(url, data, format='json')
        self.assertEqual(response1.data['bugzilla_component']['name'], 'misc')
        self.assertIsNone(response1.data['bugzilla_component']['parent_component'])
        self.assertNumChanges([1])

    def test_update_with_patch_add_srpm(self):
        url = reverse('releasecomponent-detail', kwargs={'pk': 1})
        data = {'srpm': {'name': 'srpm'}}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['srpm']['name'], 'srpm')
        self.assertNumChanges([1])

    def test_update_with_patch_srpm(self):
        rc = models.ReleaseComponent.objects.get(id=1)
        from pdc.apps.bindings import models as bingding_models
        bingding_models.ReleaseComponentSRPMNameMapping.objects.create(srpm_name='srpm',
                                                                       release_component=rc)
        self.assertEqual(bingding_models.ReleaseComponentSRPMNameMapping.objects.count(), 1)
        url = reverse('releasecomponent-detail', kwargs={'pk': 1})
        data = {'srpm': {'name': 'new_srpm'}}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['srpm'], {'name': 'new_srpm'})
        self.assertEqual(bingding_models.ReleaseComponentSRPMNameMapping.objects.count(), 1)
        self.assertNumChanges([1])

    def test_update_with_patch_null_srpm_name(self):
        url = reverse('releasecomponent-detail', kwargs={'pk': 1})
        data = {'srpm': {'name': 'srpm'}}
        from pdc.apps.bindings import models as bingding_models
        response = self.client.patch(url, data, format='json')
        count = bingding_models.ReleaseComponentSRPMNameMapping.objects.count()
        self.assertEqual(count, 1)
        data = {'srpm': {'name': None}}
        response = self.client.patch(url, data, format='json')
        count = bingding_models.ReleaseComponentSRPMNameMapping.objects.count()
        self.assertEqual(count, 0)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['srpm'], None)
        self.assertNumChanges([1, 1])

    def test_update_with_patch_null_srpm(self):
        url = reverse('releasecomponent-detail', kwargs={'pk': 1})
        data = {'srpm': None}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['srpm'], None)
        self.assertNumChanges([])

    def test_update_with_patch_srpm_to_null(self):
        rc = models.ReleaseComponent.objects.get(id=1)
        from pdc.apps.bindings import models as bingding_models
        bingding_models.ReleaseComponentSRPMNameMapping.objects.create(srpm_name='srpm',
                                                                       release_component=rc)
        self.assertEqual(bingding_models.ReleaseComponentSRPMNameMapping.objects.count(), 1)
        url = reverse('releasecomponent-detail', kwargs={'pk': 1})
        data = {'srpm': None}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['srpm'], None)
        self.assertEqual(bingding_models.ReleaseComponentSRPMNameMapping.objects.count(), 0)
        self.assertNumChanges([1])

    def test_update_with_patch_wrong_format_srpm(self):
        url = reverse('releasecomponent-detail', kwargs={'pk': 1})
        data = {'srpm': 'name'}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNumChanges([])

    def test_update_with_patch_wrong_dict_format_srpm(self):
        url = reverse('releasecomponent-detail', kwargs={'pk': 1})
        data = {'srpm': {'srpm_name': 'srpm'}}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNumChanges([])

    def test_update_with_put_srpm(self):
        url = reverse('releasecomponent-detail', kwargs={'pk': 1})
        data = {'srpm': {'name': 'srpm'}}
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {"name": ["This field is required."]})
        self.assertNumChanges([])

    def test_get_release_component_contact(self):
        url = reverse('releasecomponentcontact-list', kwargs={'instance_pk': 1})
        data = {}
        response = self.client.get(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('http://testserver/rest_api/v1/global-components/1/contacts/1/', response.content)
        self.assertEqual(len(response.data), 5)

    def test_get_single_release_component_contact(self):
        url = reverse('releasecomponentcontact-detail', kwargs={'instance_pk': 1, 'pk': 5})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_assign_label_to_global_component_without_name(self):
        url = reverse('globalcomponentlabel-list', kwargs={'instance_pk': 1})
        response = self.client.post(url, format='json', data={})
        self.assertEqual(response.data, {'name': ['This field is required.']})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_add_release_component_contact(self):
        url = reverse('releasecomponentcontact-list', kwargs={'instance_pk': 2})
        data = {
            "contact_role": "QE_Group",
            "contact": {
                'username': 'foo1',
                'email': 'foo1@example.com',
            }
        }
        response = self.client.post(url, data, format='json')
        response_new = self.client.get(url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response_new.status_code, status.HTTP_200_OK)
        self.assertIn(response.data, response_new.data)
        # PDC-288
        self.assertNumChanges([1])

    def test_add_release_component_contact_extra_fields(self):
        url = reverse('releasecomponentcontact-list', kwargs={'instance_pk': 2})
        data = {
            "contact_role": "QE_Group",
            "contact": {
                'username': 'foo1',
                'email': 'foo1@example.com',
            },
            'foo': 'bar'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data.get('detail'), 'Unknown fields: "foo".')
        self.assertNumChanges([])

    def test_add_existed_release_component_contact(self):
        # PDC-272
        url = reverse('releasecomponentcontact-list', kwargs={'instance_pk': 2})
        data = {
            "contact_role": "QE_Group",
            "contact": {
                'username': 'foo1',
                'email': 'foo1@example.com',
            }
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response_again = self.client.post(url, data, format='json')
        self.assertEqual(response_again.status_code, status.HTTP_400_BAD_REQUEST)

    def test_add_rc_contact_with_inexistent_contact(self):
        # PDC-272
        url = reverse('releasecomponentcontact-list', kwargs={'instance_pk': 2})
        data = {
            "contact_role": "new_type",
            "contact": {
                'username': 'foo1',
                'email': 'foo1@example.com',
            }
        }
        response = self.client.post(url, data, format='json')
        response_new = self.client.get(url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response_new.status_code, status.HTTP_200_OK)
        self.assertIn(response.data, response_new.data)
        # 3 = new_type + new_rolecontact + new_rc_contact
        self.assertNumChanges([3])

    def test_filter_release_component_contact(self):
        url = reverse('releasecomponentcontact-list', kwargs={'instance_pk': 1})
        data = {}
        qe_group_url = url + "?contact_role=QE_Group"
        response_new = self.client.get(qe_group_url, data, format='json')
        self.assertEqual(response_new.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_new.data), 2)

    def test_filter_release_component_inherited_contact(self):
        url = reverse('releasecomponentcontact-list', kwargs={'instance_pk': 1})
        data = {}
        response = self.client.get(url, data, format='json')
        qe_group_url = url + "?contact_role=qe_ack"
        response_filtered = self.client.get(qe_group_url, data, format='json')
        self.assertEqual(response_filtered.status_code, status.HTTP_200_OK)
        self.assertIn(response_filtered.data[0], response.data)
        self.assertEqual(len(response_filtered.data), 1)
        contact_qe_ack = response_filtered.data[0]
        self.assertTrue('inherited' in contact_qe_ack)
        self.assertTrue(contact_qe_ack.get('inherited'))

    def test_filter_release_component_by_email_contact_role(self):
        url = reverse('releasecomponent-list')
        data = {}
        qe_group_url = url + "?email=foo1@example.com&contact_role=QE_Group"
        response_new = self.client.get(qe_group_url, data, format='json')
        self.assertEqual(response_new.status_code, status.HTTP_200_OK)
        self.assertEqual(response_new.data['count'], 1)
        self.assertEqual(len(response_new.data['results'][0]['contacts']), 5)

    def test_filter_release_component_by_bugzillacomponent(self):
        url = reverse('releasecomponent-list')
        bugzilla_component_url = url + "?bugzilla_component=python27"
        response_new = self.client.get(bugzilla_component_url, format='json')
        self.assertEqual(response_new.status_code, status.HTTP_200_OK)
        self.assertEqual(response_new.data['count'], 1)

    def test_same_contact_role_exist_in_both(self):
        url = reverse('releasecomponentcontact-list', kwargs={'instance_pk': 1})
        data = {}
        response = self.client.get(url, data, format='json')
        gc_contact_pm = response.data[3]

        # Add a new contact whose contact_role is same as one of global_component
        contact = RoleContact.specific_objects.create(
            username='release_component',
            email='release@example.com',
            contact_role='pm')
        models.ReleaseComponent.objects.get(pk=1).contacts.add(contact)
        response = self.client.get(url, data, format='json')
        rc_contact_pm = response.data[3]

        self.assertNotIn(gc_contact_pm, response.data)
        self.assertIn(rc_contact_pm, response.data)

    def test_release_component_with_overwrite_email(self):
        url = reverse('releasecomponent-list')
        contact = RoleContact.specific_objects.create(
            username='release_component',
            email='release@example.com',
            contact_role='pm')
        models.ReleaseComponent.objects.get(pk=1).contacts.add(contact)
        response = self.client.get(url, {'email': 'person1@test.com'}, format='json')
        self.assertEqual(response.data['count'], 0)

    def test_release_component_with_multiple_overwrite(self):
        url = reverse('releasecomponent-list')
        contact = RoleContact.specific_objects.create(
            username='release_component',
            email='release@example.com',
            contact_role='pm')
        models.ReleaseComponent.objects.get(pk=1).contacts.add(contact)
        contact = RoleContact.specific_objects.create(
            username='gc_person_1',
            email='person1@test.com',
            contact_role='type_YYY')
        models.GlobalComponent.objects.get(pk=1).contacts.add(contact)
        response = self.client.get(url, {'email': 'person1@test.com'}, format='json')
        self.assertEqual(response.data['count'], 1)

    def test_remove_release_component_contact(self):
        url = reverse('releasecomponentcontact-list', kwargs={'instance_pk': 1})
        data = {}
        response = self.client.get(url, data, format='json')
        contact = response.data[0]
        response = self.client.delete(contact['url'], format='json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        response = self.client.get(url, data, format='json')
        self.assertNotIn(contact, response.data)
        # PDC-288
        self.assertNumChanges([1])

    def test_update_release_component_contacts(self):
        url = reverse('releasecomponent-list')
        data = {
            "global_component": "python",
            "releases": ["release-1.0"],
            "contacts": [{
                "contact_role": "qe_ack",
                "contact": {
                    "username": "person2",
                    "email": "person2@test.com"
                }
            }]
        }
        response = self.client.put(url, format='json', data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        release_component = response.data[0]
        self.assertEqual(release_component['global_component'], 'python')
        self.assertEqual(release_component['release']['release_id'], 'release-1.0')
        contacts = release_component['contacts']

        self.assertEqual(contacts[0]['contact_role'], 'qe_ack')
        self.assertEqual(contacts[0]['contact']['username'],
                         'person2')
        self.assertEqual(contacts[0]['contact']['email'],
                         'person2@test.com')
        self.assertIsNone(contacts[0].get('inherited', None))
        self.assertNumChanges([1])

    def test_partial_update_release_component_contacts_fails(self):
        url = reverse('releasecomponent-list')
        response = self.client.patch(url, data=None)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_update_multiple_release_component_contacts(self):
        url = reverse('releasecomponent-list')
        data = {
            "global_component": "MySQL-python",
            "releases": ["release-1.0"],
            "contacts": [{
                "contact_role": "qe_ack",
                "contact": {
                    "username": "person2",
                    "email": "person2@test.com"
                }
            }, {
                "contact_role": "pm",
                "contact": {
                    "username": "person2",
                    "email": "person2@test.com"
                }
            }]
        }
        response = self.client.put(url, format='json', data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        release_component = response.data[0]
        self.assertEqual(release_component['global_component'], 'MySQL-python')
        self.assertEqual(release_component['release']['release_id'], 'release-1.0')
        contacts = release_component['contacts']

        self.assertEqual(contacts[0]['contact_role'], 'pm')
        self.assertEqual(contacts[0]['contact']['username'],
                         'person2')
        self.assertEqual(contacts[0]['contact']['email'],
                         'person2@test.com')
        self.assertIsNone(contacts[0].get('inherited', None))
        self.assertEqual(contacts[1]['contact_role'], 'qe_ack')
        self.assertEqual(contacts[1]['contact']['username'],
                         'person2')
        self.assertEqual(contacts[1]['contact']['email'],
                         'person2@test.com')
        self.assertIsNone(contacts[1].get('inherited', None))
        self.assertNumChanges([1])

    def test_update_multiple_rc_contacts_with_inexistent_contact(self):
        # PDC-289
        url = reverse('releasecomponent-list')
        data = {
            "global_component": "MySQL-python",
            "releases": ["release-1.0"],
            "contacts": [{
                "contact_role": "new_type",
                "contact": {
                    "username": "person2",
                    "email": "person2@test.com"
                }
            }, {
                "contact_role": "pm",
                "contact": {
                    "username": "person2",
                    "email": "person2@test.com"
                }
            }]
        }
        response = self.client.put(url, format='json', data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        release_component = response.data[0]
        self.assertEqual(release_component['global_component'], 'MySQL-python')
        self.assertEqual(release_component['release']['release_id'], 'release-1.0')
        contacts = release_component['contacts']

        self.assertEqual(contacts[1]['contact_role'], 'new_type')
        self.assertEqual(contacts[1]['contact']['username'],
                         'person2')
        self.assertEqual(contacts[1]['contact']['email'],
                         'person2@test.com')
        self.assertIsNone(contacts[1].get('inherited', None))
        self.assertNumChanges([3])

    def test_update_duplicated_rc_contacts_with_inexistent_contact(self):
        # PDC-289
        url = reverse('releasecomponent-list')
        data = {
            "global_component": "MySQL-python",
            "releases": ["release-1.0"],
            "contacts": [{
                "contact_role": "pm",
                "contact": {
                    "username": "person2",
                    "email": "person2@test.com"
                }
            }, {
                "contact_role": "pm",
                "contact": {
                    "username": "person2",
                    "email": "person2@test.com"
                }
            }]
        }
        response = self.client.put(url, format='json', data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        release_component = response.data[0]
        self.assertEqual(release_component['global_component'], 'MySQL-python')
        self.assertEqual(release_component['release']['release_id'], 'release-1.0')

        contacts = release_component['contacts']
        self.assertEqual(len(contacts), 1)

        self.assertEqual(contacts[0]['contact_role'], 'pm')
        self.assertEqual(contacts[0]['contact']['username'],
                         'person2')
        self.assertEqual(contacts[0]['contact']['email'],
                         'person2@test.com')
        self.assertIsNone(contacts[0].get('inherited', None))
        self.assertNumChanges([1])

    def test_bulk_update_with_release(self):
        # PDC-289
        url = reverse('releasecomponent-list')
        data = {
            "global_component": "MySQL-python",
            "releases": "release-1.0",
            "contacts": [{
                "contact_role": "pm",
                "contact": {
                    "username": "person2",
                    "email": "person2@test.com"
                }
            }, {
                "contact_role": "pm",
                "contact": {
                    "username": "person2",
                    "email": "person2@test.com"
                }
            }]
        }
        response = self.client.put(url, format='json', data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        release_component = response.data[0]
        self.assertEqual(release_component['global_component'], 'MySQL-python')
        self.assertEqual(release_component['release']['release_id'], 'release-1.0')

        contacts = release_component['contacts']
        self.assertEqual(len(contacts), 1)

        self.assertEqual(contacts[0]['contact_role'], 'pm')
        self.assertEqual(contacts[0]['contact']['username'],
                         'person2')
        self.assertEqual(contacts[0]['contact']['email'],
                         'person2@test.com')
        self.assertIsNone(contacts[0].get('inherited', None))

    def test_create_with_inactive_release(self):
        url = reverse('releasecomponent-list')
        data = {
            "global_component": "MySQL-python",
            "releases": [self.rhel5_inactive.release_id],
            "name": "MySQL-python-1.2.5"
        }
        response = self.client.post(url, format='json', data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_bulk_delete_contacts(self):
        url = reverse('releasecomponentcontact-list', args=[1])
        response = self.client.delete(url, [5, 6, 7], format='json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        c = models.ReleaseComponent.objects.get(pk=1)
        self.assertEqual(c.contacts.count(), 0)

    def test_delete_inherited_contact(self):
        url = reverse('releasecomponentcontact-detail', kwargs={'instance_pk': 1, 'pk': 2})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('is inherited from GlobalComponent', response.data.get('detail'))

    def test_delete_inherited_contact_from_globalcomponent(self):
        url = reverse('releasecomponent-detail', kwargs={'pk': 1})
        response = self.client.get(url, format='json')
        length = len(response.data['contacts'])

        url1 = reverse('releasecomponentcontact-list', kwargs={'instance_pk': 1})
        response1 = self.client.get(url1, format='json')
        self.assertEqual(length, len(response1.data))

        url2 = reverse('globalcomponentcontact-detail', kwargs={'instance_pk': 1, 'pk': 2})
        self.client.delete(url2)

        url3 = reverse('globalcomponentcontact-detail', kwargs={'instance_pk': 1, 'pk': 1})
        self.client.delete(url3)

        url4 = reverse('releasecomponent-detail', kwargs={'pk': 1})
        response4 = self.client.get(url4, format='json')
        self.assertEqual(length - 2, len(response4.data['contacts']))

        url5 = reverse('releasecomponentcontact-list', kwargs={'instance_pk': 1})
        response5 = self.client.get(url5, format='json')
        self.assertEqual(length - 2, len(response5.data))

        url6 = reverse('globalcomponentcontact-list', kwargs={'instance_pk': 1})
        response6 = self.client.get(url6)
        self.assertEqual(response6.data, [])


class ReleaseCloneWithComponentsTestCase(TestCaseWithChangeSetMixin, APITestCase):
    fixtures = [
        "pdc/apps/release/fixtures/tests/release.json",
        "pdc/apps/component/fixtures/tests/upstream.json",
        "pdc/apps/component/fixtures/tests/global_component.json",
        "pdc/apps/component/fixtures/tests/release_component.json",
        "pdc/apps/contact/fixtures/tests/contact_role.json",
        'pdc/apps/component/fixtures/tests/group_type.json',
        'pdc/apps/component/fixtures/tests/release_component_group.json',
        'pdc/apps/component/fixtures/tests/release_component_relationship.json'
    ]

    def test_clone_components(self):
        response = self.client.post(reverse('releaseclone-list'),
                                    {'old_release_id': 'release-1.0', 'version': '1.1'},
                                    format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(models.ReleaseComponent.objects.filter(release__release_id='release-1.1').count(), 2)
        self.assertNumChanges([6])

    def test_clone_component_groups(self):
        response = self.client.post(reverse('releaseclone-list'),
                                    {'old_release_id': 'release-1.0', 'version': '1.1'},
                                    format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        groups = models.ReleaseComponentGroup.objects.filter(release__release_id='release-1.1')
        self.assertEqual(groups.count(), 1)
        self.assertNotEqual(groups[0].id, 1)
        self.assertNumChanges([6])

    def test_clone_release_component_relationship(self):
        response = self.client.post(reverse('releaseclone-list'),
                                    {'old_release_id': 'release-1.0', 'version': '1.1'},
                                    format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        relations = models.ReleaseComponentRelationship.objects.filter(
            from_component__release__release_id='release-1.1')
        self.assertEqual(relations.count(), 2)
        self.assertGreater(relations[0].id, 2)
        self.assertNumChanges([6])

    def test_clone_component_with_contact(self):
        response = self.client.put(reverse('releasecomponent-list'),
                                   {'global_component': 'python', 'releases': ['release-1.0'],
                                    'contacts': [{'contact_role': 'qe_ack',
                                                  'contact': {'username': 'person1',
                                                              'email': 'person1@test.com'}}]},
                                   format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNumChanges([3])

        response = self.client.post(reverse('releaseclone-list'),
                                    {'old_release_id': 'release-1.0', 'version': '1.1'},
                                    format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertNumChanges([3, 6])
        contacts = models.ReleaseComponent.objects.get(release__release_id='release-1.1',
                                                       name='python27').contacts.all()
        self.assertEqual(1, len(contacts))
        self.assertEqual('qe_ack', contacts[0].contact_role.name)
        self.assertEqual('person1', contacts[0].contact.person.username)
        count = sum([row.contacts.all().count() for row in models.ReleaseComponent.objects.all()])
        self.assertEqual(2, count)

    def test_clone_components_change_dist_git_branch(self):
        response = self.client.post(reverse('releaseclone-list'),
                                    {'old_release_id': 'release-1.0', 'version': '1.1',
                                     'component_dist_git_branch': 'new_branch'},
                                    format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(models.ReleaseComponent.objects.filter(release__release_id='release-1.1').count(), 2)
        self.assertNumChanges([6])
        rcs = models.ReleaseComponent.objects.filter(release__release_id='release-1.1')
        self.assertEqual(['new_branch', 'new_branch'], [rc.dist_git_branch for rc in rcs])

    def test_clone_components_include_inactive_by_default(self):
        rc = models.ReleaseComponent.objects.get(name='python27')
        rc.active = False
        rc.save()
        response = self.client.post(reverse('releaseclone-list'),
                                    {'old_release_id': 'release-1.0', 'version': '1.1'},
                                    format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        rcs = models.ReleaseComponent.objects.filter(release__release_id='release-1.1')
        self.assertEqual(len(rcs), 2)
        self.assertNumChanges([6])

    def test_clone_components_include_inactive_explicitly(self):
        rc = models.ReleaseComponent.objects.get(name='python27')
        rc.active = False
        rc.save()
        response = self.client.post(reverse('releaseclone-list'),
                                    {'old_release_id': 'release-1.0', 'version': '1.1',
                                     'include_inactive': True},
                                    format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(models.ReleaseComponent.objects.filter(release__release_id='release-1.1').count(), 2)
        self.assertNumChanges([6])

    def test_clone_components_exclude_inactive_explicitly(self):
        rc = models.ReleaseComponent.objects.get(name='python27')
        rc.active = False
        rc.save()
        response = self.client.post(reverse('releaseclone-list'),
                                    {'old_release_id': 'release-1.0', 'version': '1.1',
                                     'include_inactive': False},
                                    format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(models.ReleaseComponent.objects.filter(release__release_id='release-1.1').count(), 1)
        self.assertNumChanges([3])

    def test_clone_components_bad_include_inactive_value(self):
        response = self.client.post(reverse('releaseclone-list'),
                                    {'old_release_id': 'release-1.0', 'version': '1.1',
                                     'include_inactive': 'foobar'},
                                    format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Value [foobar] of include_inactive is not a boolean',
                      response.content)


class BugzillaComponentRESTTestCase(TestCaseWithChangeSetMixin, APITestCase):
    fixtures = [
        "pdc/apps/component/fixtures/tests/upstream.json",
        "pdc/apps/component/fixtures/tests/bugzilla_component.json",
        "pdc/apps/component/fixtures/tests/global_component.json",
        "pdc/apps/release/fixtures/release_type.json",
        "pdc/apps/release/fixtures/tests/release.json",
    ]

    def test_list_bugzilla_component(self):
        url = reverse('bugzillacomponent-list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)
        names = list(d['name'] for d in response.data['results'])
        self.assertTrue('python' in names)
        self.assertTrue('lib' in names)

    def test_query_bugzilla_component(self):
        url = reverse('bugzillacomponent-list')
        url = '%s%s' % (url, '?name=python')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['name'], 'python')

    def test_query_bugzilla_component_with_multiple_values(self):
        url = reverse('bugzillacomponent-list')
        url = '%s%s' % (url, '?name=python&name=lib')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)
        names = list(d['name'] for d in response.data['results'])
        self.assertIn('python', names)
        self.assertIn('lib', names)

    def test_detail_bugzilla_component(self):
        url = reverse('bugzillacomponent-detail', kwargs={'pk': 1})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'python')

    def test_detail_bugzilla_component_only_include_name_field(self):
        url = reverse('bugzillacomponent-detail', kwargs={'pk': 1})
        response = self.client.get(url + '?fields=name', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertDictEqual(response.data, {'name': 'python'})

    def test_detail_bugzilla_component_exclude_parent_component_fields(self):
        url = reverse('bugzillacomponent-detail', kwargs={'pk': 1})
        response = self.client.get(url + '?exclude_fields=parent_component', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'python')
        self.assertNotIn('parent_component', response.data)

    def test_detail_bugzilla_component_not_exist(self):
        url = reverse('bugzillacomponent-detail', kwargs={'pk': 999})
        response = self.client.get(url, format='json')
        data = {'detail': 'Not found.'}
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data, data)

    def test_create_bugzilla_component(self):
        url = reverse('bugzillacomponent-list')
        data = {'name': 'bin', 'parent_pk': 1}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['parent_component'], 'python')
        self.assertIsNotNone(response.data['subcomponents'])

    def test_create_bugzilla_component_duplicate(self):
        url = reverse('bugzillacomponent-list')
        data = {'name': 'lib', "parent_pk": 1}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_bugzilla_component_extra_fields(self):
        url = reverse('bugzillacomponent-list')
        data = {'name': 'bin', 'parent_pk': 1, 'foo': 'bar'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data.get('detail'), 'Unknown fields: "foo".')

    def test_create_root_bugzilla_component_duplicate(self):
        url = reverse('bugzillacomponent-list')
        data = {'name': 'python'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_bugzilla_component(self):
        url = reverse('bugzillacomponent-detail', kwargs={'pk': 2})
        data = {'name': 'lib64', 'parent_pk': 1}
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'lib64')
        self.assertNumChanges([1])

    def test_partial_update_empty(self):
        url = reverse('bugzillacomponent-detail', kwargs={'pk': 2})
        response = self.client.patch(url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_bugzilla_component_parent_not_exist(self):
        url = reverse('bugzillacomponent-detail', kwargs={'pk': 2})
        data = {'name': 'lib64', 'parent_pk': 999}
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_bugzilla_component_with_cyclic_error(self):
        url = reverse('bugzillacomponent-detail', kwargs={'pk': 1})
        data = {'parent_pk': 2}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_bugzilla_component_with_null_parent_pk(self):
        url = reverse('bugzillacomponent-detail', kwargs={'pk': 2})
        data = {'name': 'python1', 'parent_pk': None}
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNumChanges([1])

    def test_update_bugzilla_component_already_exists(self):
        url = reverse('bugzillacomponent-detail', kwargs={'pk': 2})
        data = {'name': 'python', 'parent_pk': None}
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        url1 = reverse('bugzillacomponent-list')
        data1 = {'name': 'bin', 'parent_pk': 2}
        response1 = self.client.post(url1, data1, format='json')
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)

        url2 = reverse('bugzillacomponent-detail', kwargs={'pk': 3})
        data2 = {'name': 'lib', 'parent_pk': 1}
        response2 = self.client.put(url2, data2, format='json')
        self.assertEqual(response2.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_bugzilla_component_lack_input(self):
        url = reverse('bugzillacomponent-detail', kwargs={'pk': 2})
        data = {'name': 'lib64'}
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = {'parent_pk': 1}
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_patch_update_bugzilla_component(self):
        url = reverse('bugzillacomponent-detail', kwargs={'pk': 2})
        data = {'name': 'lib64'}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'lib64')
        self.assertNumChanges([1])

    def test_patch_update_bugzilla_component1(self):
        url = reverse('bugzillacomponent-list')
        data = {'name': 'bin', 'parent_pk': 2}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        url1 = reverse('bugzillacomponent-detail', kwargs={'pk': 3})
        data1 = {'parent_pk': 2}
        response1 = self.client.patch(url1, data1, format='json')
        self.assertEqual(response1.status_code, status.HTTP_200_OK)

    def test_patch_update_bugzilla_component_already_exists(self):
        url = reverse('bugzillacomponent-list')
        data = {'name': 'python', 'parent_pk': 2}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        url1 = reverse('bugzillacomponent-detail', kwargs={'pk': 3})
        data1 = {'parent_pk': None}
        response1 = self.client.patch(url1, data1, format='json')
        self.assertEqual(response1.status_code, status.HTTP_400_BAD_REQUEST)

    def test_patch_update_root_bugzilla_component_in_release_component(self):
        url = reverse('releasecomponent-list')
        data = {'release': 'release-1.0', 'global_component': 'python', 'name': 'python26', 'brew_package': 'python-pdc', 'bugzilla_component': 'python'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        url1 = reverse('bugzillacomponent-list')
        data1 = {'name': 'test', 'parent_pk': None}
        response1 = self.client.post(url1, data1, format='json')
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)

        url2 = reverse('bugzillacomponent-detail', kwargs={'pk': 1})
        data2 = {'parent_pk': 3}
        response2 = self.client.patch(url2, data2, format='json')
        self.assertEqual(response2.status_code, status.HTTP_200_OK)

        url3 = reverse('releasecomponent-detail', kwargs={'pk': 1})
        response3 = self.client.get(url3, format='json')
        self.assertEqual(response3.data['bugzilla_component']['parent_component'], 'test')
        self.assertNumChanges([1, 1, 1])

    def test_patch_update_root_bugzilla_component_not_in_release_component(self):
        url = reverse('releasecomponent-list')
        data = {'release': 'release-1.0', 'global_component': 'python', 'name': 'python26', 'brew_package': 'python-pdc', 'bugzilla_component': 'python'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        url1 = reverse('bugzillacomponent-list')
        data1 = {'name': 'test', 'parent_pk': None}
        response1 = self.client.post(url1, data1, format='json')
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)

        url2 = reverse('bugzillacomponent-list')
        data2 = {'name': 'test1', 'parent_pk': None}
        response2 = self.client.post(url2, data2, format='json')
        self.assertEqual(response2.status_code, status.HTTP_201_CREATED)

        url3 = reverse('bugzillacomponent-detail', kwargs={'pk': 4})
        data3 = {'parent_pk': 3}
        response3 = self.client.patch(url3, data3, format='json')
        self.assertEqual(response3.status_code, status.HTTP_200_OK)

    def test_delete_bugzilla_component(self):
        url = reverse('bugzillacomponent-detail', kwargs={'pk': 2})
        response = self.client.delete(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        url1 = reverse('bugzillacomponent-list')
        response1 = self.client.get(url1, format='json')
        self.assertEqual(response1.data['count'], 1)
        self.assertNumChanges([1])

    def test_delete_bugzilla_component_with_child(self):
        url = reverse('bugzillacomponent-detail', kwargs={'pk': 1})
        response = self.client.delete(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        url1 = reverse('bugzillacomponent-list')
        response1 = self.client.get(url1, format='json')
        self.assertEqual(response1.data['count'], 0)
        self.assertNumChanges([2])

    def test_delete_bugzilla_component_in_release_component(self):
        pyth = models.BugzillaComponent.objects.create(name='python26')
        models.BugzillaComponent.objects.create(name='bin', parent_component=pyth)

        url = reverse('releasecomponent-list')
        data = {'release': 'release-1.0', 'global_component': 'python', 'name': 'python26', 'brew_package': 'python-pdc', 'bugzilla_component': 'python26'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.data['bugzilla_component']['subcomponents'][0], 'bin')

        url1 = reverse('bugzillacomponent-detail', kwargs={'pk': 4})
        self.client.delete(url1, format='json')

        url2 = reverse('releasecomponent-detail', kwargs={'pk': 1})
        response2 = self.client.get(url2, format='json')
        self.assertEqual(response2.data['bugzilla_component']['subcomponents'], [])

        url3 = reverse('bugzillacomponent-detail', kwargs={'pk': 3})
        self.client.delete(url3, format='json')

        url4 = reverse('releasecomponent-detail', kwargs={'pk': 1})
        response4 = self.client.get(url4, format='json')
        self.assertIsNone(response4.data['bugzilla_component'])
        self.assertNumChanges([1, 1, 2])


class GroupTypeRESTTestCase(TestCaseWithChangeSetMixin, APITestCase):
    fixtures = [
        'pdc/apps/component/fixtures/tests/group_type.json',
    ]

    def test_list_group_types(self):
        url = reverse('componentgrouptype-list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 2)

    def test_query_group_types(self):
        url = reverse('componentgrouptype-list')
        response = self.client.get(url + '?name=type1', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 1)

    def test_get_specified_group_type(self):
        url = reverse('componentgrouptype-detail', kwargs={'pk': 1})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_specified_group_type_not_exist(self):
        url = reverse('componentgrouptype-detail', kwargs={'pk': 9999})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_group_type(self):
        url = reverse('componentgrouptype-list')
        data = {'name': 'type3', 'description': 'group type 3'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertNumChanges([1])

    def test_update_group_type(self):
        url = reverse('componentgrouptype-detail', kwargs={'pk': 1})
        data = {'name': 'type1', 'description': 'new description'}
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNumChanges([1])

    def test_partial_update_group_type(self):
        url = reverse('componentgrouptype-detail', kwargs={'pk': 1})
        data = {'description': 'new description'}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNumChanges([1])

    def test_delete_group_type(self):
        url = reverse('componentgrouptype-detail', kwargs={'pk': 1})
        response = self.client.delete(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertNumChanges([1])


class GroupRESTTestCase(TestCaseWithChangeSetMixin, APITestCase):
    fixtures = [
        'pdc/apps/component/fixtures/tests/group_type.json',
        'pdc/apps/component/fixtures/tests/global_component.json',
        'pdc/apps/component/fixtures/tests/upstream.json',
        'pdc/apps/release/fixtures/tests/release.json',
        'pdc/apps/release/fixtures/tests/new_release.json',
        'pdc/apps/component/fixtures/tests/release_component.json',
        'pdc/apps/component/fixtures/tests/release_component_group.json'
    ]

    def test_list_group(self):
        url = reverse('componentgroup-list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 1)

    def test_query_groups(self):
        url = reverse('componentgroup-list')
        response = self.client.get(url + '?group_type=type1', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 1)

        response = self.client.get(url + '?release=release-1.0', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 1)

        response = self.client.get(url + '?release_component=python27', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 1)

    def test_query_groups_with_incorrect_filter(self):
        url = reverse('componentgroup-list')
        response = self.client.get(url + '?wrong=type1', format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_specified_group(self):
        url = reverse('componentgroup-detail', kwargs={'pk': 1})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_specified_group_not_exist(self):
        url = reverse('componentgroup-detail', kwargs={'pk': 9999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_group_with_components_id(self):
        url = reverse('componentgroup-list')
        data = {'group_type': 'type2', 'release': 'release-1.0', 'description': 'dd',
                'components': [{'id': 1}, {'id': 2}]}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertNumChanges([1])

    def test_create_group_with_components_and_different_release(self):
        url = reverse('componentgroup-list')
        data = {'group_type': 'type2', 'release': 'release-2.0', 'description': 'dd',
                'components': [{'id': 1}]}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNumChanges([])

    def test_create_group_with_components_unique_together_fields(self):
        url = reverse('componentgroup-list')
        data = {'group_type': 'type2', 'release': 'release-1.0', 'description': 'dd',
                'components': [{'release': 'release-1.0', 'global_component': 'python', 'name': 'python27'}]}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertNumChanges([1])

    def test_create_group_with_components_mix_id_unique_together_fields(self):
        url = reverse('componentgroup-list')
        data = {'group_type': 'type2', 'release': 'release-1.0', 'description': 'dd',
                'components': [{'id': 2, 'release': 'release-1.0', 'global_component': 'python', 'name': 'python27'}]}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNumChanges([])

    def test_create_group_with_components_wrong_format(self):
        url = reverse('componentgroup-list')
        data = {'group_type': 'type2', 'release': 'release-1.0', 'description': 'dd',
                'components': ['wrong field']}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNumChanges([])

    def test_create_group_with_components_with_wrong_field(self):
        url = reverse('componentgroup-list')
        data = {'group_type': 'type2', 'release': 'release-1.0', 'description': 'dd',
                'components': [{"foo": "bar"}]}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNumChanges([])

        data = {'group_type': 'type2', 'release': 'release-1.0', 'description': 'dd',
                'components': [{"iid": 1, "release": "foo"}]}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNumChanges([])

        data = {'group_type': 'type2', 'release': 'release-1.0', 'description': 'dd',
                'components': [{"id": 1, "release": "foo"}]}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNumChanges([])

    def test_create_group_without_component(self):
        url = reverse('componentgroup-list')
        data = {'group_type': 'type2', 'release': 'release-1.0', 'description': 'dd'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertNumChanges([1])

    def test_create_group_with_non_existed_release_component(self):
        url = reverse('componentgroup-list')
        data = {'group_type': 'type2', 'release': 'release-1.0', 'description': 'dd', 'components': [{'id': 9999}]}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNumChanges([])

    def test_create_group_with_different_releases(self):
        url = reverse('componentgroup-list')
        data = {'group_type': 'type2', 'release': 'release-2.0', 'description': 'dd',
                'components': [{'id': 1}, {'id': 2}]}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNumChanges([])

    def test_update_group(self):
        url = reverse('componentgroup-detail', kwargs={'pk': 1})
        data = {'group_type': 'type1', 'release': 'release-1.0', 'description': 'dd', 'components': [{'id': 1}]}
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('components')[0].get('name'), 'python27')

    def test_update_group_with_other_release(self):
        url = reverse('componentgroup-detail', kwargs={'pk': 1})
        data = {'group_type': 'type1', 'release': 'release-2.0', 'description': 'dd', 'components': [{'id': 1}]}
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_partial_update_group(self):
        url = reverse('componentgroup-detail', kwargs={'pk': 1})
        data = {'components': [{'id': 1}]}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('components')[0].get('name'), 'python27')

    def test_partial_update_other_release(self):
        url = reverse('componentgroup-detail', kwargs={'pk': 1})
        data = {'release': 'release-2.0'}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_delete_group(self):
        url = reverse('componentgroup-detail', kwargs={'pk': 1})
        response = self.client.delete(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertNumChanges([1])

    def test_delete_type_with_existing_group(self):
        url = reverse('componentgrouptype-detail', args=[1])
        response = self.client.delete(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNumChanges([])


class ReleaseComponentRelationshipRESTTestCase(TestCaseWithChangeSetMixin, APITestCase):
    fixtures = [
        'pdc/apps/component/fixtures/tests/global_component.json',
        'pdc/apps/component/fixtures/tests/upstream.json',
        'pdc/apps/release/fixtures/tests/release.json',
        'pdc/apps/release/fixtures/tests/new_release.json',
        'pdc/apps/component/fixtures/tests/release_component_for_relationship.json',
        'pdc/apps/component/fixtures/tests/release_component_relationship.json'
    ]

    def test_list_relationship(self):
        url = reverse('rcrelationship-list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 2)

    def test_create_relationship(self):
        url = reverse('rcrelationship-list')
        data = {"from_component": {'id': 1}, "to_component": {'id': 2}, "type": "executes"}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertNumChanges([1])

        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 3)

    def test_create_relationship_with_non_integer_id(self):
        url = reverse('rcrelationship-list')
        data = {"from_component": {'id': 'ab'}, "to_component": {'id': 'abc'}, "type": "executes"}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNumChanges([])

    def test_create_relationship_with_non_existed_release_component(self):
        url = reverse('rcrelationship-list')
        data = {"from_component": {'id': 1}, "to_component": {'id': 20000}, "type": "executes"}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNumChanges([])

    def test_create_relationship_with_non_existed_type(self):
        url = reverse('rcrelationship-list')
        data = {"from_component": {'id': 1}, "to_component": {'id': 2}, "type": "fake-type"}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNumChanges([])

    def test_create_relationship_with_unique_together_fields(self):
        url = reverse('rcrelationship-list')
        data = {"from_component": {'release': 'release-1.0', 'global_component': 'python', 'name': 'python27'},
                "to_component": {'release': 'release-1.0', 'global_component': 'MySQL-python', 'name': 'MySQL-python'},
                "type": "executes"}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertNumChanges([1])

    def test_create_group_with_components_wrong_format(self):
        url = reverse('rcrelationship-list')
        data = {"from_component": 'wrong field',
                "to_component": {'release': 'release-1.0', 'global_component': 'MySQL-python', 'name': 'MySQL-python'},
                "type": "executes"}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNumChanges([])

    def test_query_relationship(self):
        url = reverse('rcrelationship-list')
        response = self.client.get(url + '?type=executes', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 1)

        response = self.client.get(url + '?type=bundles', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 1)

        response = self.client.get(url + '?from_component_release=release-1.0', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 2)

        response = self.client.get(url + '?to_component_release=release-1.0', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 2)

        response = self.client.get(url + '?from_component_name=python27', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 1)

        response = self.client.get(url + '?to_component_name=MySQL-python', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 1)

        response = self.client.get(url + '?type=executes&from_component_name=python27', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 0)

        response = self.client.get(url + '?type=bundles&from_component_name=python27', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 1)

    def test_update_relationship(self):
        url = reverse('rcrelationship-detail', kwargs={'pk': 1})
        # 2 name MySQL-python, 3 name java
        data = {'type': 'executes', "from_component": {'id': 2}, "to_component": {'id': 3}}
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('to_component').get('name'), 'java')

    def test_update_relationship_with_non_exist_release_component(self):
        url = reverse('rcrelationship-detail', kwargs={'pk': 1})
        data = {'type': 'executes', "from_component": {'id': 2}, "to_component": {'id': 20}}
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_partial_update_relationship_to_component(self):
        url = reverse('rcrelationship-detail', kwargs={'pk': 1})
        # 2 name MySQL-python, 3 name java
        data = {"to_component": {'id': 3}}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('to_component').get('name'), 'java')

    def test_partial_update_relationship_from_component(self):
        url = reverse('rcrelationship-detail', kwargs={'pk': 1})
        # 2 name MySQL-python, 3 name java
        data = {"from_component": {'id': 3}}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('from_component').get('name'), 'java')

    def test_partial_update_relationship_type(self):
        url = reverse('rcrelationship-detail', kwargs={'pk': 1})
        data = {"type": 'bundles'}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('type'), 'bundles')

    def test_delete_group(self):
        url = reverse('rcrelationship-detail', kwargs={'pk': 1})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.client.delete(url, format='json')
        self.assertNumChanges([1])

        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
