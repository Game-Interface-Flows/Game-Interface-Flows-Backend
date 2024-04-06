import enum
from abc import ABC


class IRepository(ABC):
    @staticmethod
    def get_order_option(sort_field: str, order: str):
        return sort_field if order == OrderOption.ascending.value else f"-{sort_field}"


class OrderOption(enum.Enum):
    ascending = "asc"
    descending = "desc"
