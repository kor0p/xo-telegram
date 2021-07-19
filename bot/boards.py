from __future__ import annotations

import re
from itertools import permutations
from typing import Optional, Union, Iterable

from .languages import Language
from .row import RowItem, Row, join
from .button import inline_buttons
from .const import (
    CONSTS,
    UserSigns,
    how_many_to_win,
    BIG_GAME_SIZES,
    inverted_game_signs,
    URLS,
    GameType,
    GameEndAction,
    Choice,
    CHOICE_NULL,
)
from .utils import callback


def is_cell_free(board_cell: str) -> bool:
    return board_cell == CONSTS.EMPTY_CELL


class Board(Row):
    @classmethod
    def create(cls, board: Union[str, Iterable, int], size: int = 0) -> Board:
        if isinstance(board, Iterable) and not isinstance(board, str):
            board = ''.join(board)
        if isinstance(board, int):
            size = board
            board = None
        if board and not size:
            size = round(len(board) ** 0.5)
        size = size or 3
        if not board:
            board = CONSTS.EMPTY_CELL * (size ** 2)

        if size in BIG_GAME_SIZES:
            return BoardBig(board, round(size ** 0.5))
        return Board(board, size)

    def __init__(self, board: str, size: int = 0):
        self.size = size
        self.value = [Row(board[i * size : (i + 1) * size]) for i in range(size)]

    def __contains__(self, key):
        return key in str(self.value)

    def __bool__(self):
        return CONSTS.EMPTY_CELL in str(self)

    def free(self, index: RowItem) -> bool:
        return is_cell_free(self[index])

    def last_of_three(self, sign: str, *positions: Choice) -> Choice:
        for x, y, z in permutations(positions):
            if self[x] == self[y] == sign and self.free(z):
                return z
        return Choice()

    def set_inverted_value_for_choice(self, choice: Optional[Choice]):
        if choice is not None:
            self[choice] = inverted_game_signs[self[choice]]

    def board_text(self, last_turn: Optional[Choice] = None):
        self.set_inverted_value_for_choice(last_turn)
        board = join('\n', (self[i] for i in range(self.size))) + '\n'
        self.set_inverted_value_for_choice(last_turn)
        return board

    def check_win_for_sign(self, sign):
        """one system for all sizes"""
        win_count = how_many_to_win(self.size)

        board = self.board_text()  # # check for first N turns:
        if board.count(sign) < win_count:  # if there is less than N count of sign -> no way to have win
            return

        def all_in_row(cb):
            return all(self[Choice(cb(q))] == sign for q in range(win_count))

        return any(
            # main diagonal check                     or collateral diagonal check
            (all_in_row(lambda q: ((j + q), (i + q))) or all_in_row(lambda q: ((j + q), (i + win_count - 1 - q))))
            or any(
                # horizontal lines check                 or vertical lines check
                (all_in_row(lambda q: ((j + l), (i + q))) or all_in_row(lambda q: ((j + q), (i + l))))
                for l in range(win_count)
            )
            for i in range(self.size + 1 - win_count)
            for j in range(self.size + 1 - win_count)
        )

    def bot_choice_func(self, bot_sgn, user_sgn) -> Optional[Choice]:
        if not self:
            return
        for s in [bot_sgn, user_sgn]:
            for positions in (
                ((0, 0), (1, 1), (2, 2)),  # crosses
                ((0, 2), (1, 1), (2, 0)),  # then rows and cols
                *[[(i, j) for j in range(3)] for i in range(3)],
                *[[(j, i) for j in range(3)] for i in range(3)],
            ):
                if res := self.last_of_three(s, *map(Choice, positions)):
                    return res

        if self.free(center := Choice(1, 1)):
            return center

        for positions in (
            ((0, 1), (0, 2), (1, 0)),
            ((0, 0), (0, 1), (1, 2)),
            ((1, 0), (2, 1), (2, 2)),
            ((1, 2), (2, 1), (2, 1)),
        ):
            if res := self.last_of_three(s, *map(Choice, positions)):
                return res
        # last hope :)
        for i in range(3):
            for j in range(3):
                if self.free(index := Choice(i, j)):
                    return index

    def game_buttons(self, game_type: GameType, language=Language(), turn=None):
        if turn is None:
            turn = Choice()
        else:
            self.set_inverted_value_for_choice(turn)
        is_users_game = game_type == GameType.USER
        game_callback: callback = callback.game if is_users_game else callback.text__game

        return inline_buttons(
            *(
                (
                    item := str(self[i][j]),
                    game_callback.create(Choice(i, j) if item == CONSTS.EMPTY_CELL else item),
                )
                for i in range(self.size)
                for j in range(self.size)
            ),
            is_users_game and (language.do_tie, callback.confirm_end.create(GameEndAction.TIE, turn)),
            is_users_game and (language.giveup, callback.confirm_end.create(GameEndAction.GIVE_UP, turn)),
            width=self.size,
        )

    def end_game_buttons(self, *utm_ref):
        current_chat = bool(utm_ref)
        other_chat = not current_chat
        return inline_buttons(
            *(
                {
                    'text': sign,
                    'current_chat': current_chat and f'x{self.size}',
                    'another_chat': other_chat and f'x{self.size}',
                }
                for sign in UserSigns
            ),
            current_chat
            and {
                'text': CONSTS.ROBOT,
                'url': URLS.ROBOT_START.format(utm_ref='__'.join(('robot',) + utm_ref)),
            },
            other_chat and (CONSTS.ROBOT, callback.create(callback.text__reset_start)),
            width=2,
        )


class BoardBig(Board):
    __slots__ = ('s_value',)

    def __init__(self, board: str, size: int = 0):
        super().__init__('')
        self.size = size
        self.value = [
            [
                Board.create(board[(row * size + col) * (size * size) : (row * size + col + 1) * (size * size)])
                for col in range(size)
            ]
            for row in range(size)
        ]
        self.s_value = Board.create(board[-size * size :]) if len(board) == size ** 4 + size ** 2 else Board('')

    def __getitem__(self, key: RowItem):
        if isinstance(key, int):
            return Row(self.value[key])
        return super().__getitem__(key)

    def __repr__(self):
        return join('', self) + str(self.small_value())

    def set_inverted_value_for_choice(self, choice: Optional[Choice]):
        if choice is not None:
            super().set_inverted_value_for_choice(choice)
            Board.create(inverted_game_signs[i] for row in self[choice[2:]] for i in row)

    def small_value(self, new=False):
        arr = []
        if self.s_value:
            if not new:
                return self.s_value
            arr = list(str(self.s_value))
        arr = arr or [CONSTS.EMPTY_CELL] * self.size ** 2
        for i in range(self.size):
            for sign in reversed(UserSigns):
                if self[i // self.size][i % self.size].check_win_for_sign(sign) and arr[i] == CONSTS.EMPTY_CELL:
                    arr[i] = sign
        return Board.create(arr)

    def board_text(self, last_turn: Optional[Choice] = None):
        if last_turn and last_turn[0] == CHOICE_NULL:
            last_turn = last_turn[2:] * 2
        self.set_inverted_value_for_choice(last_turn)
        board = (
            '\n\n'.join(
                '\n'.join('  '.join(self[i][j][k] for j in range(self.size)) for k in range(self.size))
                for i in range(self.size)
            )
            + '\n'
        )
        self.set_inverted_value_for_choice(last_turn)
        if last_turn:
            last_turn = last_turn[:2]
        board += f'\n{self.small_value().board_text(last_turn)}\n'
        return board

    def check_win_for_sign(self, sign):
        return self.small_value().check_win_for_sign(sign)

    def game_buttons(self, game_sign, user_language=None, l_t=None):
        if l_t is not None:
            board = self[l_t[2:]]
            if not board or (
                len(re.findall(CONSTS.EMPTY_CELL, str(board))) == 1
                and str(board).index(CONSTS.EMPTY_CELL) == l_t[0] * self.size + l_t[1]
            ):
                board = self.small_value()
                l_t = Choice()
        else:
            board = self.small_value()
            l_t = Choice()
        return inline_buttons(
            *(
                (
                    cell := board[i][j],
                    callback.game.create(
                        CONSTS.LOCK
                        if l_t[:2] == [i, j]
                        else Choice(l_t[2], l_t[3], i, j)
                        if not board or l_t[2] == CHOICE_NULL or cell == CONSTS.EMPTY_CELL
                        else cell
                    ),
                )
                for i in range(self.size)
                for j in range(self.size)
            ),
            (user_language.do_tie, callback.confirm_end.create(GameEndAction.TIE, l_t)),
            (user_language.giveup, callback.confirm_end.create(GameEndAction.GIVE_UP, l_t)),
            {'text': user_language.rules, 'url': URLS.ULTIMATE_TIC_TAC_TOE},
            width=self.size,
        )
