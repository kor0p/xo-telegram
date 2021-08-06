from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable, Optional


class URLS:
    ROBOT_START = 'https://t.me/m0xbot?start={utm_ref}'
    DONATE = 'https://send.monobank.ua/zEuxNoaWc'
    ULTIMATE_TIC_TAC_TOE = 'https://mathwithbaddrawings.com/2013/06/16/ultimate-tic-tac-toe/'


HOW_MANY_TO_WIN = {
    3: {2: 3},
    5: {2: 4, 3: 4},
    6: {2: 4, 3: 4, 4: 3},
    7: {2: 5, 3: 4, 4: 4, 5: 3},
    8: {2: 5, 3: 4, 4: 4, 5: 4, 6: 3},
    # big boards
    4: {2: 2},
    9: {2: 3, 3: 3, 4: 3},
    16: {2: 4, 3: 4, 4: 3, 5: 3, 6: 3},
}

POSSIBLE_SIZES_FOR_PLAYERS = {
    i: tuple(size for size, players_to_win_count in HOW_MANY_TO_WIN.items() if i in players_to_win_count)
    for i in range(2, 7)
}


BIG_GAME_SIZES = (4, 9, 16)
SMALL_GAME_SIZES = (3, 5, 6, 7, 8)
ALL_AVAILABLE_ACTUAL_GAME_SIZES = (*SMALL_GAME_SIZES, *(s ** 0.5 for s in BIG_GAME_SIZES))
GAME_SIZES: tuple[int, ...] = (*BIG_GAME_SIZES, *SMALL_GAME_SIZES)


class CONSTS:
    ALL_GAMES_SIGNS = '❌⭕🐵🌝🤓💀' '✖🔴🙈🌚😎👽'
    DEFAULT_GAMES_SIGNS = '❌⭕' '✖🔴'
    SUPER_ADMIN_USER_ID = 320063227
    LOCK = 'LOCK'
    BOT_USERNAME = 'm0xbot'
    EMPTY_CELL = '⬜'
    INVERTED_EMPTY_CELL = '◻'
    TIME = '⏳'
    WIN = '🏆'
    LOSE = '☠️'
    TURN = ' 👈'
    ROBOT = '🤖'


class GameType(Enum):
    ROBOT = 'ROBOT'
    USER = 'USER'


class GameState(Enum):
    GAME = 'GAME'
    END = 'END'  # WIN
    TIE = 'TIE'
    GIVE_UP = 'GIVE_UP'


class GameEndAction(Enum):
    TIE = 'TIE'
    GIVE_UP = 'GIVE_UP'
    CONFIRM = 'CONFIRM'
    CANCEL = 'CANCEL'


class ActionType(Enum):
    GAME = 'GAME'
    TIE = 'TIE'
    GIVE_UP = 'GIVE_UP'
    END = 'END'  # WIN or TIE


CHOICE_NULL = -1


@dataclass
class Choice:
    x: int = CHOICE_NULL
    y: int = CHOICE_NULL
    a: int = CHOICE_NULL
    b: int = CHOICE_NULL

    def __post_init__(self):
        if isinstance(self.x, Iterable):
            self.__init__(*self.x)

    def to_tuple(self):
        return self.x, self.y, self.a, self.b

    def __iter__(self):
        for key in self.to_tuple():
            if key != CHOICE_NULL:
                yield key

    def __getitem__(self, key):
        return self.to_tuple()[key]

    def __len__(self):
        return len(tuple(iter(self)))

    def is_inner(self):
        return self.a == CHOICE_NULL

    def get_outer(self):
        return Choice(self.a, self.b)

    def is_outer(self):
        return self.x == CHOICE_NULL


class GameSigns(list):
    DEFAULT: GameSigns
    inverted_sings: list[str]

    def __init__(self, signs: Optional[list[str, ...]] = None, length: int = None):
        if signs is None:
            signs = list(CONSTS.ALL_GAMES_SIGNS)

        HALF_LENGTH = len(signs) // 2
        if length is None:
            length = HALF_LENGTH
        super().__init__(signs[:length])
        self.inverted_sings = signs[HALF_LENGTH : HALF_LENGTH + length]

    def invert(self, sign):
        if sign in self:
            return self.inverted_sings[self.index(sign)]
        elif sign in self.inverted_sings:
            return self[self.inverted_sings.index(sign)]
        elif sign == CONSTS.EMPTY_CELL:
            return CONSTS.INVERTED_EMPTY_CELL
        elif sign == CONSTS.INVERTED_EMPTY_CELL:
            return CONSTS.EMPTY_CELL
        else:
            print('WTF', sign)

    def __str__(self):
        return ''.join(self) + ''.join(self.inverted_sings)


GameSigns.DEFAULT = GameSigns(list(CONSTS.DEFAULT_GAMES_SIGNS))
