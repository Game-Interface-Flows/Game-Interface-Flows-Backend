from django.core.exceptions import ObjectDoesNotExist
from PIL import Image

import apps.interface_flows_api.config as config
from apps.interface_flows_api.exceptions import (
    MLServicesUnavailableException, PrivateFlowException)
from apps.interface_flows_api.repositories.flow_repository import \
    FlowRepository
from apps.interface_flows_api.services.auth_service import AuthService
from apps.interface_flows_api.services.ml_provider import \
    MachineLearningProvider


class FlowService:
    repository = FlowRepository()
    ml_provider = MachineLearningProvider()

    @staticmethod
    def _get_frame_size(image_file):
        image = Image.open(image_file)
        width, height = image.size
        return width, height

    def _compute_flow_frames_positions(self, flow) -> None:
        frames = self.repository.get_all_flow_frames(flow)
        graph = {}

        for frame in frames:
            graph[frame] = self.repository.get_all_frame_connected_frames(frame)

        height = []
        stack = [(max(graph, key=lambda x: len(graph[x])), 0)]
        visited = set()

        while len(stack) > 0:
            current_frame, pos_x = stack.pop()

            if len(height) <= pos_x:
                height.append(0)

            pos_y = height[pos_x]
            height[pos_x] += 1

            self.repository.update_frame_pos(current_frame, pos_x, pos_y)

            visited.add(current_frame)
            connected_frames = graph[current_frame]

            for frame in connected_frames:
                if frame not in visited:
                    stack.append((frame, pos_x + 1))

            if len(stack) == 0:
                not_visited = list(visited - set(graph.keys()))
                if len(not_visited) == 0:
                    break
                stack.append((graph[not_visited[0]], 0))

    def get_flow_by_id(self, flow_id: int, user=None):
        profile = AuthService().get_profile(user)
        try:
            flow = self.repository.get_flow_by_id(flow_id=flow_id)
        except ObjectDoesNotExist:
            raise ObjectDoesNotExist
        if flow.is_public_and_verified is False and profile != flow.author:
            raise PrivateFlowException
        return flow

    def get_public_flows(
        self, sort: str = "date", order: str = "ASC", limit: int = 10, offset: int = 0
    ):
        return self.repository.get_public_flows(sort, order, limit, offset)

    def get_available_flows(self):
        return self.repository.get_available_flows()

    def create_new_flow(
        self,
        title: str,
        description: str,
        frames=None,
        user=None,
    ):
        profile = AuthService().get_profile(user)
        width, height = self._get_frame_size(frames[0])
        data = {
            "title": title,
            "description": description,
            "height": height,
            "width": width,
        }
        flow = self.repository.add_flow(data, profile)

        try:
            predictions = self.ml_provider.get_direct_graph(frames)
        except MLServicesUnavailableException:
            raise MLServicesUnavailableException

        previous_frame = None

        for i, prediction in enumerate(predictions):
            frame = self.repository.add_frame(
                flow=flow, image=frames[prediction["index"]]
            )
            if (
                i > 0
                and predictions[i]["time_out"] - predictions[i - 1]["time_in"]
                < config.MAX_TIME_BETWEEN_SCREENS
            ):
                self.repository.add_connection(frame_out=previous_frame, frame_in=frame)

            previous_frame = frame

        self._compute_flow_frames_positions(flow)

        return flow

    def comment_flow(self, flow_id: int, user, text: str):
        try:
            flow = self.repository.get_flow_by_id(flow_id=flow_id)
        except ObjectDoesNotExist:
            raise ObjectDoesNotExist
        profile = AuthService().get_profile(user)
        return self.repository.add_comment(text, flow, profile)
