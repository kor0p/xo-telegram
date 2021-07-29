import json
import random
from enum import Enum
from typing import Union, Literal, Sequence, Iterator

from telebot.types import User

from .const import ALL_AVAILABLE_ACTUAL_GAME_SIZES, CONSTS, Choice, GameEndAction, GameSigns
from .user import TGUser

JSON_COMMON_DATA = Union[list, int, str]


def get_random_list_size() -> Iterator[int]:
    while True:
        yield random.choice(ALL_AVAILABLE_ACTUAL_GAME_SIZES)


def get_random_players_count(max_players) -> int:
    return random.randint(2, max(max_players - 1, 2))


random_list_size = get_random_list_size()


def resolve_text(queue: Union[bool, int], data: Union[str, Sequence]) -> Sequence:
    if isinstance(data, str):
        data = (data, '')
    if queue:
        return tuple(reversed(data))
    return data


def get_markdown_user_url(user: Union[TGUser, User]) -> str:
    if user.username:
        return f'[{user.first_name}](https://t.me/{user.username})'
    return f'[{user.first_name}](tg://user?id={user.id})'


def _map_callback_data(row: Union[JSON_COMMON_DATA, Choice, Enum]) -> JSON_COMMON_DATA:
    if isinstance(row, Choice):
        return list(row.to_tuple())
    if isinstance(row, Enum):
        return row.name
    return row


class ChooseSize(int):
    pass


class ChoosePlayersCount(int):
    pass


class callback(Enum):
    text__reset_start = ''
    text__start = GameSigns
    text__game = Union[Choice, GameSigns]
    start_size = ChooseSize
    start_players_count = ChoosePlayersCount
    game = Union[Choice, GameSigns, Literal[CONSTS.LOCK]]
    confirm_end = list[GameEndAction, Choice]

    def create(self, *data: Union[JSON_COMMON_DATA, Choice, Enum]) -> str:
        result_data = dict(type=self.name, data=[_map_callback_data(row) for row in data])
        return json.dumps(result_data, separators=(',', ':'))
