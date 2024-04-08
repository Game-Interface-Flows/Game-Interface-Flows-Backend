from django.urls import reverse
from rest_framework.test import APITestCase

from apps.interface_flows_api.models import Genre


class FlowsTests(APITestCase):
    def setUp(self):
        Genre.objects.create(name="genre_test_1")
        Genre.objects.create(name="genre_test_2")

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
                    "id": 1,
                    "name": "genre_test_2",
                    "genre_icon_url": "http://storage.yandexcloud.net/game-interface-flows/icons/icon.png",
                },
            ],
        )
