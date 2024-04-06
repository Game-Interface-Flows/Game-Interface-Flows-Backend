from typing import List

from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import Paginator
from django.db.models import QuerySet

from apps.interface_flows_api.models import (Comment, Connection, Flow, Genre,
                                             Platform, Profile, Screen,
                                             ScreenVisualProperties)
from apps.interface_flows_api.repositories.repository import IRepository
from apps.interface_flows_api.serializers import FlowSerializer


class FlowRepository(IRepository):
    @staticmethod
    def get_flow_by_id(flow_id: int) -> Flow:
        try:
            flow = Flow.objects.get(id=flow_id)
            return flow
        except ObjectDoesNotExist:
            raise ObjectDoesNotExist

    def get_public_flows(
        self,
        sort: str = "date",
        order: str = "asc",
        genres: QuerySet[Genre] = None,
        platforms: QuerySet[Platform] = None,
    ) -> QuerySet[Flow]:
        """
        filter options: genres, platforms
        sort options: date, title, likes
        order options: asc or desc
        """
        flows = Flow.objects.filter(visibility="PB", status="VR")
        if genres:
            flows = flows.filter(genres__in=genres)
        if platforms:
            flows = flows.filter(platforms__in=platforms)
        order_option = self.get_order_option(sort, order)
        return flows.order_by(order_option)

    @staticmethod
    def get_flow_screens(flow: Flow) -> QuerySet[Screen]:
        return Screen.objects.filter(flow=flow)

    @staticmethod
    def get_connected_screens(screen: Screen) -> QuerySet[Screen]:
        direct_connections = Connection.objects.filter(screen_out=screen)
        directed_connected = Screen.objects.filter(
            connections_in__in=direct_connections
        )

        reverse_connections = Connection.objects.filter(
            screen_in=screen, bidirectional=True
        )

        reverse_connected = Screen.objects.filter(
            connections_out__in=reverse_connections
        )

        return directed_connected.union(reverse_connected)

    @staticmethod
    def add_get_screen_properties(width: int, height: int) -> ScreenVisualProperties:
        instance, created = ScreenVisualProperties.objects.get_or_create(
            width=width, height=height
        )
        return instance

    def add_flow(
        self, title: str, description: str, width: int, height: int, author: Profile
    ) -> Flow:
        screen_properties = self.add_get_screen_properties(width, height)
        data = {
            "title": title,
            "description": description,
        }
        serializer = FlowSerializer(data=data)
        if serializer.is_valid():
            serializer.save(author=author, screens_properties=screen_properties)
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
                screen_out=screen_out, screen_in=screen_in
            )

        except ObjectDoesNotExist:
            direct_connection = None

        try:
            reverse_connection = Connection.objects.get(
                screen_out=screen_in, screen_in=screen_out
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
