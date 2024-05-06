import json
import os
from io import BytesIO
from typing import List

import requests
from django.core.files.uploadedfile import (SimpleUploadedFile,
                                            TemporaryUploadedFile)

from apps.interface_flows_api.exceptions import MLServicesUnavailableException


class MachineLearningServiceProvider:
    def __init__(self, host: str, port: str):
        self.ml_service_url = f"{host}:{port}"

    def get_direct_graph(self, images, images_interval: int = 1) -> json:
        files = [
            ("images", (file.name, file.open().read(), file.content_type))
            for file in images
        ]
        try:
            response = requests.post(
                f"{self.ml_service_url}/flow",
                files=files,
                json={images_interval: images_interval},
            )
            flow_graph = response.json()
            return flow_graph
        except requests.exceptions.RequestException as e:
            raise MLServicesUnavailableException(f"ML service call failed: {e}")


ml_service_provider = MachineLearningServiceProvider(
    host=os.getenv("ML_SERVICE_HOST"), port=os.getenv("ML_SERVICE_PORT")
)
