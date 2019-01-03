import telebot
import cherrypy
import threading
import sqlite3
import re
from time import sleep
from secure_config import (
    token, ip_address, port, path_to_db
)
headers = cherrypy.request.headers
body = cherrypy.request.body

bot = telebot.TeleBot(token)

WEBHOOK_HOST = ip_address
WEBHOOK_PORT = port
WEBHOOK_LISTEN = '0.0.0.0'
# on some servers need to be as WEBHOOK_HOST
WEBHOOK_SSL_CERT = '../webhook/webhook_cert.pem'
WEBHOOK_SSL_PRIV = '../webhook/webhook_pkey.pem'
WEBHOOK_URL_BASE = 'https://%s:%s' % (WEBHOOK_HOST, WEBHOOK_PORT)
WEBHOOK_URL_PATH = '/%s/' % token

languages = {
    'en': {
        'start': 'Choose your side and get started!',
        'bot': 'Bot',
        'don’t touch': 'Oh, don’t touch this)',
        'cnld': 'Canceled',
        'new': 'Start a new game?',
        'to_win': lambda s: f'{s} in the row to win!',
        'stop': 'Stop! Wait your turn',
        'stop+game': 'Stop! There already playing',
        'dotie': 'Tie',
        'confirmtie': 'Accept tie?',
        'confirmloss': 'Confirm giving up!',
        'start-pl-2': 'Let’s go!',
        'player': lambda n: f'Player {n} gives up',
        'giveup': 'Give up',
        'cnf': 'Confirm',
        'cnl': 'Cancel',
        'startN': 'Choose size and get started!',
        'random': 'Random'
    }, 'uk': {
        'start': 'Обирай сторону і почнімо!',
        'bot': 'Бот',
        'don’t touch': 'Ой, сюди не тикай)',
        'cnld': 'Відмінено',
        'new': 'Зіграємо ще раз?',
        'to_win': lambda s: f'{s} поспіль для перемоги!',
        'stop': 'Стоп! Не твій хід)',
        'stop+game': 'Стоп! Тут уже грають)',
        'dotie': 'Нічия',
        'confirmtie': 'Приймаєш нічию?',
        'confirmloss': 'Підтвердь поразку!',
        'start-pl-2': 'Почнімо!',
        'player': lambda n: f'Гравець {n} здався',
        'giveup': 'Здатися',
        'cnf': 'Підтверджую',
        'cnl': 'Відміна',
        'startN': 'Обирай тип і до бою!',
        'random': 'Однаково'
    }, 'ru': {
        'start': 'Выбери сторону и начнём!',
        'bot': 'Бот',
        'don’t touch': 'Ой, да не тыкай сюда!',
        'cnld': 'Отменено',
        'new': 'Сыграем ещё раз?',
        'to_win': lambda s: f'{s} в ряд для победы!',
        'stop': 'Стопэ! Не твой ход!',
        'stop+game': 'Стопэ! Здесь уже играют!',
        'dotie': 'Ничья',
        'confirmtie': 'Принимаешь ничью?',
        'confirmloss': 'Подтвердите проиграш!',
        'start-pl-2': 'Начнём!',
        'player': lambda n: f'Игрок {n} сдался',
        'giveup': 'Сдаться',
        'cnf': 'Подтверждаю',
        'cnl': 'Отмена',
        'startN': 'Выбери тип и к бою!',
        'random': 'Рандом'
    }
}

# constants
how_many_to_win = {
    3: 3,
    4: 4, 5: 4, 6: 4,
    7: 5, 8: 5
}

cell = '⬜'

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
        return self.__repr__() != str(tg_user_default)

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
        if list(Cur):
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
            self.b,
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
        isX, b = list(Cur)[0][1:]
        self.isX = int(isX)
        self.b = b

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
            ''', [self.id])
        if list(Cur):
            if not new:
                return self.pull()
            self.dlt()
            return None
        self.plX = self.plO = self.giveup_user\
            = tg_user(tg_user_default)
        self.queue = 1
        self.b = ''
        self.s = 3
        self.tie_id = 0
        Cur.execute('''
            INSERT INTO xo
            VALUES (?,?,?,?,?,?,?,?)
            ''', (
            self.id, str(self.plX), str(self.plO),
            str(self.giveup_user), self.queue,
            self.b, self.s, self.tie_id
        )
        )
        Conn.commit()

    def push(self):
        list_to_set = ', '.join([
            f'{name} = "{value}"'
            for name, value in self.__dict__.items()
        ])
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
            ''', [self.id]
        )
        id,\
            plX, plO, giveup_user,\
            queue, b, s, tie_id = list(Cur)[0]
        self.plX = tg_user(plX)
        self.plO = tg_user(plO)
        self.giveup_user = tg_user(giveup_user)
        self.b = b
        self.queue = int(queue)
        self.s = int(s)
        self.tie_id = int(tie_id)

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

    def __repr__(self):
        return str(self.__dict__)

    def __str__(self):
        # same as __repr__
        return str(self.__dict__)


def free(a): return a not in game_signs


def merge_user_languages(ul1, ul2):
    return lambda n: ul1(n) + '\n' + ul2(n)


def last_of_three(b, x, y, z, s): return \
    z if b[x] == b[y] == s and free(b[z]) else\
    y if b[x] == b[z] == s and free(b[y]) else\
    x if b[y] == b[z] == s and free(b[x]) else -1


def board_text(board, size, last_turn):
    b = ''
    for i in range(size):
        for j in range(size):
            key = i * size + j
            b += new_game_signs[board[key]]\
                if last_turn == key else board[key]
        b += '\n'
    return b


def winxo(board, sgn, size):
    assert 9 > size > 2
    row = how_many_to_win[size]
    # one system for all sizes
    # easy to manage
    for i in range(size + 1 - row):
        for j in range(size + 1 - row):
            if all([board[i+q+(j+q)*size] == sgn
                    for q in range(row)]) or\
                    all([board[i+row-1-q+(j+q)*size] == sgn
                         for q in range(row)]):
                return True
            for l in range(row):
                if all([board[i+q+(j+l)*size] == sgn
                        for q in range(row)]) or\
                        all([board[i+l+(j+q)*size] == sgn
                             for q in range(row)]):
                    return True
    return False


def end(g, text, index_last_turn):
    b_text = board_text(g.b, g.s, index_last_turn)
    b_text_new = board_text(g.b, g.s, -1)
    button = end_game_Buttons(g.s)
    bot.edit_message_text(
        inline_message_id=g.id,
        text=b_text + text,
        reply_markup=button
    )
    if index_last_turn:
        sleep(5)
        bot.edit_message_text(
            inline_message_id=g.id,
            text=b_text_new + text,
            reply_markup=button
        )
    g.dlt()


def game_xo(g, choice, ul):
    turn = choice
    name_X = g.plX.first_name
    name_O = g.plO.first_name
    g.b = g.b[:turn] + game_signs[g.queue] + g.b[turn + 1:]
    win = winxo(g.b, g.b[choice], g.s)
    if win:
        return end(
            g,
            f'{x_sgn} {name_X} {end_signs[g.queue]}\n' +
            f'{o_sgn} {name_O} {end_signs[not g.queue]}',
            choice
        )
    elif cell not in g.b:
        return end(
            g,
            f'{x_sgn} {name_X} {tie_sgn} {name_O} {o_sgn}',
            choice
        )
    g.queue = int(not g.queue)  # pass turn
    g.push()
    return bot.edit_message_text(
        inline_message_id=g.id,
        text=ul['to_win'](how_many_to_win[g.s]) + '\n' +
        f'{x_sgn} {name_X}{turn_sgn*g.queue}\n' +
        f'{o_sgn} {name_O}{turn_sgn*(not g.queue)}',
        reply_markup=game_Buttons(
            g.b,
            g.s,
            friend_sgn,
            choice,
            user_language=ul
        )
    )


def bot_choice_func(board, bot_sgn, user_sgn):
    if not (cell in board):
        return -1
    for s in [bot_sgn, user_sgn]:
        for i in range(3):
            for x, y, z in [[3*i, 3*i+1, 3*i+2], [i, i+3, i+6]]:
                res = last_of_three(board, x, y, z, s)
                if res > -1:
                    return res
        for x, y, z in [[0, 4, 8], [2, 4, 6]]:
            res = last_of_three(board, x, y, z, s)
            if res > -1:
                return res
    for i, j, k, l, r in [
            (1, 3, 1, 5, 2), (3, 7, 5, 7, 8),
            (2, 6, 0, 8, 1), (2, 3, 0, 5, 1),
            (3, 8, 5, 6, 7), (1, 6, 0, 7, 3),
            (1, 8, 2, 7, 5), (4, 8, 4, 8, 2)]:
        # leave this part, please, it just works!
        if (board[i] == board[j] == user_sgn or
                board[k] == board[l] == user_sgn) and free(board[r]):
            return r
    for i in range(9):
        if free(board[i]):
            return i


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


def game_Buttons(board, size, game_sign, last_turn, user_language={}):
    return InlineButtons(
        [
            (new_game_signs[board[i]]
                if int(last_turn) == i else
             board[i],
                game_sign +
                str([board[i], f'{i:02}'][board[i] == cell])
             )
            for i in range(size**2)
        ]
        +
        [
            (user_language.get('dotie'), 'tie'),
            (user_language.get('giveup'), 'giveup')
        ] * bool(user_language),
        width=size
    )


def end_game_Buttons(size, current_chat=True):
    return _InlineButtons_(
        [[
            {
                'text': x_sgn,
                'current_chat': f'x{size}'
                if current_chat else None,
                'another_chat': f'x{size}'
                if not current_chat else None
            },
            {
                'text': o_sgn,
                'current_chat': f'o{size}'
                if current_chat else None,
                'another_chat': f'o{size}'
                if not current_chat else None
            }
        ] +
            [{
                'text': robot_sgn,
                'url': 't.me/m0xbot?start=1'
            }] * current_chat +
            [{
                'text': repeat_sgn,
                'callback': repeat_sgn * 2
            }] * (not current_chat)
        ],
        width=2
    )


lock = threading.Lock()

# database initialization
Conn = sqlite3.Connection(path_to_db, check_same_thread=False)
Cur = Conn.cursor()
