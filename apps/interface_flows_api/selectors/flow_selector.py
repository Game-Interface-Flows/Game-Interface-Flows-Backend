from typing import Iterable, List, Type

from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Model

from apps.interface_flows_api.exceptions import PrivateFlowException
from apps.interface_flows_api.models import (Connection, Flow, FlowStatus,
                                             FlowVisibility, Genre, Platform,
                                             Screen)
from apps.interface_flows_api.selectors.selector import (SelectionOption,
                                                         Selector,
                                                         model_binder)


class FlowSelector(Selector):
    """Flow Selector is designed for read-only operations."""

    flows_on_verify_limit = 100

    @model_binder(Genre)
    def get_genres_by_names(
        self,
        model: Type[Model],
        names: List[str] = None,
        option: SelectionOption = SelectionOption.all,
    ) -> Iterable[Genre]:
        return self.get_items_by_names(model, names, option)

    @model_binder(Platform)
    def get_platforms_by_names(
        self,
        model: Type,
        names: List[str] = None,
        option: SelectionOption = SelectionOption.all,
    ) -> Iterable[Platform]:
        return self.get_items_by_names(model, names, option)

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

    @staticmethod
    def get_flows_by_title(title: str) -> Iterable[Flow]:
        return Flow.objects.filter(title=title)

    @staticmethod
    def get_flow_screens(flow: Flow) -> Iterable[Screen]:
        return Screen.objects.filter(flow=flow)

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
            flows = flows.filter(genres__in=genres).distinct()
        if platforms:
            platforms = self.get_platforms_by_names(platforms)
            flows = flows.filter(platforms__in=platforms).distinct()
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
