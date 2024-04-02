from typing import List

from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q, QuerySet

from apps.interface_flows_api.models import (Comment, Connection, Flow, Screen,
                                             Genre, Platform, Profile)
from apps.interface_flows_api.serializers import FlowSerializer


class FlowRepository:
    @staticmethod
    def get_flow_by_id(flow_id: int) -> Flow:
        try:
            flow = Flow.objects.get(id=flow_id)
            return flow
        except ObjectDoesNotExist:
            raise ObjectDoesNotExist

    @staticmethod
    def get_public_flows(
        sort: str = "date",
        order: str = "ASC",
        limit: int = 10,
        offset: int = 0,
        genres=None,
        platforms=None,
    ) -> QuerySet[Flow]:
        """
        filter options: genres, platforms
        order options: date, title, likes
        """
        flows = Flow.objects.filter(visibility="PB", status="VR")
        # if genres:
        #    flows = flows.filter(genres__in=genres)
        # if platforms:
        #    flows = flows.filter(platforms__in=platforms)
        order_option = sort if order == "ASC" else f"-{sort}"
        return flows.order_by(order_option)[offset:limit]

    @staticmethod
    def get_flow_screens(flow: Flow) -> QuerySet[Screen]:
        return Screen.objects.filter(flow=flow)

    @staticmethod
    def get_connected_screens(screen: Screen) -> QuerySet[Screen]:
        direct_connections = Connection.objects.filter(screen_out=screen)
        directed_connected = Screen.objects.filter(connections_in__in=direct_connections)

        reverse_connections = Connection.objects.filter(
            screen_in=screen, bidirectional=True
        )

        reverse_connected = Screen.objects.filter(
            connections_out__in=reverse_connections
        )

        return directed_connected.union(reverse_connected)

    @staticmethod
    def add_flow(title: str, description: str, width: int, height: int, author: Profile) -> Flow:
        data = {
            "title": title,
            "description": description,
            "screens_height": height,
            "screens_width": width,
        }
        serializer = FlowSerializer(data=data)
        if serializer.is_valid():
            serializer.save(author=author)
            return serializer.instance
        return serializer.errors

    @staticmethod
    def add_screen(flow: Flow, number: int, image) -> Screen:
        screen = Screen()
        screen.flow = flow
        screen.flow_screen_number = number
        screen.image = image
        screen.save()
        return screen

    @staticmethod
    def get_screen(flow: Flow, flow_screen_number: int) -> Screen:
        return Screen.objects.get(flow=flow, flow_screen_number=flow_screen_number)

    @staticmethod
    def update_screen_pos(screen: Screen, pos_x: float, pos_y: float) -> Screen:
        screen.position_x = pos_x
        screen.position_y = pos_y
        screen.save()
        return screen

    @staticmethod
    def add_connection(screen_out: Screen, screen_in: Screen) -> Connection:
        try:
            direct_connection = Connection.objects.get(
                Q(screen_out=screen_out) & Q(screen_in=screen_in)
            )
        except ObjectDoesNotExist:
            direct_connection = None

        try:
            reverse_connection = Connection.objects.get(
                Q(screen_out=screen_in) & Q(screen_in=screen_out)
            )
        except ObjectDoesNotExist:
            reverse_connection = None

        if direct_connection:
            return direct_connection

        if reverse_connection:
            reverse_connection.bidirectional = True
            reverse_connection.save()
            return reverse_connection

        connection = Connection()
        connection.screen_out = screen_out
        connection.screen_in = screen_in
        connection.save()

        return connection

    @staticmethod
    def add_comment(comment_text: str, flow: Flow, author: Profile) -> Comment:
        comment = Comment()
        comment.flow = flow
        comment.author = author
        comment.text = comment_text
        comment.save()
        return comment

    @staticmethod
    def get_genres_by_names(names: List[str] = None) -> QuerySet[Genre]:
        if names is None:
            return Genre.objects.all()
        return Genre.objects.filter(name__in=names)

    @staticmethod
    def get_platforms_by_names(names: List[str] = None) -> QuerySet[Platform]:
        if names is None:
            return Platform.objects.all()
        return Platform.objects.filter(name__in=names)


flow_repository = FlowRepository()
