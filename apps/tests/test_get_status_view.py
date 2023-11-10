from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from projects.models import Project

from ..models import AppCategories, AppInstance, Apps

User = get_user_model()

test_user = {"username": "foo@test.com", "email": "foo@test.com", "password": "bar"}


class GetStatusViewTestCase(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(test_user["username"], test_user["email"], test_user["password"])
        self.category = AppCategories.objects.create(name="Network", priority=100, slug="network")
        self.app = Apps.objects.create(
            name="Jupyter Lab",
            slug="jupyter-lab",
            user_can_edit=False,
            category=self.category,
        )

        self.project = Project.objects.create_project(
            name="test-perm-get_status",
            owner=self.user,
            description=""
        )

        self.app_instance = AppInstance.objects.create(
            access="public",
            owner=self.user,
            name="test_app_instance_public",
            app=self.app,
            project=self.project,
            parameters={
                "environment": {"pk": ""},
            },
        )

    def test_user_has_access(self):
        c = Client()

        response = c.post("/accounts/login/", {"username": test_user["email"], "password": test_user["password"]})
        response.status_code

        self.assertEqual(response.status_code, 302)

        url = f"/{self.user.username}/{self.project.slug}/apps/status"

        response = c.post(url, {"apps": [self.app_instance.id]})

        self.assertEqual(response.status_code, 200)

    def test_user_has_no_access(self):
        c = Client()

        url = f"/{self.user.username}/{self.project.slug}/apps/status"

        response = c.post(url, {"apps": [self.app_instance.id]})

        self.assertEqual(response.status_code, 403)

        user = User.objects.create_user("foo2@test.com", "foo2@test.com", "bar")

        response = c.post("/accounts/login/", {"username": "foo2@test.com", "password": "bar"})
        response.status_code

        self.assertEqual(response.status_code, 302)

        url = f"/{user.username}/{self.project.slug}/apps/status"

        response = c.post(url, {"apps": [self.app_instance.id]})

        self.assertEqual(response.status_code, 403)

    def test_apps_empty(self):
        c = Client()

        response = c.post("/accounts/login/", {"username": test_user["email"], "password": test_user["password"]})
        response.status_code

        self.assertEqual(response.status_code, 302)

        url = f"/{self.user.username}/{self.project.slug}/apps/status"

        response = c.post(url, {"apps": []})

        self.assertEqual(response.status_code, 200)
