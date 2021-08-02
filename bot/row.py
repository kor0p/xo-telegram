from __future__ import annotations

from typing import Union, Any, Iterable, Optional

from .const import Choice

RowItem = Union[int, Choice, 'Row']


def join(string: str, iterable: Iterable):
    return string.join(map(str, iterable))


class Row:
    __slots__ = ('value', 'size')

    value: list[Any, ...]
    size: int

    def __init__(self, value: Optional[Union[str, list[RowItem]]] = None, size: Optional[int] = None):
        if isinstance(value, str):
            value = list(value)
        self.value = value or []
        self.size = size or round(len(value) ** 0.5)

    def __contains__(self, key):
        return key in self.value

    def __getitem__(self, key: RowItem):
        if not isinstance(key, Choice):
            return self.value[key]

        result = self.value
        for dimension_value in key:
            result = result[dimension_value]
        return result

    def __setitem__(self, key: RowItem, item: Union[str, Row]):
        if not isinstance(key, Choice):
            self.value[key] = item
            return

        *getter_key, setter_key = list(key)
        value = self.value
        for get in getter_key:
            value = value[get]
        value[setter_key] = item

    def __repr__(self):
        return join('', self)

    def __len__(self):
        return self.size
