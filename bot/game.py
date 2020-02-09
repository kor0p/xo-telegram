import time
import threading

from datetime import datetime
from .boards import Board, BoardBig, create_board
from .user import TGUser
from .button import *
from .database import Base, XOTEXTDB, XODB, db as sa


class Game:
    def __init__(self, _id, new=False, db=Base):
        self.db = db
        self.id = str(_id)
        self._set()
        print(self.db.whereAll())
        if self().first():
            if new:
                self.delete()
            else:
                self._set(**self().first().raw())
        if new:
            self.db.create(**self.data())
        print('__init__', self.db.whereAll(), dir(self), sep='\n')

    def __call__(self):
        return self.db.where(id=self.id, deleted_at=None)

    def push(self):
        print('pushing...')
        self().update(**self.data())
        print(self.db.whereAll())

    def _set(self, **kwargs):
        print('kwargs, but why...:', kwargs)
        # raise NotImplementedError("Base class has no _set method")

    def delete(self):
        self().update(deleted_at=sa.sql.func.now())
        print("Deleted")

    def __bool__(self):
        return bool(self().first())

    def data(self):
        res = {str(k): str(v) for k, v in vars(self).items()}
        res.pop('db')
        print('return .data:', res)
        return res


class XOText(Game):
    __tablename__ = 'xo_text'

    def __init__(self, _id, new=False):
        super().__init__(_id, new, XOTEXTDB)

    def _set(self, is_x=None, b=None):
        self.isX,       self.b = \
        int(is_x or 0), Board(b or '')


class XO(Game):
    __tablename__ = 'xo'

    def __init__(self, _id, new=False):
        super().__init__(_id, new, XODB)

    def upd_id(self, new_id):
        old_id = self.id
        self.id = new_id
        self.db.where(id=old_id).update(**self.data())
        print('upd id:', self.db.whereAll())

    def _set(self, plX=None, plO=None, giveup_user=None, queue=None, b=None, tie_id=None):
        s = int(len(b or '.'*9)**.5)
        self.plX,    self.plO,    self.giveup_user,    self.queue,      self.b,             self.tie_id  = \
        TGUser(plX), TGUser(plO), TGUser(giveup_user), int(queue or 1), create_board(b, s), int(tie_id or 0)

    def __bool__(self):
        return bool(super()) or self.tie_id or bool(self.giveup_user)

    def __repr__(self):
        return str(vars(self))

    def __str__(self):
        return ', '.join((f"{name} = {value}" for name, value in vars(self).items()))

    def game_language(self):
        return self.plX.lang + self.plO.lang

    def end(self, g_type, index_last_turn=None, text=''):
        name_x = self.plX.first_name
        name_o = self.plO.first_name
        ul = self.game_language()
        if g_type == 'giveup':
            self.queue = int(self.giveup_user == self.plO)
        text += '\n'
        if g_type == 'tie':
            text +=\
                f'{sgn.x} {name_x} {cnst.tie} {name_o} {sgn.o}\n' +\
                ul.cnld*bool(self.b)
        elif g_type in ('win', 'giveup'):
            text +=\
                f'{sgn.x} {name_x} {end_signs[self.queue]}\n' +\
                f'{sgn.o} {name_o} {end_signs[not self.queue]}\n'
        elif g_type:
            text +=\
                f'{sgn.x} {name_x}\n' +\
                f'{sgn.o} {name_o}\n'
        if g_type == 'giveup':
            text += ul.player.format(self.giveup_user.first_name)
        if index_last_turn and index_last_turn[0] == 9:
            index_last_turn = ()
        b_text = self.b.board_text(index_last_turn)
        button = self.b.end_game_buttons(current_chat=True)
        out = bot.edit_message_text(
            b_text + text,
            inline_message_id=self.id,
            reply_markup=button
        )
        if index_last_turn:
            self.timeout(5, '\n' + text)
        else:
            self.delete()
        return out

    def game_xo(self, choice):
        if isinstance(self.b, BoardBig):
            return self.game_xo_big(choice)
        ul = self.game_language()
        name_x = self.plX.first_name
        name_o = self.plO.first_name
        if choice:
            self.b[choice] = game_signs[self.queue]
            if self.b.winxo(self.b[choice]):
                return self.end('win', choice)
            elif not self.b:
                return self.end('tie', choice)
        if sgn.x in str(self.b) or sgn.o in str(self.b):
            self.queue = int(not self.queue)  # pass turn
        self.push()
        bot.edit_message_text(
            ul.to_win.format(how_many_to_win[self.b.size]) + '\n' +
            f'{sgn.x} {name_x}{cnst.turn*self.queue}\n' +
            f'{sgn.o} {name_o}{cnst.turn*(not self.queue)}',
            inline_message_id=self.id,
            reply_markup=self.b.game_buttons(
                choice, cnst.friend, ul
            )
        )

    def game_xo_big(self, choice):
        ul = self.game_language()
        name_x = self.plX.first_name
        name_o = self.plO.first_name
        last_turn = ()
        if choice and choice[0] != 9:
            last_turn = choice
            self.b[choice] = game_signs[self.queue]
            self.b.s_value = self.b.small_value(True)
            if self.b.winxo(self.b[choice]):
                return self.end('win', choice)
            elif not self.b:
                return self.end('tie', choice)
        if (sgn.x in str(self.b) or sgn.o in str(self.b)) and last_turn:
            self.queue = int(not self.queue)  # pass turn
        elif choice:
            last_turn = choice[2:]*2
        self.push()
        bot.edit_message_text(
            self.b.board_text(last_turn) + '\n\n' +
            f'{sgn.x} {name_x}{cnst.turn*self.queue}\n' +
            f'{sgn.o} {name_o}{cnst.turn*(not self.queue)}',
            inline_message_id=self.id,
            reply_markup=self.b.game_buttons(
                choice, cnst.friend, ul
            )
        )

    def timeout(self, _time, text, last_turn=()):
        text = text.split('\n', maxsplit=1)

        def __inner():
            print('start __inner')
            time.sleep(_time)
            print('end sleep')
            if _time > 60 or _time < 10 or bool(self):
                if _time > 10:
                    time.sleep(5)
                if not self:
                    return 2, 0
                if len(text) > 1:
                    return 3, self.end(text[0], last_turn, text[1])
                return 4, self.end(text[0], last_turn, cnst.time)

        thread = threading.Thread(target=__inner, args=())
        thread.daemon = True
        thread.start()

    def timeout_confirm(self, g_type, pl, l_t):
        ul = self.game_language()
        another_user = (self.plX, self.plO)[pl == self.plX]
        _user = another_user if g_type == 'tie' else pl
        ul_user = _user.lang
        text = eval(f"ul_user.confirm_{g_type}")
        buttons = callback_buttons((
            (ul_user.cnf, f'confirm_{g_type}{l_t}'),
            (ul.cnl, f'cancelend{l_t}')
        ))
        bot.edit_message_text(
            (
                f'[{_user.first_name}](tg://user?id={_user.id})',
                f'@{_user.username}'
            )[bool(_user.username)] +
            f',\n{text}',
            inline_message_id=self.id,
            reply_markup=buttons,
            parse_mode='Markdown'
        )
        self.timeout(30, g_type, l_t)
