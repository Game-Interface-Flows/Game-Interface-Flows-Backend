from __future__ import annotations

import tempfile
from io import BytesIO
from typing import Iterable, List

import cv2
from django.core.exceptions import ObjectDoesNotExist
from django.core.files.uploadedfile import (InMemoryUploadedFile,
                                            SimpleUploadedFile)
from PIL import Image

from apps.interface_flows_api.exceptions import (
    MLServicesUnavailableException, UnverifiedFlowExistsException,
    VideoProcessingException)
from apps.interface_flows_api.models import (Connection, Flow, Genre, Platform,
                                             Screen, ScreenVisualProperties,
                                             User)
from apps.interface_flows_api.selectors.flow_selector import flow_selector
from apps.interface_flows_api.selectors.selector import SelectionOption
from apps.interface_flows_api.services.ml_provider import ml_service_provider


class FlowBuildService:
    MAX_TIME_BETWEEN_SCREENS = 100

    @staticmethod
    def cut_video_into_frames(video_file, interval: int = 3):
        try:
            with tempfile.NamedTemporaryFile(
                suffix=".mp4", delete=True
            ) as temp_video_file:
                for chunk in video_file.chunks():
                    temp_video_file.write(chunk)
                temp_video_file.flush()

                video = cv2.VideoCapture(temp_video_file.name)
                fps = video.get(cv2.CAP_PROP_FPS)
                frame_interval = int(fps) * interval

                frames = []
                count = 0
                success, frame = video.read()
                while success:
                    if count % frame_interval == 0:
                        image = Image.fromarray(frame)
                        img_byte_array = BytesIO()
                        image.save(img_byte_array, format="JPEG")
                        img_byte_array.seek(0)
                        file_like_object = SimpleUploadedFile(
                            f"image{count}.jpg", img_byte_array.getvalue()
                        )
                        frames.append(file_like_object)
                    count += 1
                    success, frame = video.read()
                video.release()
                return frames
        except Exception:
            raise VideoProcessingException

    @staticmethod
    def _get_screen_size(image_bytes: bytes) -> (int, int):
        image = Image.open(image_bytes)
        width, height = image.size
        return width, height

    @staticmethod
    def _add_screen(flow: Flow, image: InMemoryUploadedFile) -> Screen:
        flow_num = len(flow_selector.get_flows_by_title(flow.title))
        f_flow_num = "{:02d}".format(flow_num)
        screen_num = len(flow_selector.get_flow_screens(flow)) + 1
        f_screen_num = "{:02d}".format(screen_num)
        ext = image.name.split(".")[-1]
        image.name = f"{flow.title}_{f_flow_num}_{f_screen_num}.{ext}"
        return Screen.objects.create(
            flow=flow, flow_screen_number=screen_num, image=image
        )

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

    def _compute_screen_position(
        self, visited: set, graph: dict, node: Screen, x: int, y: int
    ) -> int | None:
        if node not in visited:
            self._update_flow_screen_pos(node, x, y)
            visited.add(node)
            i = 0
            for neighbour in graph[node]:
                next_x = x + 1
                next_y = y + 1 if i > 0 else y
                dy = self._compute_screen_position(
                    visited, graph, neighbour, next_x, next_y
                )
                if dy is None:
                    continue
                y = dy
                i += 1
            del graph[node]
            return y
        return None

    def _build_graph(self, flow: Flow) -> Iterable[Screen]:
        screens = flow_selector.get_flow_screens(flow)
        graph = {}
        for screen in screens:
            graph[screen] = flow_selector.get_connected_screens(screen)
        visited = set()
        y = 0
        while len(graph) != 0:
            current_node = max(graph, key=lambda x: len(graph[x]))
            y = self._compute_screen_position(visited, graph, current_node, 0, y)
            y += 1
        return screens

    def create_new_flow(
        self,
        title: str,
        frames: List[bytes],
        user: User,
        flow_thumbnail_url: InMemoryUploadedFile = None,
        description: str = None,
        interval: int = 1,
        platforms: List[Platform] = None,
        genres: List[Genre] = None,
    ) -> Flow:
        if flow_selector.if_user_reach_unverified_flows_limit(user):
            raise UnverifiedFlowExistsException

        try:
            predictions = ml_service_provider.get_direct_graph(
                frames, images_interval=interval
            )
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

        platforms = flow_selector.get_platforms_by_names(
            names=platforms, option=SelectionOption.nothing
        )
        flow.platforms.set(platforms)

        genres = flow_selector.get_genres_by_names(
            names=genres, option=SelectionOption.nothing
        )
        flow.genres.set(genres)

        if flow_thumbnail_url is not None:
            flow.flow_thumbnail_url = flow_thumbnail_url
            flow.save()

        previous_screen = None
        seen_screens_indices = set()

        for i, prediction in enumerate(predictions):
            if prediction["index"] not in seen_screens_indices:
                screen = self._add_screen(
                    flow=flow,
                    image=frames[prediction["index"]],
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

        self._build_graph(flow)

        return flow


flow_build_service = FlowBuildService()
