import json
import random
from enum import Enum
from typing import Union, Literal, Sequence, Iterator

from telebot.types import User

from .const import GAME_SIZES, SIGNS_TYPE, CONSTS, Choice, GameEndAction
from .user import TGUser

JSON_COMMON_DATA = Union[list, int, str]


def get_random_list_size() -> Iterator[int]:
    while True:
        yield random.choice(GAME_SIZES)


random_list_size = get_random_list_size()


def resolve_text(queue: Union[bool, int], data: Union[str, Sequence]) -> Sequence:
    if isinstance(data, str):
        data = (data, '')
    if queue:
        return tuple(reversed(data))
    return data


def get_markdown_user_url(user: Union[TGUser, User]) -> str:
    return f'[{user.first_name}](tg://user?id={user.id})'


def _map_callback_data(row: Union[JSON_COMMON_DATA, Choice, Enum]) -> JSON_COMMON_DATA:
    if isinstance(row, Choice):
        return list(row.to_tuple())
    if isinstance(row, Enum):
        return row.name
    return row


class callback(Enum):
    text__reset_start = ''
    text__start = SIGNS_TYPE
    text__game = Union[Choice, SIGNS_TYPE]
    start = int
    game = Union[Choice, SIGNS_TYPE, Literal[CONSTS.LOCK]]
    confirm_end = list[GameEndAction, Choice]

    def create(self, *data: Union[JSON_COMMON_DATA, Choice, Enum]) -> str:
        return json.dumps(
            {'type': self.name}
            if data is None
            else {'type': self.name, 'data': [_map_callback_data(row) for row in data]},
            separators=(',', ':'),
        )
