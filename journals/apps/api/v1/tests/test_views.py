""" Test Cases for UserPageVisitView """

import logging
import json

from django.test import TestCase
from django.urls import reverse

from journals.apps.core.tests.factories import UserFactory, PageFactory

logger = logging.getLogger(__name__)


class TestUserPageVisitView(TestCase):
    """
    Test Cases for UserPageVisitView
    """

    def setUp(self):
        super(TestUserPageVisitView, self).setUp()

        self.user = UserFactory()
        self.page = PageFactory(path="002", numchild=1)
        self.other_page = PageFactory(path="002001", numchild=0)
        self.path = reverse("api:v1:userpagevisit", kwargs={'user_id': self.user.id})
        self.client.login(username=self.user.username, password='password')

    def _create_user_page_visit(self, user, page):
        """
        Created the UserPageVisit's object with the given user and page objects.
        """
        self.client.post(
            self.path,
            {
                "user": user.id,
                "page": page.id,
            }
        )

    def _assert_user_page_visit(self, response, user, page):
        """
        Assert the given response with the given user and page object.
        """
        response_data = json.loads(response.content.decode('utf-8'))

        self.assertEqual(len(response_data), 1)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response_data[0]['page'], page.id)
        self.assertEqual(response_data[0]['user'], user.id)

    def test_get_request(self):
        """
        Test the get functionality of UserPageVisitView
        """
        # this should return zero objects because
        # we didn't create any UserPageVisit object
        response = self.client.get(self.path)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(json.loads(response.content.decode('utf-8'))), 0)

        self._create_user_page_visit(self.user, self.page)
        response = self.client.get(self.path)
        self._assert_user_page_visit(response, self.user, self.page)

    def test_create_request(self):
        """
        Test the create functionality of UserPageVisitView
        """
        self._create_user_page_visit(self.user, self.page)
        self._create_user_page_visit(self.user, self.other_page)
        response = self.client.get(self.path)
        response_data = json.loads(response.content.decode('utf-8'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response_data), 2)

    def test_search_on_page(self):
        """
        Test the UserPageVisitView, by searching on the base of page id.
        """
        self._create_user_page_visit(self.user, self.page)
        self._create_user_page_visit(self.user, self.other_page)
        path_with_parameters = "{path}/?page_id={page_id}".format(
            path=self.path,
            page_id=self.other_page.id
        )
        response = self.client.get(path_with_parameters)
        self._assert_user_page_visit(response, self.user, self.other_page)

    def test_get_last_page(self):
        """
        Test the UserPageVisitView, by getting the last page visit of a user.
        """
        self._create_user_page_visit(self.user, self.other_page)
        self._create_user_page_visit(self.user, self.page)
        path_with_parameters = "{path}/?last_visit=true".format(
            path=self.path,
        )
        response = self.client.get(path_with_parameters)

        # API should return the UserPageVisit object which was created later.
        self._assert_user_page_visit(response, self.user, self.page)

    def test_login_permission(self):
        """
        Test the UserPageVisitView's permissions
        """
        self._create_user_page_visit(self.user, self.page)
        response = self.client.get(self.path)
        self._assert_user_page_visit(response, self.user, self.page)

        self.client.logout()
        response = self.client.get(self.path)
        self.assertEqual(response.status_code, 403)

    def test_is_staff_permission(self):
        """
        Test the UserPageVisitView's permissions
        """
        # non-staff user can get its own visits
        self._create_user_page_visit(self.user, self.page)
        response = self.client.get(self.path)
        self._assert_user_page_visit(response, self.user, self.page)

        # non-staff user can not get any other user's visits
        other_user = UserFactory()
        self._create_user_page_visit(other_user, self.page)
        path = reverse("api:v1:userpagevisit", kwargs={'user_id': other_user.id})
        response = self.client.get(path)
        self.assertEqual(response.status_code, 403)

        # staff user can get any user's visits.
        self.user.is_staff = True
        self.user.save()
        response = self.client.get(path)
        self._assert_user_page_visit(response, other_user, self.page)
