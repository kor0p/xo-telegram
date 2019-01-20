import telebot
import cherrypy
import threading
import sqlite3
import re
from os import system
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
        'dont_touch': 'Oh, don\'t touch this)',
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
        'timeout': lambda s: f'Seconds remains: {s}'
    }, 'uk': {
        'start': 'Обирай сторону і почнімо!',
        'bot': 'Бот',
        'dont_touch': 'Ой, сюди не тикай)',
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
        'timeout': lambda s: f'Секунд лишилось: {s}'
    }, 'ru': {
        'start': 'Выбери сторону и начнём!',
        'bot': 'Бот',
        'dont_touch': 'Ой, да не тыкай сюда!',
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
        'timeout': lambda s: f'Секунд осталось: {s}'
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

cell = '⬜'
time_sgn = '⏳'
new_time_sgn = '⌛️'

x_sgn = '❌'
o_sgn = '⭕'
game_signs = [o_sgn, x_sgn]

new_x_sgn = '✖'
new_o_sgn = '🔴'
new_game_signs = {x_sgn: new_x_sgn, o_sgn: new_o_sgn, cell: cell}

win_sgn = '🏆'
lose_sgn = '☠️'
end_signs = [lose_sgn, win_sgn]

tie_sgn = '🤜🤛'
turn_sgn = ' 👈'
repeat_sgn = '🔄'
robot_sgn = '🤖'
friend_sgn = '🙎'
tg_user_default = {'id': 0, 'first_name': '?', 'language_code': 'en'}


def search_callback(to_find):
    return lambda c: re.search(
        {
            'reset_start': repeat_sgn * 2,
            'start': repeat_sgn + f'[{x_sgn}|{o_sgn}]',
            'choice_size': 'start\d',
            'text': robot_sgn + f'[\d\d|{x_sgn}|{o_sgn}]',
            'friend': friend_sgn + f'[\d\d|{x_sgn}|{o_sgn}]',
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

    def __init__(self, d):
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

    def __setitem__(self, key, item):
        self.value[key] = item

    def __getitem__(self, key):
        return self.value[key]

    def __repr__(self):
        return ''.join(self.value)

    __str__ = __repr__


class Board:

    def __init__(self, _board=''):
        self.value = _board
        self.size = s = int(len(self.value)**(.5))
        if self.size == 9:
            return Board_9(_board)
        assert 9 > self.size > 2 or not self.size
        self.value = [
            Row(self.value[i*s:(i+1)*s])
            for i in range(s)
        ]

    def __getitem__(self, key):
        s = self.size
        if type(key) == tuple:
            return self.value[key[0]][key[1]]
        if type(key) == slice:
            start, stop = key.start, key.stop
            if not start:
                start = 0
            if not stop:
                stop = s-1
            return self.value[start*s:(stop+1)*s]
        if key >= s:
            raise IndexError('board index out of range')
        return Row(self.value[key])

    def __setitem__(self, key, item):
        if key and type(key) == tuple:
            self.value[key[0]][key[1]] = item

    def __bool__(self):
        return (cell in str(self.value))

    def __repr__(self):
        return ''.join(list(map(str, self)))

    __str__ = __repr__

    def last_of_three(self, a, b, c, sign):
        for x, y, z in [[a, b, c], [c, a, b], [b, c, a]]:
            if self[x] == self[y] == sign and free(self[z]):
                return z
        return ()

    def board_text(self, last_turn):
        b = ''
        for i in range(self.size):
            for j in range(self.size):
                b += new_game_signs[self[i][j]]\
                    if last_turn == (i, j) else self[i][j]
            b += '\n'
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
        for s in [bot_sgn, user_sgn]:
            for x, y, z in (
                ((0, 0), (1, 1), (2, 2)),  # . 0 1 2
                ((0, 2), (1, 1), (2, 0)),  # 0 . . .
                ((0, 0), (1, 0), (2, 0)),  # 1 . . .
                ((0, 0), (0, 1), (0, 2)),  # 2 . . .
                ((0, 1), (1, 1), (2, 1)),
                ((1, 0), (1, 1), (1, 2)),
                ((0, 2), (1, 2), (2, 2)),
                ((2, 0), (2, 1), (2, 2))
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
        # lasr hope :)
        for i in range(3):
            for j in range(3):
                if free(self[i][j]):
                    return i, j

    def game_Buttons(self, game_sign, last_turn,
                     user_language=tg_user(tg_user_default).lang()):
        return InlineButtons(
            tuple(
                (new_game_signs[self[i][j]]
                 if last_turn == (i, j) else
                 self[i][j],
                 game_sign +
                 str((self[i][j], f'{i}{j}')[self[i][j] == cell])
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
                    'text': x_sgn,
                    'current_chat': f'x{self.size}'
                    if current_chat else None,
                    'another_chat': f'x{self.size}'
                    if not current_chat else None
                },
                {
                    'text': o_sgn,
                    'current_chat': f'o{self.size}'
                    if current_chat else None,
                    'another_chat': f'o{self.size}'
                    if not current_chat else None
                }
            ] + [[
                {
                    'text': repeat_sgn,
                    'callback': repeat_sgn * 2
                },
                {
                    'text': robot_sgn,
                    'url': 't.me/m0xbot?start=1'
                }
            ][current_chat]
            ]],
            width=2
        )


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
        self.Timeout(self.s*180, '_')

    def dlt(self):
        Cur.execute('''
            DELETE
            FROM xo
            WHERE id = ?
            ''', [self.id])
        Conn.commit()

    def _set(self, *args,
             plX=tg_user_default, plO=tg_user_default,
             giveup_user=tg_user_default, queue=1,
             b='', s=3, tie_id=0
             ):
        if args:
            id, plX, plO, giveup_user, queue, b, s, tie_id = args
        self.plX = tg_user(plX)
        self.plO = tg_user(plO)
        self.giveup_user = tg_user(giveup_user)
        self.queue = int(queue)
        self.b = Board(b)
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
        return bool(tuple(Cur))

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

    def end(self, g_type, index_last_turn, text=''):
        name_X = self.plX.first_name
        name_O = self.plO.first_name
        ul = self.game_language()
        text += '\n'
        if g_type == 'tie':
            text +=\
                f'{x_sgn} {name_X} {tie_sgn} {name_O} {o_sgn}\n' +\
                ul.cnld*bool(self.b)
        elif g_type == 'win' or g_type == 'giveup':
            text += \
                f'{x_sgn} {name_X} {end_signs[self.queue]}\n' +\
                f'{o_sgn} {name_O} {end_signs[not self.queue]}\n'
        elif g_type:
            text +=\
                f'{x_sgn} {name_X}\n' +\
                f'{o_sgn} {name_O}\n'
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
            self.Timeout(
                5,
                '\n'+self.b.board_text(None)+text
            )
        self.dlt()

    def game_xo(self, choice):
        ul = self.game_language()
        name_X = self.plX.first_name
        name_O = self.plO.first_name
        if choice:
            self.b[choice] = game_signs[self.queue]
            if self.b.winxo(self.b[choice]):
                return self.end('win', choice)
            elif not self.b:
                return self.end('tie', choice)
        if x_sgn in str(self.b) or o_sgn in str(self.b):
            self.queue = int(not self.queue)  # pass turn
        self.push()
        return bot.edit_message_text(
            ul.to_win(how_many_to_win[self.s]) + '\n' +
            f'{x_sgn} {name_X}{turn_sgn*self.queue}\n' +
            f'{o_sgn} {name_O}{turn_sgn*(not self.queue)}',
            inline_message_id=self.id,
            reply_markup=self.b.game_Buttons(
                friend_sgn, choice, user_language=ul
            )
        )

    def Timeout(self, temp_time, g_type):
        system(
            'python3 timeout_.py -i {} -t {} -x "{}" &'.format(
                self.id, temp_time, g_type
            )
        )

    def Timeout_confirm(self, g_type, pl):
        ul = self.game_language()
        another_user = (self.plX, self.plO)[pl == self.plX]
        _user = another_user if g_type == 'tie' else pl
        ul_user = _user.lang()
        text = eval(f"ul_user.confirm_{g_type}")
        buttons = InlineButtons((
            (ul_user.cnf, 'confirm_'+g_type),
            (ul.cnl, 'cancelend')
        ))
        bot.edit_message_text(
            f'[{_user.first_name}](tg://user?id={_user.id}),\n{text}',
            inline_message_id=self.id,
            reply_markup=buttons,
            parse_mode='Markdown'
        )
        self.Timeout(30, g_type)
        return 1


def free(board_cell):
    return board_cell not in game_signs


def merge_user_languages(k1, k2):
    return lambda n: k1(n) + '\n' + k2(n)


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
        [x_sgn, repeat_sgn + x_sgn],
        [o_sgn, repeat_sgn + o_sgn]
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
