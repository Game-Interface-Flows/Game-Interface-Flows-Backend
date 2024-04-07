import enum
from abc import ABC


class Selector(ABC):
    """Selector is an abstract class which has common functions for filtering/sorting."""

    @staticmethod
    def get_order_option(sort_field: str, order: str) -> str:
        return sort_field if order == OrderOption.ascending.value else f"-{sort_field}"


class OrderOption(enum.Enum):
    ascending = "asc"
    descending = "desc"
