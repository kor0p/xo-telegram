import telebot
import cherrypy
import threading
import sqlite3
import re
from os import system
from random import choice
from collections import namedtuple
from secure_config import (
    token, ip_address, port, path_to_db
)
headers = cherrypy.request.headers
body = cherrypy.request.body

bot = telebot.TeleBot(token)

WEBHOOK_HOST = ip_address
WEBHOOK_PORT = port
# 443,80,88 or 8443,port must be open; I use 8443
WEBHOOK_LISTEN = '0.0.0.0'
# on some servers need to be as WEBHOOK_HOST
WEBHOOK_SSL_CERT = '../webhook/webhook_cert.pem'
WEBHOOK_SSL_PRIV = '../webhook/webhook_pkey.pem'
WEBHOOK_URL_BASE = 'https://%s:%s' % (WEBHOOK_HOST, WEBHOOK_PORT)
WEBHOOK_URL_PATH = '/%s/' % token

langs = {
    'en': {
        'start': 'Choose your side and get started!',
        'bot': 'Bot',
        'dont_touch': 'Oh, you can\'t go there',
        'cnld': 'Canceled',
        'new': 'Start a new game?',
        'to_win': lambda s: f'{s} in the row to win!',
        'stop': 'Stop! Wait your turn',
        'stop_game': 'Stop! There already playing',
        'dotie': 'Tie',
        'confirm_tie': 'Accept tie?',
        'confirm_giveup': 'Confirm giving up!',
        'start_pl_2': 'Let’s go!',
        'player': lambda n: f'Player {n} gives up',
        'giveup': 'Give up',
        'cnf': 'Confirm',
        'cnl': 'Cancel',
        'startN': 'Choose size and get started!',
        'random': 'Random',
        'timeout': lambda s: f'Seconds remains: {s}',
        'start9': 'It\'s double-turn, keep going!',
        'rules': 'Rules'
    }, 'uk': {
        'start': 'Обирай сторону і почнімо!',
        'bot': 'Бот',
        'dont_touch': 'Ой, сюди заборонено ходити)',
        'cnld': 'Відмінено',
        'new': 'Зіграємо ще раз?',
        'to_win': lambda s: f'{s} поспіль для перемоги!',
        'stop': 'Стоп! Не твій хід)',
        'stop_game': 'Стоп! Тут уже грають)',
        'dotie': 'Нічия',
        'confirm_tie': 'Приймаєш нічию?',
        'confirm_giveup': 'Підтвердь поразку!',
        'start_pl_2': 'Почнімо!',
        'player': lambda n: f'Гравець {n} здався',
        'giveup': 'Здатися',
        'cnf': 'Підтверджую',
        'cnl': 'Відміна',
        'startN': 'Обирай тип і до бою!',
        'random': 'Однаково',
        'timeout': lambda s: f'Секунд лишилось: {s}',
        'start9': 'Твій хід ще триває, продовжуй!',
        'rules': 'Правила'
    }, 'ru': {
        'start': 'Выбери сторону и начнём!',
        'bot': 'Бот',
        'dont_touch': 'Ой, ты не можеш сюда идти!',
        'cnld': 'Отменено',
        'new': 'Сыграем ещё раз?',
        'to_win': lambda s: f'{s} в ряд для победы!',
        'stop': 'Стопэ! Не твой ход!',
        'stop_game': 'Стопэ! Здесь уже играют!',
        'dotie': 'Ничья',
        'confirm_tie': 'Принимаешь ничью?',
        'confirm_giveup': 'Подтвердите проиграш!',
        'start_pl_2': 'Начнём!',
        'player': lambda n: f'Игрок {n} сдался',
        'giveup': 'Сдаться',
        'cnf': 'Подтверждаю',
        'cnl': 'Отмена',
        'startN': 'Выбери тип и к бою!',
        'random': 'Рандом',
        'timeout': lambda s: f'Секунд осталось: {s}',
        'start9': 'Этот ход ещё не кончился, продолжай!',
        'rules': 'Правила'
    }
}

lang = namedtuple('lang', langs['en'])
languages = {k: lang(*langs[k].values()) for k in langs}

# constants
how_many_to_win = {
    3: 3,
    4: 4, 5: 4, 6: 4,
    7: 5, 8: 5
}

signs = namedtuple('signs', ('cell', 'x', 'o'))
sgn = signs('⬜', '❌', '⭕')
new_sgn = signs('◻', '✖', '🔴')
cnst = namedtuple('const_signs', (
    'lock', 'time', 'win', 'lose', 'tie', 'turn', 'repeat', 'robot', 'friend'
))('🔒', '⏳', '🏆', '☠️', '🤜🤛', ' 👈', '🔄', '🤖', '🙎')

game_signs = (sgn.o, sgn.x)
end_signs = (cnst.lose, cnst.win)
new_game_signs = {
    sgn.x: new_sgn.x,
    sgn.o: new_sgn.o,
    sgn.cell: new_sgn.cell,
    new_sgn.x: sgn.x,
    new_sgn.o: sgn.o,
    new_sgn.cell: sgn.cell
}

tg_user_default = {'id': 0, 'first_name': '?', 'language_code': 'en'}


def search_callback(to_find):
    return lambda c: re.search(
        {
            'reset_start': cnst.repeat * 2,
            'start': cnst.repeat + f'[{sgn.x}|{sgn.o}]',
            'choice_size': 'start\d',
            'text': cnst.robot + f'[\d\d|{sgn.x}|{sgn.o}]',
            'friend': cnst.friend + f'[\d\d|{sgn.x}|{sgn.o}|{cnst.lock}]',
            'confirm/end': 'cancel|tie|giveup|confirm'
        }[to_find],
        c.data)


class WebhookServer(object):
    def __init__(self, bot):
        self.bot = bot

    @cherrypy.expose
    def index(self):
        if 'content-length' in headers and \
                'content-type' in headers and \
                headers['content-type'] == 'application/json':
            length = int(headers['content-length'])
            json_string = body.read(length).decode('utf-8')
            update = telebot.types.Update.de_json(json_string)
            self.bot.process_new_updates([update])
            return ''
        raise cherrypy.HTTPError(403)


def webhook_func(bot):
    bot.remove_webhook()
    bot.set_webhook(
        url=WEBHOOK_URL_BASE + WEBHOOK_URL_PATH,
        certificate=open(WEBHOOK_SSL_CERT, 'r')
    )
    cherrypy.config.update({
        'server.socket_host': WEBHOOK_LISTEN,
        'server.socket_port': WEBHOOK_PORT,
        'server.ssl_module': 'builtin',
        'server.ssl_certificate': WEBHOOK_SSL_CERT,
        'server.ssl_private_key': WEBHOOK_SSL_PRIV})
    cherrypy.quickstart(
        WebhookServer(bot), WEBHOOK_URL_PATH, {'/': {}}
    )


class tg_user:

    def __init__(self, d=tg_user_default):
        if type(d) == str:
            d = eval(d)
        if type(d) == dict:
            self.id = d['id']
            self.first_name = d['first_name']
            self.language_code = d['language_code']
            return None
        self.id = d.id
        self.first_name = d.first_name
        self.language_code = d.language_code

    def __repr__(self):
        return str(self.__dict__)

    __str__ = __repr__

    def __bool__(self):
        return str(self) != str(tg_user_default)

    def lang(self):
        l_code = self.language_code
        if not l_code:
            l_code = tg_user_default['language_code']
        if '-' in l_code:
            l_code = l_code.strip('-')[0]
        return languages[l_code]

    def __eq__(self, other):
        return self.id == other.id

    def __ne__(self, other):
        return self.id != other.id


class Row:

    def __init__(self, board):
        if type(board) == str:
            board = list(board)
        self.value = board
        self.size = 3

    def __getitem__(self, key):
        if type(key) == tuple:
            return self.value[key[0]][key[1]]
        return self.value[key]

    def __setitem__(self, key, item):
        self.value[key] = item

    def __repr__(self):
        return join('', self)

    def __len__(self):
        return self.size

    __str__ = __repr__


class Board(Row):

    def __init__(self, _board=''):
        self.size = s = int(len(_board)**(.5))
        assert 9 > self.size > 2 or not self.size
        self.value = [
            Row(_board[i*s:(i+1)*s])
            for i in range(s)
        ]

    def __setitem__(self, key, item):
        if key and type(key) == tuple:
            self.value[key[0]][key[1]] = item

    def __bool__(self):
        return (sgn.cell in str(self))

    def last_of_three(self, a, b, c, sign):
        for x, y, z in [[a, b, c], [c, a, b], [b, c, a]]:
            if self[x] == self[y] == sign and free(self[z]):
                return z
        return ()

    def board_text(self, last_turn=None):
        if last_turn:
            self[last_turn] = new_game_signs[self[last_turn]]
        b = join('\n', [self[i] for i in range(self.size)])
        if last_turn:
            self[last_turn] = new_game_signs[self[last_turn]]
        return b

    def winxo(self, sgn):
        row = how_many_to_win[self.size]
        # one system for all sizes
        rowr = range(row)
        return any([
            all([self[j+q][i+q] == sgn for q in rowr]) or
            # main diagonal check
            all([self[j+q][i+row-1-q] == sgn for q in rowr]) or
            # collateral diagonal check
            any([
                all([self[j+l][i+q] == sgn for q in rowr]) or
                # horizontal lines check
                all([self[j+q][i+l] == sgn for q in rowr])
                # vertical lines check
                for l in range(row)
            ])
            for i in range(self.size + 1 - row)
            for j in range(self.size + 1 - row)
        ])

    def bot_choice_func(self, bot_sgn, user_sgn):
        if not self:
            return []
        for s in [bot_sgn, user_sgn]:      # . 0 1 2
            for x, y, z in (               # 0 . . .
                ((0, 0), (1, 1), (2, 2)),  # 1 . . .
                ((0, 2), (1, 1), (2, 0)),  # 2 . . .
                *zip(*(
                    zip(*(
                    ((i, j), (j, i))
                    for j in range(3)))
                    for i in range(3)))
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
                        user_sgn in (self[j], self[k])
                    ):
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

    def game_Buttons(self, last_turn, game_sign,
                     user_language=tg_user().lang()):
        if last_turn:
            self[last_turn] = new_game_signs[self[last_turn]]
        return InlineButtons(
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
                (user_language.dotie, 'tie'),
                (user_language.giveup, 'giveup')
            ) * bool(user_language),
            width=self.size
        )

    def end_game_Buttons(self, current_chat=False):
        return _InlineButtons_(
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


class Board_9(Board):

    def __init__(self, _board=''):
        if not _board:
            _board = sgn.cell*81
        self.size = s = 9
        self.value = [[
            Board(_board[(i*3+j)*9:(i*3+j+1)*9])
            for j in range(3)]
            for i in range(3)
        ]
        self.s_value = Board(_board[81:])\
            if len(_board) == 90 else Board('')

    def __getitem__(self, key):
        s = self.size
        if type(key) == tuple:
            if len(key) == 2:
                return self.value[key[0]][key[1]]
            return self.value[key[0]][key[1]][key[2]][key[3]]
        return Row(self.value[key])

    def __setitem__(self, key, item):
        if key and type(key) == tuple:
            if len(key) == 2:
                self.value[key[0]][key[1]] = item
                return None
            self.value[key[0]][key[1]][key[2]][key[3]] = item

    def __repr__(self):
        return join('', self) + str(self.small_value())

    __str__ = __repr__

    def small_value(self, new=False):
        arr = []
        if self.s_value:
            if not new:
                return self.s_value
            else:
                arr = list(str(self.s_value))
        if not arr:
            arr = [sgn.cell]*9
        for i in range(self.size):
            for s in game_signs:
                if self[i//3][i % 3].winxo(s) and\
                        arr[i] == sgn.cell:
                    arr[i] = s
        return Board(join('', arr))

    def board_text(self, last_turn=()):
        if last_turn and last_turn[0] == 9:
            last_turn = last_turn[2:]*2
        if last_turn:
            self[last_turn] = new_game_signs[self[last_turn]]
            self[last_turn[2:]] = Board(''.join([
                new_game_signs[i]
                for row in self[last_turn[2:]]
                for i in row
            ]))
        b = '\n\n'.join(
            ['\n'.join(
                [join('   ', [self[i][j][k] for j in range(3)])
                 for k in range(3)]
            ) for i in range(3)]
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

    def winxo(self, sgn):
        return self.small_value().winxo(sgn)

    def game_Buttons(self,
                     l_t=(),
                     game_sign=cnst.friend,
                     user_language=tg_user().lang()
                     ):
        if l_t:
            board = self[l_t[2:]]
            if not board or (
                len(re.findall(sgn.cell, str(board))) == 1 and
                str(board).index(sgn.cell) == l_t[0]*3+l_t[1]
            ):
                l_t = ()
                board = self.small_value()
        else:
            board = self.small_value()
        if not l_t:
            l_t = (9,)*4
        markup = InlineButtons(
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
                for i in range(3)
                for j in range(3)
            )
            +
            (
                (user_language.dotie,
                    f'tie{l_t[0]}{l_t[1]}{l_t[2]}{l_t[3]}'),
                (user_language.giveup,
                    f'giveup{l_t[0]}{l_t[1]}{l_t[2]}{l_t[3]}')
            ) * bool(user_language),
            width=3
        )
        markup.add(telebot.types.InlineKeyboardButton(
            user_language.rules,
            url='https://mathwithbaddrawings.com/2013/06/16/ultimate-tic-tac-toe/'
        ))
        return markup


class xo_text:

    def __init__(self, id, new=False):
        self.id = id
        self.isX = 0
        self.b = ''
        Cur.execute(
            '''
                SELECT *
                FROM xo_text
                WHERE id = ?
            ''', [self.id])
        if tuple(Cur):
            if not new:
                return self.pull()
            self.dlt()
        if new:
            Cur.execute('''
                INSERT INTO xo_text
                VALUES (?,?,?)
                ''', (
                self.id, str(self.isX), self.b
            )
            )
            Conn.commit()

    def push(self):
        Cur.execute('''
            UPDATE xo_text
            SET isX = ?, b = ?
            WHERE id = ?
            ''', [
            str(self.isX),
            str(self.b),
            self.id
        ])
        Conn.commit()

    def pull(self):
        Cur.execute(
            '''
                SELECT *
                FROM xo_text
                WHERE id = ?
                ''', [self.id]
        )
        isX, b = tuple(Cur)[0][1:]
        self.isX = int(isX)
        self.b = Board(b)

    def dlt(self):
        Cur.execute('''
            DELETE
            FROM xo_text
            WHERE id = ?
            ''', [self.id])
        Conn.commit()


class xo:

    def __init__(self, id, new=False):
        self.id = id
        Cur.execute(
            '''
                SELECT *
                FROM xo
                WHERE id = ?
            ''', (self.id,)
        )
        if tuple(Cur):
            if not new:
                return self.pull()
            self.dlt()
            return None
        self._set()
        Cur.execute('''
            INSERT INTO xo
            VALUES (?,?,?,?,?,?,?,?)
            ''', (
            self.id, str(self.plX), str(self.plO),
            str(self.giveup_user), self.queue,
            str(self.b), self.s, self.tie_id
        )
        )
        Conn.commit()

    def push(self):
        list_to_set = ', '.join((
            f'{name} = "{value}"'
            for name, value in self.__dict__.items()
        ))
        Cur.execute(f'''
            UPDATE xo
            SET   {list_to_set}
            WHERE id = ?
            ''', [self.id])
        Conn.commit()

    def pull(self):
        Cur.execute(
            '''
                SELECT *
                FROM xo
                WHERE id = ?
            ''', (self.id,)
        )
        cr = tuple(Cur)
        if not cr:
            self._set()
            return None
        self._set(*cr[0])

    def upd_id(self, new_id):
        Cur.execute('''
            UPDATE xo
            SET id = ?
            WHERE id =       ?
            ''', [new_id, self.id])
        Conn.commit()
        self.id = new_id

    def dlt(self):
        Cur.execute('''
            DELETE
            FROM xo
            WHERE id = ?
            ''', [self.id])
        Conn.commit()

    def _set(self, *args,
             plX=tg_user(), plO=tg_user(),
             giveup_user=tg_user(), queue=1,
             b='', s=3, tie_id=0
             ):
        if args:
            id, plX, plO, giveup_user, queue, b, s, tie_id = args
        self.plX = tg_user(plX)
        self.plO = tg_user(plO)
        self.giveup_user = tg_user(giveup_user)
        self.queue = int(queue)
        self.b = Board_9(b) if int(s) == 9 else Board(b)
        self.s = int(s)
        self.tie_id = int(tie_id)

    def __bool__(self):
        Cur.execute(
            '''
            SELECT *
            FROM xo
            WHERE id = ?
            ''', (self.id,)
        )
        return bool(bool(tuple(Cur)) and (self.tie_id or bool(self.giveup_user)))

    def __repr__(self):
        return str(self.__dict__)

    __str__ = __repr__

    def game_language(self):
        ul1 = self.plX.lang()
        ul2 = self.plO.lang()
        if ul1 == ul2:
            return ul1
        return lang(*(
            (k1 + '\n' + k2
                if type(k1) == str else
                (merge_user_languages(k1, k2))
             )
            for k1, k2 in zip(ul1, ul2)
        ))

    def end(self, g_type, index_last_turn=None, text=''):
        name_X = self.plX.first_name
        name_O = self.plO.first_name
        ul = self.game_language()
        if g_type == 'giveup':
            self.queue = int(self.giveup_user == self.plO)
        text += '\n'
        if g_type == 'tie':
            text +=\
                f'{sgn.x} {name_X} {cnst.tie} {name_O} {sgn.o}\n' +\
                ul.cnld*bool(self.b)
        elif g_type in ('win', 'giveup'):
            text +=\
                f'{sgn.x} {name_X} {end_signs[self.queue]}\n' +\
                f'{sgn.o} {name_O} {end_signs[not self.queue]}\n'
        elif g_type:
            text +=\
                f'{sgn.x} {name_X}\n' +\
                f'{sgn.o} {name_O}\n'
        if g_type == 'giveup':
            text += ul.player(self.giveup_user.first_name)
        b_text = self.b.board_text(index_last_turn)
        button = self.b.end_game_Buttons(current_chat=True)
        bot.edit_message_text(
            b_text + text,
            inline_message_id=self.id,
            reply_markup=button
        )
        if index_last_turn:
            self.Timeout(5, '\n'+text)
        else:
            self.dlt()

    def game_xo(self, choice):
        if self.s == 9:
            return self.game_xo_9(choice)
        ul = self.game_language()
        name_X = self.plX.first_name
        name_O = self.plO.first_name
        if choice:
            self.b[choice] = game_signs[self.queue]
            if self.b.winxo(self.b[choice]):
                return self.end('win', choice)
            elif not self.b:
                return self.end('tie', choice)
        if sgn.x in str(self.b) or sgn.o in str(self.b):
            self.queue = int(not self.queue)  # pass turn
        self.push()
        return bot.edit_message_text(
            ul.to_win(how_many_to_win[self.s]) + '\n' +
            f'{sgn.x} {name_X}{cnst.turn*self.queue}\n' +
            f'{sgn.o} {name_O}{cnst.turn*(not self.queue)}',
            inline_message_id=self.id,
            reply_markup=self.b.game_Buttons(
                choice, cnst.friend, ul
            )
        )

    def game_xo_9(self, choice):
        ul = self.game_language()
        name_X = self.plX.first_name
        name_O = self.plO.first_name
        last_turn = ()
        if choice and choice[0] != 9:
            last_turn = choice
            self.b[choice] = game_signs[self.queue]
            self.b.s_value = self.b.small_value(True)
            if self.b.winxo(self.b[choice]):
                return self.end('win', choice)
            elif not self.b:
                return self.end('tie', choice)
        if (sgn.x in str(self.b) or sgn.o in str(self.b)) and\
                last_turn:
            self.queue = int(not self.queue)  # pass turn
        elif choice:
            last_turn = choice[2:]*2
        self.push()
        return bot.edit_message_text(
            self.b.board_text(last_turn) + '\n\n' +
            f'{sgn.x} {name_X}{cnst.turn*self.queue}\n' +
            f'{sgn.o} {name_O}{cnst.turn*(not self.queue)}',
            inline_message_id=self.id,
            reply_markup=self.b.game_Buttons(
                choice, cnst.friend, ul
            )
        )

    def Timeout(self, temp_time, g_type, last_turn=()):
        system(
            'python3 timeout_.py -i {} -t {} -x "{}" -l "{}" &'.format(
                self.id, temp_time, g_type, ''.join(map(str, last_turn))
            )
        )

    def Timeout_confirm(self, g_type, pl, l_t):
        ul = self.game_language()
        another_user = (self.plX, self.plO)[pl == self.plX]
        _user = another_user if g_type == 'tie' else pl
        ul_user = _user.lang()
        text = eval(f"ul_user.confirm_{g_type}")
        buttons = InlineButtons((
            (ul_user.cnf, f'confirm_{g_type}{l_t}'),
            (ul.cnl, f'cancelend{l_t}')
        ))
        bot.edit_message_text(
            f'<a href="tg://user?id={_user.id}">{_user.first_name}</a>,\n{text}',
            # f'[{_user.first_name}](tg://user?id={_user.id}),\n{text}',
            inline_message_id=self.id,
            reply_markup=buttons,
            parse_mode='HTML'
        )
        self.Timeout(30, g_type, l_t)


def free(board_cell):
    return board_cell not in game_signs


def merge_user_languages(k1, k2):
    return lambda n: k1(n) + '\n' + k2(n)


def join(strg, arr_to_str):
    return strg.join(map(str, arr_to_str))


def InlineButtons(Buttons, width=3):
    temp_buttons = telebot.types.InlineKeyboardMarkup(
        row_width=width if width else len(Buttons[0]))
    temp_buttons.add(*[
        telebot.types.InlineKeyboardButton(
            button[0],
            callback_data=button[1]
        ) for button in Buttons])
    return temp_buttons


def main_menu_Buttons():
    return InlineButtons([
        [sgn.x, cnst.repeat + sgn.x],
        [sgn.o, cnst.repeat + sgn.o]
    ])


def _InlineButtons_(Buttons, width=3):
    temp_buttons = telebot.types.InlineKeyboardMarkup(
        row_width=width if width else len(Buttons[0]))
    temp_buttons.add(*[
        telebot.types.InlineKeyboardButton(
            button['text'],
            url=button.get('url'),
            callback_data=button.get('callback'),
            switch_inline_query=button.get('another_chat'),
            switch_inline_query_current_chat=button.get('current_chat'),
            callback_game=button.get('game'),
            pay=button.get('pay')
        ) for i in Buttons for button in i])
    return temp_buttons


lock = threading.Lock()

# database initialization
Conn = sqlite3.Connection(path_to_db, check_same_thread=False)
Cur = Conn.cursor()
