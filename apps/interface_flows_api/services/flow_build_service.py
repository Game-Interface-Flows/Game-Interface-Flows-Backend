from __future__ import annotations

import tempfile
from typing import Iterable, List

import cv2
import numpy as np
from django.core.exceptions import ObjectDoesNotExist
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import InMemoryUploadedFile

from apps.interface_flows_api.exceptions import (
    MLServicesException, MLServicesUnavailableException,
    UnverifiedFlowExistsException, VideoProcessingException)
from apps.interface_flows_api.models import (Connection, Flow, FlowStatus,
                                             Genre, Platform, Screen,
                                             ScreenVisualProperties, User)
from apps.interface_flows_api.selectors.flow_selector import flow_selector
from apps.interface_flows_api.selectors.selector import SelectionOption
from apps.interface_flows_api.services.ml_provider import ml_service_provider
from apps.interface_flows_api.utils.encoder import numpy_array_to_io
from apps.interface_flows_api.utils.resizer import resize_image


class FlowBuildService:
    MAX_TIME_BETWEEN_SCREENS = 100

    @staticmethod
    def cut_video_into_frames(video_file: InMemoryUploadedFile, interval: int = 3):
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
                total_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))

                frames = []
                for frame_index in range(0, total_frames, frame_interval):
                    video.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
                    success, frame = video.read()
                    if success:
                        frames.append(frame)
                video.release()
                return frames
        except Exception:
            raise VideoProcessingException

    @staticmethod
    def _get_screen_size(image: np.array) -> (int, int):
        height, width = image.shape[:2]
        return width, height

    @staticmethod
    def _np_to_image(
        image_np: np.array, image_format: str = "JPEG", filename: str = "default"
    ) -> ContentFile:
        buffered = numpy_array_to_io(image_np)
        buffered.seek(0)
        filename = f"{filename}.{image_format.lower()}"
        return ContentFile(buffered.read(), name=filename)

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

    @staticmethod
    def _get_filename_prefix(title: str) -> str:
        flow_num = len(flow_selector.get_flows_by_title(title)) + 1
        flow_num = "{:02d}".format(flow_num)
        prefix = f"{title}_{flow_num}"
        return prefix

    @staticmethod
    def _add_thumbnail(flow: Flow, image: InMemoryUploadedFile, prefix) -> Flow:
        buffed, f = resize_image(image)
        image = ContentFile(buffed.getvalue())
        image.name = f"{prefix}.{f}"
        flow.flow_thumbnail_url = image
        flow.save()
        return flow

    def _add_screen(self, flow: Flow, image: np.array, prefix: str, pid: int) -> Screen:
        screen_num = "{:02d}".format(pid)
        filename = f"{prefix}_{screen_num}"
        image = self._np_to_image(image_np=image, filename=filename)
        return Screen.objects.create(flow=flow, flow_screen_number=pid, image=image)

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
        video_file: InMemoryUploadedFile,
        user: User,
        thumbnail_file: InMemoryUploadedFile = None,
        source: str = None,
        interval: int = 1,
        platforms: List[Platform] = None,
        genres: List[Genre] = None,
    ) -> Flow:
        if flow_selector.if_user_reach_unverified_flows_limit(user):
            raise UnverifiedFlowExistsException

        try:
            frames = self.cut_video_into_frames(video_file, interval)
        except VideoProcessingException:
            raise VideoProcessingException

        try:
            predictions = ml_service_provider.get_direct_graph(
                frames, images_interval=interval
            )
        except MLServicesUnavailableException:
            raise MLServicesUnavailableException
        except MLServicesException:
            raise MLServicesUnavailableException

        width, height = self._get_screen_size(frames[0])
        screens_properties = self._add_get_screen_properties(width, height)
        prefix = self._get_filename_prefix(title)

        flow = Flow.objects.create(
            author=user.profile,
            title=title,
            source=source,
            screens_properties=screens_properties,
            status=FlowStatus.VERIFIED,
        )

        platforms = flow_selector.get_platforms_by_names(
            names=platforms, option=SelectionOption.nothing
        )
        flow.platforms.set(platforms)

        genres = flow_selector.get_genres_by_names(
            names=genres, option=SelectionOption.nothing
        )
        flow.genres.set(genres)

        if thumbnail_file is not None:
            self._add_thumbnail(flow=flow, image=thumbnail_file, prefix=prefix)

        previous_screen = None
        seen_screens_indices = set()

        for i, prediction in enumerate(predictions):
            if prediction.index not in seen_screens_indices:
                screen = self._add_screen(
                    flow=flow,
                    image=frames[prediction.index],
                    pid=prediction.index,
                    prefix=prefix,
                )
                seen_screens_indices.add(prediction.index)
            else:
                screen = Screen.objects.get(
                    flow=flow, flow_screen_number=prediction.index
                )
            if (
                i > 0
                and predictions[i].time_in - predictions[i - 1].time_out
                < self.MAX_TIME_BETWEEN_SCREENS
            ):
                self._add_screens_connection(
                    screen_out=previous_screen, screen_in=screen
                )

            previous_screen = screen

        self._build_graph(flow)

        return flow


flow_build_service = FlowBuildService()
