from typing import List

from django.core.exceptions import ObjectDoesNotExist
from PIL import Image

import apps.interface_flows_api.config as config
from apps.interface_flows_api.exceptions import (
    MLServicesUnavailableException, PrivateFlowException)
from apps.interface_flows_api.models import Comment, Flow, Screen, User
from apps.interface_flows_api.repositories.flow_repository import \
    flow_repository
from apps.interface_flows_api.services.auth_service import auth_service
from apps.interface_flows_api.services.ml_provider import ml_service_provider


class FlowService:
    def __init__(self, repository):
        self.repository = repository

    @staticmethod
    def _get_screen_size(image_bytes: bytes) -> (int, int):
        image = Image.open(image_bytes)
        width, height = image.size
        return width, height

    def _dfs(self, visited: set, graph: dict, node: Screen, x: int, y: int):
        if node not in visited:
            self.repository.update_screen_pos(node, x, y)
            visited.add(node)
            i = 0
            for neighbour in graph[node]:
                next_x = x + 1
                next_y = y + 1 if i > 0 else y
                dy = self._dfs(visited, graph, neighbour, next_x, next_y)
                if dy is None:
                    continue
                y = dy
                i += 1
            del graph[node]
            return y
        return None

    def _compute_flow_screens_positions(self, flow) -> List[Screen]:
        screens = self.repository.get_flow_screens(flow)
        graph = {}

        for screen in screens:
            graph[screen] = self.repository.get_connected_screens(screen)

        visited = set()
        y = 0

        while len(graph) != 0:
            current_node = max(graph, key=lambda x: len(graph[x]))
            y = self._dfs(visited, graph, current_node, 0, y)
            y += 1

        return screens

    def get_flow_by_id(self, flow_id: int, user: User = None) -> Flow:
        profile = auth_service.get_profile(user)
        try:
            flow = self.repository.get_flow_by_id(flow_id=flow_id)
        except ObjectDoesNotExist:
            raise ObjectDoesNotExist
        if flow.is_public_and_verified is False and profile != flow.author:
            raise PrivateFlowException
        return flow

    def get_public_flows(
        self,
        sort: str = "date",
        order: str = "ASC",
        limit: int = 10,
        offset: int = 0,
        genres: List[str] = None,
        platforms: List[str] = None,
    ) -> List[Flow]:
        genres = self.repository.get_genres_by_names(genres)
        platforms = self.repository.get_platforms_by_names(platforms)
        return self.repository.get_public_flows(
            sort, order, limit, offset, genres, platforms
        )

    def create_new_flow(
        self,
        title: str,
        description: str,
        frames: List[bytes],
        user: User,
    ) -> Flow:
        profile = auth_service.get_profile(user)
        width, height = self._get_screen_size(frames[0])
        print(width, height)
        flow = self.repository.add_flow(title, description, width, height, profile)

        try:
            predictions = ml_service_provider.get_direct_graph(frames)
        except MLServicesUnavailableException:
            raise MLServicesUnavailableException

        previous_screen = None
        seen_screens_indices = set()

        for i, prediction in enumerate(predictions):
            if prediction["index"] not in seen_screens_indices:
                screen = self.repository.add_screen(
                    flow=flow,
                    image=frames[prediction["index"]],
                    number=prediction["index"],
                )
                seen_screens_indices.add(prediction["index"])
            else:
                screen = self.repository.get_screen(flow, prediction["index"])
            if (
                i > 0
                and predictions[i]["time_in"] - predictions[i - 1]["time_out"]
                < config.MAX_TIME_BETWEEN_SCREENS
            ):
                self.repository.add_connection(
                    screen_out=previous_screen, screen_in=screen
                )

            previous_screen = screen

        self._compute_flow_screens_positions(flow)

        return flow

    def comment_flow(self, flow_id: int, user: User, text: str) -> Comment:
        try:
            flow = self.repository.get_flow_by_id(flow_id=flow_id)
        except ObjectDoesNotExist:
            raise ObjectDoesNotExist
        profile = auth_service.get_profile(user)
        return self.repository.add_comment(text, flow, profile)


flow_service = FlowService(flow_repository)