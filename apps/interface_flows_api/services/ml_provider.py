import base64
import json
import os
from dataclasses import dataclass
from typing import List

import numpy as np
import requests

from apps.interface_flows_api.exceptions import (
    MLServicesException, MLServicesUnavailableException)
from apps.interface_flows_api.utils.encoder import numpy_array_to_io


@dataclass
class MachineLearningServicePrediction:
    index: int
    time_in: int
    time_out: int


class MachineLearningServiceProvider:
    def __init__(self, host: str, port: str):
        self.ml_service_url = f"{host}:{port}"

    @staticmethod
    def numpy_array_to_base64(image_np: np.array) -> str:
        buffered = numpy_array_to_io(image_np)
        return base64.b64encode(buffered.getvalue()).decode("utf-8")

    def get_direct_graph(
        self, images, images_interval: int = 1
    ) -> List[MachineLearningServicePrediction]:
        encoded_images = [self.numpy_array_to_base64(image) for image in images]
        data = json.dumps(
            {"encoded_images": encoded_images, "images_interval": images_interval}
        )
        try:
            response = requests.post(
                f"{self.ml_service_url}/flow",
                data=data,
                headers={"Content-Type": "application/json"},
            )
            if response.status_code != 200:
                print(response)
                raise MLServicesException
            predictions = response.json()
            predictions = [
                MachineLearningServicePrediction(**prediction)
                for prediction in predictions
            ]
            return predictions
        except requests.exceptions.RequestException as e:
            print(e)
            raise MLServicesUnavailableException(f"ML service call failed: {e}")


ml_service_provider = MachineLearningServiceProvider(
    host=os.getenv("ML_SERVICE_HOST"), port=os.getenv("ML_SERVICE_PORT")
)
