import os

import requests


class MachineLearningProvider:
    ml_service_url = os.getenv("ML_SERVICE_URL")

    def get_direct_graph(self, frames):
        files_to_send = [
            ("frames", (file.name, file.file, file.content_type)) for file in frames
        ]
        response = requests.post(f"{self.ml_service_url}/flow", files=files_to_send)
        graph = response.json()
        return graph
