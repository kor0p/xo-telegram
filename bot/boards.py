from .user import TGUser
from .row import *
from .button import *
from .const import *
import re


def free(board_cell):
    return board_cell not in game_signs


def create_board(board, size):
    if size < 9 and size != 4:
        return Board(board)
    return BoardBig(board)


class Board(Base):

    def __init__(self, _board=''):
        if not _board:
            _board = sgn.cell * 9
        s = int(len(_board) ** .5)
        self.size = s
        self.value = [
            Row(_board[i * s:(i + 1) * s])
            for i in range(s)
        ]

    def __setitem__(self, key, item):
        if not key:
            raise KeyError("It must be int or tuple")
        if isinstance(key, tuple):
            self.value[key[0]][key[1]] = item
        elif isinstance(key, int):
            self.value[key] = item

    def __bool__(self):
        return sgn.cell in str(self)

    def last_of_three(self, a, b, c, sign):
        for x, y, z in ((a, b, c), (c, a, b), (b, c, a)):
            if self[x] == self[y] == sign and free(self[z]):
                return z
        return ()

    def board_text(self, last_turn=None):
        if last_turn:
            self[last_turn] = new_game_signs[self[last_turn]]
        b = join('\n', [self[i] for i in range(self.size)]) + '\n'
        if last_turn:
            self[last_turn] = new_game_signs[self[last_turn]]
        return b

    def winxo(self, sign):
        row = how_many_to_win[self.size]
        # one system for all sizes
        rowr = range(row)
        return any([
            all([self[j + q][i + q] == sign for q in rowr]) or
            # main diagonal check
            all([self[j + q][i + row - 1 - q] == sign for q in rowr]) or
            # collateral diagonal check
            any([
                all([self[j + l][i + q] == sign for q in rowr]) or
                # horizontal lines check
                all([self[j + q][i + l] == sign for q in rowr])
                # vertical lines check
                for l in range(row)
            ])
            for i in range(self.size + 1 - row)
            for j in range(self.size + 1 - row)
        ])

    def bot_choice_func(self, bot_sgn, user_sgn):
        if not self:
            return []
        for s in [bot_sgn, user_sgn]:  # . 0 1 2
            for x, y, z in (  # 0 . . .
                    ((0, 0), (1, 1), (2, 2)),  # 1 . . .
                    ((0, 2), (1, 1), (2, 0)),  # 2 . . .
                    *(((i, j) for j in range(3)) for i in range(3)),
                    *(((j, i) for j in range(3)) for i in range(3))
            ):
                res = self.last_of_three(x, y, z, s)
                if res:
                    return res
        # leave this part, please, it just works!
        for i, j, k, r in (
                ((0, 1), (1, 0), (1, 2), (0, 2)),
                ((2, 1), (1, 0), (1, 2), (2, 2)),
                ((0, 2), (2, 0), (1, 0), (0, 1)),
                ((0, 0), (2, 2), (1, 2), (0, 1))
        ):
            if (free(self[r]) and
                    self[i] == user_sgn and
                    user_sgn in (self[j], self[k])):
                return r
        for i, j, k, l, r in (
                ((1, 0), (2, 2), (1, 2), (2, 0), (2, 1)),
                ((0, 1), (2, 0), (0, 0), (2, 1), (1, 0)),
                ((0, 1), (2, 2), (0, 2), (2, 1), (1, 2)),
                ((1, 1), (2, 2), (1, 1), (2, 2), (0, 2))
        ):
            if free(self[r]) and (
                    self[i] == self[j] == user_sgn or
                    self[k] == self[l] == user_sgn
            ):
                return r
        # last hope :)
        for i in range(3):
            for j in range(3):
                if free(self[i][j]):
                    return i, j

    def game_buttons(self, last_turn, game_sign,
                     user_language=TGUser().lang):
        if last_turn:
            self[last_turn] = new_game_signs[self[last_turn]]
        last_turn = last_turn or (9, 9)
        return callback_buttons(
            tuple(
                (self[i][j],
                 game_sign +
                 str((self[i][j], f'{i}{j}')[self[i][j] == sgn.cell])
                 )
                for i in range(self.size)
                for j in range(self.size)
            )
            +
            (
                (user_language.do_tie, f'tie{last_turn[0]}{last_turn[1]}'),
                (user_language.giveup, f'giveup{last_turn[0]}{last_turn[1]}')
            ) * bool(user_language) * (game_sign != cnst.robot),
            width=self.size
        )

    def end_game_buttons(self, current_chat=False):
        return inline_buttons_(
            [[
                 {
                     'text': sgn.x,
                     'current_chat': f'x{self.size}'
                     if current_chat else None,
                     'another_chat': f'x{self.size}'
                     if not current_chat else None
                 },
                 {
                     'text': sgn.o,
                     'current_chat': f'o{self.size}'
                     if current_chat else None,
                     'another_chat': f'o{self.size}'
                     if not current_chat else None
                 }
             ] + [[
                      {
                          'text': cnst.robot,
                          'callback': cnst.repeat * 2
                      },
                      {
                          'text': cnst.robot,
                          'url': 't.me/m0xbot?start=1'
                      }
                  ][current_chat]
                  ]],
            width=2
        )


class BoardBig(Board):

    def __init__(self, _board=''):
        super().__init__(_board)
        _board = _board or sgn.cell * 81
        self.size = s = int(len(_board) ** .25)
        self.value = \
            [
                [
                    Board(_board[(i * s + j) * (s * s):(i * s + j + 1) * (s * s)])
                    for j in range(s)
                ] for i in range(s)
            ]
        self.s_value = Board(_board[-s * s:]) \
            if len(_board) == s ** 4 + s ** 2 else Board()

    def __getitem__(self, key):
        if isinstance(key, tuple):
            if len(key) == 2:
                return self.value[key[0]][key[1]]
            return self.value[key[0]][key[1]][key[2]][key[3]]
        return Row(self.value[key])

    def __setitem__(self, key, item):
        if key and isinstance(key, tuple):
            if len(key) == 2:
                self.value[key[0]][key[1]] = item
                return None
            self.value[key[0]][key[1]][key[2]][key[3]] = item

    def __repr__(self):
        return join('', self) + str(self.small_value())

    def small_value(self, new=False):
        arr = []
        if self.s_value:
            if not new:
                return self.s_value
            arr = list(str(self.s_value))
        arr = arr or [sgn.cell] * self.size ** 2
        for i in range(self.size):
            for s in game_signs:
                if self[i // self.size][i % self.size].winxo(s) and \
                        arr[i] == sgn.cell:
                    arr[i] = s
        return Board(join('', arr))

    def board_text(self, last_turn=()):
        if last_turn and last_turn[0] == 9:
            last_turn = last_turn[2:] * 2
        if last_turn:
            self[last_turn] = new_game_signs[self[last_turn]]
            self[last_turn[2:]] = Board(''.join([
                new_game_signs[i]
                for row in self[last_turn[2:]]
                for i in row
            ]))
        b = '\n\n'.join(
            ['\n'.join(
                [join('  ', [self[i][j][k] for j in range(self.size)])
                 for k in range(self.size)]
            ) for i in range(self.size)]
        ) + '\n'
        if last_turn:
            self[last_turn] = new_game_signs[self[last_turn]]
            self[last_turn[2:]] = Board(''.join([
                new_game_signs[i]
                for row in self[last_turn[2:]]
                for i in row
            ]))
        if last_turn:
            last_turn = last_turn[:2]
        b += '\n' + self.small_value().board_text(last_turn) + '\n'
        return b

    def winxo(self, sign):
        return self.small_value().winxo(sign)

    def game_buttons(self,
                     l_t=(),
                     game_sign=cnst.friend,
                     user_language=TGUser().lang
                     ):
        if l_t:
            board = self[l_t[2:]]
            if not board or (
                    len(re.findall(sgn.cell, str(board))) == 1 and
                    str(board).index(sgn.cell) == l_t[0] * self.size + l_t[1]
            ):
                l_t = ()
                board = self.small_value()
        else:
            board = self.small_value()
        l_t = l_t or (9,) * 4
        markup = callback_buttons(
            tuple(
                (board[i][j],
                 game_sign +
                 str(cnst.lock if l_t[:2] == (i, j) else
                     f'{l_t[2]}{l_t[3]}{i}{j}' if
                     not board or
                     l_t[2] == 9 or
                     board[i][j] == sgn.cell else
                     board[i][j]
                     ))
                for i in range(self.size)
                for j in range(self.size)
            )
            +
            (
                (user_language.do_tie,
                 'tie' + join('', l_t)),
                (user_language.giveup,
                 'giveup' + join('', l_t))
            ) * bool(user_language),
            width=self.size
        )
        markup.add(telebot.types.InlineKeyboardButton(
            user_language.rules,
            url='https://mathwithbaddrawings.com/2013/06/16/ultimate-tic-tac-toe/'
        ))
        return markup
