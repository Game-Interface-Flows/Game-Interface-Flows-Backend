import enum
from abc import ABC
from typing import Callable, Iterable, List, Optional, Type, Union

from django.db.models import Model


class SelectionOption(enum.Enum):
    all = "all"
    nothing = "nothing"


class OrderOption(enum.Enum):
    ascending = "asc"
    descending = "desc"


class Selector(ABC):
    """Selector is an abstract class which has common functions for filtering/sorting."""

    @staticmethod
    def get_order_option(sort_field: str, order: str) -> str:
        return sort_field if order == OrderOption.ascending.value else f"-{sort_field}"

    @staticmethod
    def get_items_by_names(
        model: Type[Model],
        names: List[str] = None,
        option: SelectionOption = SelectionOption.all,
    ) -> Iterable[Type[Model]]:
        if names is None or len(names) == 0:
            if option == SelectionOption.all:
                return model.objects.all()
            return model.objects.none()
        return model.objects.filter(name__in=names)


def model_binder(model: Type[Model]):
    def decorator(func: Callable):
        def wrapped_function(
            self, names: Optional[List[str]] = None, option: str = "all"
        ) -> Union[Iterable[Model], None]:
            return func(self, model, names, option)

        return wrapped_function

    return decorator
