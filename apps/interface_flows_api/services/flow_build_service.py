from typing import Iterable, List

from django.core.exceptions import ObjectDoesNotExist
from PIL import Image

from apps.interface_flows_api.exceptions import MLServicesUnavailableException
from apps.interface_flows_api.models import (Connection, Flow, Screen,
                                             ScreenVisualProperties, User)
from apps.interface_flows_api.selectors.flow_selector import flow_selector
from apps.interface_flows_api.services.ml_provider import ml_service_provider


class FlowBuildService:
    MAX_TIME_BETWEEN_SCREENS = 100

    @staticmethod
    def _get_screen_size(image_bytes: bytes) -> (int, int):
        image = Image.open(image_bytes)
        width, height = image.size
        return width, height

    @staticmethod
    def _add_screen(flow: Flow, number: int, image) -> Screen:
        return Screen.objects.create(flow=flow, flow_screen_number=number, image=image)

    @staticmethod
    def _update_flow_screen_pos(screen: Screen, x: int, y: int) -> None:
        screen.position_x = x
        screen.position_y = y
        screen.save()

    @staticmethod
    def _add_get_screen_properties(width: int, height: int) -> ScreenVisualProperties:
        properties, created = ScreenVisualProperties.objects.get_or_create(
            width=width, height=height
        )
        return properties

    @staticmethod
    def _add_screens_connection(screen_out: Screen, screen_in: Screen) -> Connection:
        try:
            direct_connection = Connection.objects.get(
                screen_out=screen_out, screen_in=screen_in
            )
            return direct_connection
        except ObjectDoesNotExist:
            pass

        try:
            reverse_connection = Connection.objects.get(
                screen_out=screen_in, screen_in=screen_out
            )
            reverse_connection.bidirectional = True
            reverse_connection.save()
            return reverse_connection
        except ObjectDoesNotExist:
            pass

        return Connection.objects.create(screen_out=screen_out, screen_in=screen_in)

    def _build_graph(
        self, visited: set, graph: dict, node: Screen, x: int, y: int
    ) -> int | None:
        if node not in visited:
            self._update_flow_screen_pos(node, x, y)
            visited.add(node)
            i = 0
            for neighbour in graph[node]:
                next_x = x + 1
                next_y = y + 1 if i > 0 else y
                dy = self._build_graph(visited, graph, neighbour, next_x, next_y)
                if dy is None:
                    continue
                y = dy
                i += 1
            del graph[node]
            return y
        return None

    def _compute_flow_screens_positions(self, flow: Flow) -> Iterable[Screen]:
        screens = Screen.objects.filter(flow=flow)
        graph = {}

        for screen in screens:
            graph[screen] = flow_selector.get_connected_screens(screen)

        visited = set()
        y = 0

        while len(graph) != 0:
            current_node = max(graph, key=lambda x: len(graph[x]))
            y = self._build_graph(visited, graph, current_node, 0, y)
            y += 1

        return screens

    def create_new_flow(
        self, title: str, frames: List[bytes], user: User, description: str = None
    ) -> Flow:
        try:
            predictions = ml_service_provider.get_direct_graph(frames)
        except MLServicesUnavailableException:
            raise MLServicesUnavailableException

        width, height = self._get_screen_size(frames[0])
        screens_properties = self._add_get_screen_properties(width, height)

        flow = Flow.objects.create(
            author=user.profile,
            title=title,
            description=description,
            screens_properties=screens_properties,
        )

        previous_screen = None
        seen_screens_indices = set()

        for i, prediction in enumerate(predictions):
            if prediction["index"] not in seen_screens_indices:
                screen = self._add_screen(
                    flow=flow,
                    image=frames[prediction["index"]],
                    number=prediction["index"],
                )
                seen_screens_indices.add(prediction["index"])
            else:
                screen = Screen.objects.get(
                    flow=flow, flow_screen_number=prediction["index"]
                )
            if (
                i > 0
                and predictions[i]["time_in"] - predictions[i - 1]["time_out"]
                < self.MAX_TIME_BETWEEN_SCREENS
            ):
                self._add_screens_connection(
                    screen_out=previous_screen, screen_in=screen
                )

            previous_screen = screen

        self._compute_flow_screens_positions(flow)

        return flow


flow_build_service = FlowBuildService()