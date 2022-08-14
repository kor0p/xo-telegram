import json
import random
from enum import Enum
from typing import Union, Literal, Iterator

from telebot.types import User

from .const import ALL_AVAILABLE_ACTUAL_GAME_SIZES, HOW_MANY_TO_WIN, CONSTS, Choice, GameEndAction, GameSigns
from .user import TGUser

JSON_COMMON_DATA = Union[list, int, str]


def get_random_list_size() -> Iterator[int]:
    while True:
        yield random.choice(ALL_AVAILABLE_ACTUAL_GAME_SIZES)


def get_random_players_count(size) -> int:
    all_possible_players_counts = HOW_MANY_TO_WIN[size].keys()
    return random.randint(min(all_possible_players_counts), max(all_possible_players_counts))


random_list_size = get_random_list_size()


def make_html_user_url(user: Union[TGUser, User]) -> str:
    return f'<a href="tg://user?id={user.id}">{user.first_name}</a>'


class InvalidGameConfigError(Exception):
    pass


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
