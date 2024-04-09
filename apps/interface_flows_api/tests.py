from django.urls import reverse
from rest_framework.test import APITestCase

from apps.interface_flows_api.models import Flow, FlowVisibility, Genre, User


class FlowsTests(APITestCase):
    def setUp(self):
        Genre.objects.create(name="genre_test_1")
        Genre.objects.create(name="genre_test_2")
        User.objects.create_user(
            username="user1", password="abcde", email="test@mail.ru"
        )
        User.objects.create_user(
            username="not_user1", password="1234", email="test@mail.ru"
        )
        self.private_flow = Flow.objects.create(
            title="flow",
            author=User.objects.get(username="user1").profile,
            visibility=FlowVisibility.PRIVATE,
        )

    def test_private_flow(self):
        """Test to check if a private flow is hidden for non author users."""
        login_url = reverse("login")
        flow_url = reverse("flow", args=[self.private_flow.id])
        response = self.client.post(
            login_url, {"username": "not_user1", "password": "1234"}
        )
        fake_token = response.json()["token"]
        response = self.client.get(
            flow_url, headers={"Authorization": f"Token {fake_token}"}
        )
        self.assertEqual(response.status_code, 403)

    def test_get_private_flow_anonymously(self):
        """Test to check if a private flow is hidden for anonymous users."""
        url = reverse("flow", args=[self.private_flow.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_user_with_existing_username(self):
        """Test"""
        url = reverse("signup")
        response = self.client.post(
            url, {"username": "user1", "email": "test@mail.ru", "password": "1234"}
        )
        self.assertEqual(response.status_code, 400)

    def test_new_user(self):
        url = reverse("signup")
        response = self.client.post(
            url,
            {"username": "user2", "email": "test@mail.ru", "password": "superpassword"},
        )
        self.assertEqual(response.status_code, 201)

    def test_login_with_correct_password(self):
        url = reverse("login")
        response = self.client.post(url, {"username": "user1", "password": "abcde"})
        self.assertEqual(response.status_code, 200)

    def test_login_with_wrong_password(self):
        url = reverse("login")
        response = self.client.post(url, {"username": "user1", "password": "1234"})
        self.assertEqual(response.status_code, 400)

    def test_genres_list(self):
        """Simple test for genres list endpoint."""
        response = self.client.get(reverse("genres"))
        self.assertListEqual(
            response.data,
            [
                {
                    "id": 1,
                    "name": "genre_test_1",
                    "genre_icon_url": "http://storage.yandexcloud.net/game-interface-flows/icons/icon.png",
                },
                {
                    "id": 2,
                    "name": "genre_test_2",
                    "genre_icon_url": "http://storage.yandexcloud.net/game-interface-flows/icons/icon.png",
                },
            ],
        )
