from typing import Set

from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q

from apps.interface_flows_api.models import Connection, Flow, Frame
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
        sort: str = "date", order: str = "ASC", limit: int = 10, offset: int = 0
    ):
        """
        order options: date, title, likes
        """
        order_option = sort if order == "ASC" else f"-{sort}"
        return Flow.objects.filter(visibility="PB", status="VR").order_by(order_option)[
            offset:limit
        ]

    @staticmethod
    def get_available_flows():
        return Flow.objects.all()

    @staticmethod
    def get_all_flow_frames(flow: Flow):
        return Frame.objects.filter(flow=flow)

    @staticmethod
    def get_all_frame_connected_frames(frame: Frame) -> Set[Frame]:
        direct_connections = Connection.objects.filter(frame_out=frame)
        directed_connected = Frame.objects.filter(connections_in__in=direct_connections)

        reverse_connections = Connection.objects.filter(
            Q(frame_in=frame) & Q(bidirectional=True)
        )
        reverse_connected = Frame.objects.filter(
            connections_out__in=reverse_connections
        )

        return directed_connected | reverse_connected

    @staticmethod
    def add_flow(data, author) -> Flow:
        serializer = FlowSerializer(data=data)
        if serializer.is_valid():
            serializer.save(author=author)
            return serializer.instance
        return serializer.errors

    @staticmethod
    def add_frame(flow: Flow, image) -> Frame:
        frame = Frame()
        frame.flow = flow
        frame.frame = image
        frame.save()
        return frame

    @staticmethod
    def update_frame_pos(frame: Frame, pos_x: float, pos_y: float) -> Frame:
        frame.position_x = pos_x
        frame.position_y = pos_y
        frame.save()
        return frame

    @staticmethod
    def add_connection(frame_out: Frame, frame_in: Frame) -> Connection:
        direct_connection = Connection.objects.filter(
            Q(connections_out=frame_out) & Q(connections_in=frame_in)
        )
        reverse_connection = Connection.objects.filter(
            Q(connections_out=frame_in) & Q(connections_in=frame_out)
        )

        if direct_connection:
            return direct_connection

        if reverse_connection:
            reverse_connection.bidirectional = True
            reverse_connection.save()
            return reverse_connection

        connection = Connection()
        connection.frame_out = frame_out
        connection.frame_in = frame_in
        connection.save()

        return connection
