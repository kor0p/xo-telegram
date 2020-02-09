import random
import re

from telebot import types
from .boards import free
from .game import *

random_list_size = (random.choice(list_of_sizes) for _ in range(10000))
random_list = (random.choice((0,)*29+(1,)) for _ in range(10000))
lock = threading.Lock()


def search_callback(to_find):
    return lambda c: re.search(
        dict(
            reset_start=cnst.repeat * 2,
            start=cnst.repeat + f'[{sgn.x}|{sgn.o}]',
            choice_size=r'start\d',
            text=cnst.robot + fr'[\d\d|{sgn.x}|{sgn.o}]',
            friend=cnst.friend + fr'[\d\d|{sgn.x}|{sgn.o}|{cnst.lock}]',
            confirm_end='cancel|tie|giveup|confirm'
        )[to_find],
        c.data
    )


@bot.callback_query_handler(search_callback('reset_start'))
def start_callback(c):
    pl = TGUser(c.from_user)
    ul = pl.lang  # ul for user language
    bot.answer_callback_query(
        c.id,
        text=ul.start_pl_2
    )
    bot.send_message(
        pl.id,
        ul.start,
        reply_markup=main_menu_buttons()
    )


@bot.message_handler(commands=['start', 'new', 'game'])
def start(message):
    pl = TGUser(message.from_user)
    ul = pl.lang  # ul for user language
    if 'new' in message.text:
        bot.delete_message(
            pl.id,
            bot.send_message(
                pl.id,
                ul.start,
                reply_markup=types.
                ReplyKeyboardRemove(selective=False)
            ).message_id,
        )
    bot.send_message(
        pl.id,
        ul.start,
        reply_markup=main_menu_buttons()
    )


@bot.callback_query_handler(search_callback('start'))
def start_xo_text(c):
    text = c.data[-1]
    pl = TGUser(c.from_user)
    ul = pl.lang
    g = XOText(pl.id, new=True)
    name = pl.first_name
    g.b = Board(sgn.cell * 9)
    text_out = ''
    if text == sgn.x:
        text_out = f'{sgn.x} {name}{cnst.turn}\n' +\
            f'{sgn.o} {ul.bot}'
        g.isX = 1  # by default isX is 0
    elif text == sgn.o:
        text_out = f'{sgn.x} {ul.bot}\n' +\
            f'{sgn.o} {name}{cnst.turn}'
        print(g.b)
        g.b[1][1] = sgn.x
        print(g.b)
    bot.edit_message_text(
        text_out,
        pl.id,
        c.message.message_id,
        reply_markup=g.b.game_buttons((), cnst.robot)
    )
    g.push()


@bot.callback_query_handler(search_callback('text'))
def main_xo_text(c):
    print(c)
    m = c.message
    pl = TGUser(c.from_user)
    ul = pl.lang
    g = XOText(pl.id)
    player = pl.first_name
    usr_sign = game_signs[g.isX]
    bot_sign = game_signs[not g.isX]
    if not free(c.data[1:]):
        return bot.answer_callback_query(
            c.id,
            text=ul.dont_touch
        )
    choice = tuple(map(int, c.data[1:]))
    g.b[choice] = usr_sign
    try:
        assert g.b[1][1]
    except AssertionError:
        return bot.edit_message_text(
            ul.dont_touch,
            m.chat.id,
            m.message_id,
            reply_markup=g.b.end_game_buttons()
        )
    bot_choice = g.b.bot_choice_func(bot_sign, usr_sign)
    if free(g.b[1][1]):
        bot_choice = (1, 1)
    if bot_choice:
        g.b[bot_choice] = bot_sign
    name_x = [ul.bot, player][g.isX]
    name_o = [ul.bot, player][not g.isX]
    for s in sgn.x, sgn.o:
        queue = int(s != sgn.o)
        if g.b.winxo(s):
            b_text = g.b.board_text()
            sign_x = end_signs[queue]
            sign_o = end_signs[not queue]
            bot.edit_message_text(
                b_text +
                f'\n{sgn.x} {name_x} {sign_x}' +
                f'\n{sgn.o} {name_o} {sign_o}\n' +
                ul.new,
                m.chat.id,
                m.message_id,
                reply_markup=g.b.end_game_buttons()
            )
            return g.delete()
    if not g.b:
        b_text = g.b.board_text()
        bot.edit_message_text(
            b_text +
            f'\n{sgn.x}{name_x} {cnst.tie} {name_o}{sgn.o}\n' +
            ul.new + '\n',
            m.chat.id,
            m.message_id,
            reply_markup=g.b.end_game_buttons()
        )
        return g.delete()
    bot.edit_message_text(
        f'{sgn.x} {name_x}{cnst.turn*g.isX}\n' +
        f'{sgn.o} {name_o}{cnst.turn*(not g.isX)}',
        m.chat.id,
        m.message_id,
        reply_markup=g.b.game_buttons((), cnst.robot)
    )
    g.push()


@bot.inline_handler(lambda q: True)
def inline_query(q):
    print(q.id)
    XO(q.id, new=True)
    pl = TGUser(q.from_user)
    ul = pl.lang
    query = q.query.lower()
    s = 0
    for i in list_of_sizes:
        if str(i) in query:
            s = i
            query = query.replace(str(i), '')
            break
    if 'r' in query:
        s = next(random_list_size)
        query = query.replace('r', '')
    button = callback_buttons(
        tuple(
            (f'{i}', f'start{i:02}')
            for i in list_of_sizes
        )+(
            (ul.random, 'start00'),
        ), width=3
    )
    if next(random_list) or not s:
        button.add(types.InlineKeyboardButton(
            'Підтримати проект',
            url='https://send.monobank.ua/zEuxNoaWc'
        ))
    res = (
        types.InlineQueryResultCachedSticker(
            f'{n}{s:02}{q.id}',
            'CAADAgADKQAD-8YTE7geSMCRsyDEAg'*(1-n) +
            'CAADAgADKAAD-8YTE4byaCljfP--Ag'*n,
            reply_markup=button,
            input_message_content=types.InputTextMessageContent(ul.startN)
        ) for sign, n in [['o', 0], ['x', 1]]
        if (sign not in query) or not query
    )
    return bot.answer_inline_query(q.id, res)


@bot.chosen_inline_handler(func=lambda cr: cr)
def chosen_inline_query(cr):
    print(cr, 'CR')
    g = XO(cr.result_id[3:])
    g.upd_id(cr.inline_message_id)
    if cr.result_id[0] == '0':
        g.plX = TGUser(cr.from_user)
    elif cr.result_id[0] == '1':
        g.plO = TGUser(cr.from_user)
    s = int(cr.result_id[1:3])
    if s == 0:
        g.push()
        return 1
    g.timeout((s ** 2) * 30, '_')
    g.b = create_board(''.join([sgn.cell]*s**2), s)
    g.game_xo(())
    g.push()


@bot.callback_query_handler(search_callback('choice_size'))
def choice_size(c):
    print(c)
    g = XO(c.inline_message_id)
    s = int(c.data[-2:])
    if s == 0:
        s = next(random_list_size)
    g.b = create_board(''.join([sgn.cell]*s**2), s)
    if not g.plX and g.plO.id != c.from_user.id:
        g.plX = TGUser(c.from_user)
    elif not g.plO and g.plX.id != c.from_user.id:
        g.plO = TGUser(c.from_user)
    g.game_xo(())
    g.timeout((s ** 2) * 30, '_')


@bot.callback_query_handler(search_callback('confirm_end'))
def confirm_or_end(c):
    pl = TGUser(c.from_user)
    g = XO(c.inline_message_id)
    ul = g.game_language()
    ul_this = pl.lang
    choice = c.data[-4:]
    try:
        int(choice[0])
    except ValueError:
        choice = c.data[-2:]
    if 'cancelend' in c.data:
        if pl.id in (g.plX.id, g.plO.id):
            g.tie_id = 0
            g.giveup_user = TGUser()
            return g.game_xo(tuple(map(int, choice)))
        return bot.answer_callback_query(
            c.id,
            ul_this.stop_game,
            show_alert=True
        )
    elif c.data == 'cancelstart':
        g.delete()
        return bot.edit_message_text(
            ul.cnld,
            inline_message_id=g.id,
        )
    elif g.tie_id:
        if g.plX and g.plO and\
            pl.id in (g.plX.id, g.plO.id) and\
                g.tie_id != pl.id:
            return g.end('tie', tuple(map(int, choice)))
        return bot.answer_callback_query(
            c.id,
            ul_this.stop_game,
            show_alert=True
        )
    elif g.giveup_user:
        if pl == g.giveup_user and (g.plO or g.plX):
            return g.end('giveup', tuple(map(int, choice)))
        return bot.answer_callback_query(
            c.id,
            ul_this.stop_game,
            show_alert=True
        )
    elif 'tie' in c.data:
        if g.plX and g.plO and\
                pl.id in (g.plX.id, g.plO.id):
            g.tie_id = pl.id
            g.push()
            return g.timeout_confirm('tie', pl, choice)
        return bot.answer_callback_query(
            c.id,
            ul_this.dont_touch,
            show_alert=True
        )
    elif 'giveup' in c.data:
        if (g.plX or g.plO) and\
                pl.id in (g.plX.id, g.plO.id):
            g.giveup_user = pl
            if choice[0] != '9':
                g.queue = int(not g.queue)
            g.push()
            return g.timeout_confirm('giveup', pl, choice)
        return bot.answer_callback_query(
            c.id,
            ul_this.dont_touch,
            show_alert=True
        )


@bot.callback_query_handler(search_callback('friend'))
def main_xo(c):
    first_turn = False
    pl = TGUser(c.from_user)
    g = XO(c.inline_message_id)
    ul_this = pl.lang
    if not free(c.data[1:]) or c.data[1:] == cnst.lock:
        return bot.answer_callback_query(
            c.id,
            text=ul_this.dont_touch,
            show_alert=True
        )
    choice = tuple(map(int, c.data[1:]))
    if (g.plX or g.plO) and\
        ((pl == g.plX and not g.queue) or
         (pl == g.plO and g.queue)):
        return bot.answer_callback_query(c.id, text=ul_this.stop)
    if c.data[1:3] == '99':
        bot.answer_callback_query(c.id, text=ul_this.start9)
    if not g.plX and g.queue and pl != g.plO:
        g.plX = TGUser(c.from_user)
        bot.answer_callback_query(c.id, text=ul_this.start_pl_2)
    if g.plX and pl == g.plX:
        if g.queue:
            return g.game_xo(choice)
        return bot.answer_callback_query(c.id, text=ul_this.stop)
    elif g.plX and not g.plO:
        first_turn = True
        bot.answer_callback_query(c.id, text=ul_this.start_pl_2)
        g.plO = TGUser(c.from_user)
        g.push()
    if g.plX and not g.queue and pl == g.plO:
        return g.game_xo(choice)
    if first_turn:
        return g.game_xo(())
    return bot.answer_callback_query(c.id, text=ul_this.stop_game)


# bot.polling(none_stop=True)
bot.infinity_polling()
