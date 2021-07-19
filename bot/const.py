from dataclasses import dataclass
from enum import Enum
from typing import Literal, Iterable


class URLS:
    ROBOT_START = 'https://t.me/m0xbot?start={utm_ref}'
    DONATE = 'https://send.monobank.ua/zEuxNoaWc'
    ULTIMATE_TIC_TAC_TOE = 'https://mathwithbaddrawings.com/2013/06/16/ultimate-tic-tac-toe/'


STICKERS = {
    'X': 'CAADAgADKQAD-8YTE7geSMCRsyDEAg',  # CAACAgIAAxkBAAECmhhg9eL9L7Vzhn6e1-FT6AOBVQABiFUAAikAA_vGExO4HkjAkbMgxCAE
    'O': 'CAADAgADKAAD-8YTE4byaCljfP--Ag',
}


def how_many_to_win(size):  # 2 -> 2 | 3,4 -> 3 | 5,6 -> 4 | 7,8 -> 5
    assert size in ALL_AVAILABLE_ACTUAL_GAME_SIZES
    return round(size * 0.5 + 1.5)


BIG_GAME_SIZES = (4, 9, 16)
SMALL_GAME_SIZES = (3, 5, 6, 7, 8)
ALL_AVAILABLE_ACTUAL_GAME_SIZES = (2, *SMALL_GAME_SIZES)
GAME_SIZES: tuple[int, ...] = (*BIG_GAME_SIZES, *SMALL_GAME_SIZES)


class SIGNS:
    X = '❌'
    O = '⭕'


class INVERTED_SIGNS:
    CELL = '◻'
    X = '✖'
    O = '🔴'


class CONSTS:
    SUPER_ADMIN_USER_ID = 320063227
    LOCK = 'LOCK'
    BOT_USERNAME = 'BOT'
    EMPTY_CELL = '⬜'
    TIME = '⏳'
    WIN = '🏆'
    LOSE = '☠️'
    TURN = ' 👈'
    ROBOT = '🤖'


inverted_game_signs = {
    SIGNS.X: INVERTED_SIGNS.X,
    SIGNS.O: INVERTED_SIGNS.O,
    CONSTS.EMPTY_CELL: INVERTED_SIGNS.CELL,
    INVERTED_SIGNS.X: SIGNS.X,
    INVERTED_SIGNS.O: SIGNS.O,
    INVERTED_SIGNS.CELL: CONSTS.EMPTY_CELL,
}


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
    # CONFIRM = 'CONFIRM'
    CANCEL = 'CANCEL'


class UserSignsEnum(Enum):
    X = SIGNS.X
    O = SIGNS.O


class ActionType(Enum):
    GAME = 0
    TIE = 1
    GIVE_UP = 2


UserSignsNames = tuple(sign.name for sign in UserSignsEnum)
UserSigns = tuple(sign.value for sign in UserSignsEnum)
SIGNS_TYPE = Literal[UserSigns]

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
