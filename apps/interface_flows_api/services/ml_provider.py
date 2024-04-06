import json
import os
from typing import List

import requests
from django.core.files.uploadedfile import TemporaryUploadedFile

from apps.interface_flows_api.exceptions import MLServicesUnavailableException


class MachineLearningServiceProvider:
    def __init__(self, url: str):
        self.ml_service_url = url

    def get_direct_graph(self, frames: List[TemporaryUploadedFile]) -> json:
        frames = [
            ("frames", (file.name, file.open().read(), file.content_type))
            for file in frames
        ]
        try:
            response = requests.post(f"{self.ml_service_url}/flow", files=frames)
            flow_graph = response.json()
            return flow_graph
        except requests.exceptions.RequestException as e:
            raise MLServicesUnavailableException(f"ML service call failed: {e}")


ml_service_provider = MachineLearningServiceProvider(os.getenv("ML_SERVICE_URL"))
