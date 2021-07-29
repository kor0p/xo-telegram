from __future__ import annotations

import re
from itertools import permutations
from typing import Optional, Union, Iterable

from .languages import Language
from .row import RowItem, Row, join
from .button import inline_buttons
from .const import CONSTS, HOW_MANY_TO_WIN, BIG_GAME_SIZES, URLS, GameType, GameEndAction, Choice, GameSigns
from .utils import callback


def is_cell_free(board_cell: str) -> bool:
    return board_cell == CONSTS.EMPTY_CELL


class Board(Row):
    __slots__ = ('signs', 'raw_size')

    @classmethod
    def create(
        cls, signs: GameSigns, board: Union[str, Iterable, int], size: int = 0, used_for_big_board: bool = False
    ) -> Board:
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

        if size in BIG_GAME_SIZES and not used_for_big_board:
            return BoardBig(signs, board, round(size ** 0.5))
        return Board(signs, board, size)

    def __init__(self, signs: GameSigns, board: str, size: int = 0):
        self.signs = signs
        self.raw_size = size
        super().__init__([Row(board[i * size : (i + 1) * size]) for i in range(size)], size)

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
        if choice:
            self[choice] = self.signs.invert(self[choice])

    def board_text(self, last_turn: Optional[Choice] = None):
        self.set_inverted_value_for_choice(last_turn)
        board = join('\n', (self[i] for i in range(self.size))) + '\n'
        self.set_inverted_value_for_choice(last_turn)
        return board

    def check_win_for_sign(self, sign):
        """one system for all sizes"""
        win_count = HOW_MANY_TO_WIN[self.raw_size][len(self.signs)]

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
            ((0, 2), (2, 0), (0, 1)),
            ((0, 0), (2, 2), (0, 1)),
            ((0, 0), (1, 1), (0, 2)),
            ((0, 2), (1, 1), (2, 0)),
        ):
            if res := self.last_of_three(s, *map(Choice, positions)):
                return res
        # last hope :)
        for i in range(2, -1, -1):
            for j in range(2, -1, -1):
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
                    game_callback.create(Choice(i, j) if is_cell_free(item) else item),
                )
                for i in range(self.size)
                for j in range(self.size)
            ),
            is_users_game and (language.do_tie, callback.confirm_end.create(GameEndAction.TIE, turn)),
            is_users_game and (language.giveup, callback.confirm_end.create(GameEndAction.GIVE_UP, turn)),
            width=self.size,
        )

    def end_game_buttons(self, signs: GameSigns, *utm_ref: str):
        current_chat = bool(utm_ref)
        return inline_buttons(
            *(
                {
                    'text': sign,
                    'current_chat' if current_chat else 'another_chat': f'{sign}{self.size} n={len(self.signs)}',
                }
                for sign in signs
            ),
            current_chat
            and {
                'text': CONSTS.ROBOT,
                'url': URLS.ROBOT_START.format(utm_ref='__'.join(('robot',) + utm_ref)),
            },
            not current_chat and (CONSTS.ROBOT, callback.create(callback.text__reset_start)),
            width=len(self.signs),
        )


class BoardBig(Board):
    __slots__ = ('s_value',)

    def __init__(self, signs: GameSigns, board: str, size: int = 0):
        super().__init__(signs, '')
        self.size = size
        self.raw_size = size ** 2
        self.value = [
            [
                Board.create(
                    signs,
                    board[(row * size + col) * (size ** 2) : (row * size + col + 1) * (size ** 2)],
                    size=size,
                    used_for_big_board=True,
                )
                for col in range(size)
            ]
            for row in range(size)
        ]
        self.set_small_value(
            Board.create(
                signs,
                board[-size * size :] if len(board) == size ** 4 + size ** 2 else size,
                used_for_big_board=True,
            )
        )

    def set_small_value(self, board: Optional[Board] = None):
        if board is None:
            board = self.small_value(True)
        self.s_value = board

    def __getitem__(self, key: RowItem):
        if isinstance(key, int):
            return Row(self.value[key])
        return super().__getitem__(key)

    def __repr__(self):
        return repr(self.value) + '\n\n' + repr(self.small_value())

    def __str__(self):
        return join('', self) + str(self.small_value())

    def set_inverted_value_for_choice(self, choice: Optional[Choice]):
        if choice:
            super().set_inverted_value_for_choice(choice)
            outer_choice = choice.get_outer()
            r = []
            for row in self[outer_choice]:
                for i in row:
                    r.append(self.signs.invert(i))

            self[outer_choice] = Board.create(self.signs, r, used_for_big_board=True)

    def small_value(self, new=False):
        arr = []
        if self.s_value:
            if not new:
                return self.s_value
            arr = list(str(self.s_value))
        if arr:
            for i in range(self.size ** 2):
                temp_board = self[i // self.size][i % self.size]
                temp_board.raw_size = self.raw_size
                for sign in reversed(self.signs):
                    if is_cell_free(arr[i]) and temp_board.check_win_for_sign(sign):
                        arr[i] = sign
            return Board.create(self.signs, arr, used_for_big_board=True)
        else:
            return Board.create(self.signs, self.size ** 2, used_for_big_board=True)

    def board_text(self, last_turn: Optional[Choice] = None):
        if last_turn and last_turn.is_outer():
            outer_choice = last_turn.get_outer()
            last_turn = Choice(*outer_choice, *outer_choice)
        self.set_inverted_value_for_choice(last_turn)
        board = (
            '\n\n'.join(
                '\n'.join('  '.join(str(self[i][j][k]) for j in range(self.size)) for k in range(self.size))
                for i in range(self.size)
            )
            + '\n'
        )
        self.set_inverted_value_for_choice(last_turn)
        if last_turn:
            last_turn = Choice(last_turn.x, last_turn.y)
        board += f'\n{self.small_value().board_text(last_turn)}\n'
        return board

    def check_win_for_sign(self, sign):
        board = self.small_value()
        board.raw_size = self.raw_size
        return board.check_win_for_sign(sign)

    def game_buttons(self, game_sign, user_language: Language, last_turn: Optional[Choice] = None):
        if last_turn is not None:
            board = self[last_turn.get_outer()]
            if not board or (
                len(re.findall(CONSTS.EMPTY_CELL, str(board))) == 1
                and str(board).index(CONSTS.EMPTY_CELL) == last_turn.x * self.size + last_turn.y
            ):
                board = self.small_value()
                last_turn = Choice()
        else:
            board = self.small_value()
            last_turn = Choice()
        return inline_buttons(
            *(
                (
                    cell := board[i][j],
                    callback.game.create(
                        CONSTS.LOCK
                        if (last_turn.x == i and last_turn.y == j)
                        else Choice(last_turn.a, last_turn.b, i, j)
                        if not board or last_turn.is_inner() or cell == CONSTS.EMPTY_CELL
                        else cell
                    ),
                )
                for i in range(self.size)
                for j in range(self.size)
            ),
            (user_language.do_tie, callback.confirm_end.create(GameEndAction.TIE, last_turn)),
            (user_language.giveup, callback.confirm_end.create(GameEndAction.GIVE_UP, last_turn)),
            {'text': user_language.rules, 'url': URLS.ULTIMATE_TIC_TAC_TOE},
            width=self.size,
        )
