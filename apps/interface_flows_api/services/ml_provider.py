import os

import requests

from apps.interface_flows_api.exceptions import MLServicesUnavailableException


class MachineLearningProvider:
    ml_service_url = os.getenv("ML_SERVICE_URL")

    def get_direct_graph(self, frames):
        files_to_send = [
            ("frames", (file.name, file.open().read(), file.content_type))
            for file in frames
        ]
        try:
            response = requests.post(f"{self.ml_service_url}/flow", files=files_to_send)
            flow_graph = response.json()
            return flow_graph
        except requests.exceptions.RequestException as e:
            raise MLServicesUnavailableException(f"ML service call failed: {e}")
