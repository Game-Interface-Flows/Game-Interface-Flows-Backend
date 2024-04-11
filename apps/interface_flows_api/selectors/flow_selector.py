from typing import Iterable, List

from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist

from apps.interface_flows_api.exceptions import PrivateFlowException
from apps.interface_flows_api.models import (
    Connection,
    Flow,
    FlowStatus,
    FlowVisibility,
    Genre,
    Platform,
    Screen,
)
from apps.interface_flows_api.selectors.selector import Selector


class FlowSelector(Selector):
    """Flow Selector is designed for read-only operations."""

    flows_on_verify_limit = 1

    @staticmethod
    def get_genres_by_names(names: List[str] = None) -> Iterable[Genre]:
        if names is None or len(names) == 0:
            return Genre.objects.all()
        return Genre.objects.filter(name__in=names)

    @staticmethod
    def get_platforms_by_names(names: List[str] = None) -> Iterable[Platform]:
        if names is None or len(names) == 0:
            return Platform.objects.all()
        return Platform.objects.filter(name__in=names)

    @staticmethod
    def get_flow_by_id(flow_id: int, user: User = None) -> Flow:
        try:
            flow = Flow.objects.get(id=flow_id)
        except ObjectDoesNotExist:
            raise ObjectDoesNotExist
        if (
            flow.visibility == FlowVisibility.PRIVATE
            or flow.status == FlowStatus.ON_MODERATION
        ) and (user.id is None or user.profile != flow.author):
            raise PrivateFlowException
        return flow

    @staticmethod
    def get_my_flows(user: User) -> Iterable[Flow]:
        return Flow.objects.filter(author=user.profile)

    @staticmethod
    def get_liked_flows(user: User) -> Iterable[Flow]:
        return Flow.objects.filter(liked_by__user=user.profile)

    def if_user_reach_unverified_flows_limit(self, user: User) -> bool:
        flows = Flow.objects.filter(
            author=user.profile, status=FlowStatus.ON_MODERATION
        )
        return True if len(flows) >= self.flows_on_verify_limit else False

    def get_public_flows(
        self,
        sort: str = "date",
        order: str = "asc",
        genres: List[str] = None,
        platforms: List[str] = None,
    ) -> Iterable[Flow]:
        """
        filter options: genres, platforms
        sort options: date, title, likes
        order options: asc or desc
        """
        flows = Flow.objects.filter(
            visibility=FlowVisibility.PUBLIC, status=FlowStatus.VERIFIED
        )
        if genres:
            genres = self.get_genres_by_names(genres)
            flows = flows.filter(genres__in=genres)
        if platforms:
            platforms = self.get_platforms_by_names(platforms)
            flows = flows.filter(platforms__in=platforms)
        order_option = self.get_order_option(sort, order)
        return flows.order_by(order_option)

    @staticmethod
    def get_connected_screens(screen: Screen) -> Iterable[Screen]:
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


flow_selector = FlowSelector()
