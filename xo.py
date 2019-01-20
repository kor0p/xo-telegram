import telebot
from config import *
from random import randint
random_list = (randint(3, 8) for i in range(10000))


@bot.callback_query_handler(search_callback('reset_start'))
@bot.message_handler(commands=['start', 'new', 'game'])
def start(message):
    pl = tg_user(message.from_user)
    ul = pl.lang()  # ul for user language
    try:
        if 'new' not in message.text:
            pass
        bot.delete_message(
            pl.id,
            bot.send_message(
                pl.id,
                ul.start,
                reply_markup=telebot.types.
                ReplyKeyboardRemove(selective=False)
            )   .message_id,
        )
    except:
        pass
    try:
        bot.answer_callback_query(
            message.id,
            text=ul.start_pl_2
        )
    except:
        pass
    bot.send_message(
        pl.id,
        ul.start,
        reply_markup=main_menu_Buttons()
    )


@bot.callback_query_handler(search_callback('start'))
def start_xo_text(c):
    text = c.data[-1]
    pl = tg_user(c.from_user)
    ul = pl.lang()
    g = xo_text(pl.id, new=True)
    name = pl.first_name
    if text == x_sgn:
        text_out = f'{x_sgn} {name}{turn_sgn}\n' +\
            f'{o_sgn} {ul.bot}'
        g.isX = 1
        g.b = Board(cell * 9)
    elif text == o_sgn:
        text_out = f'{x_sgn} {ul.bot}\n' +\
            f'{o_sgn} {name}{turn_sgn}'
        g.isX = 0
        g.b = Board(cell * 4 + x_sgn + cell * 4)
    bot.edit_message_text(
        text_out,
        pl.id,
        c.message.message_id,
        reply_markup=g.b.game_Buttons(robot_sgn, -1)
    )
    g.push()


@bot.callback_query_handler(search_callback('text'))
def main_xo_text(c):
    m = c.message
    pl = tg_user(c.from_user)
    ul = pl.lang()
    g = xo_text(pl.id)
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
    except BaseException:
        return bot.edit_message_text(
            ul.dont_touch,
            m.chat.id,
            m.message_id,
            reply_markup=g.b.end_game_Buttons()
        )
    bot_choice = g.b.bot_choice_func(bot_sign, usr_sign)
    if free(g.b[1][1]):
        bot_choice = (1, 1)
    if bot_choice:
        g.b[bot_choice] = bot_sign
    name_X = [ul.bot, player][g.isX]
    name_O = [ul.bot, player][not g.isX]
    for s in x_sgn, o_sgn:
        queue = int(s != o_sgn)
        if g.b.winxo(s):
            b_text = g.b.board_text(-1)
            sign_X = end_signs[queue]
            sign_O = end_signs[not queue]
            bot.edit_message_text(
                b_text +
                f'\n{x_sgn} {name_X} {sign_X}' +
                f'\n{o_sgn} {name_O} {sign_O}\n' +
                ul.new,
                m.chat.id,
                m.message_id,
                reply_markup=g.b.end_game_Buttons()
            )
            return g.dlt()
    if not g.b:
        b_text = g.b.board_text(-1)
        bot.edit_message_text(
            b_text +
            f'\n{x_sgn}{name_X} {tie_sgn} {name_O}{o_sgn}\n' +
            ul.new + '\n',
            m.chat.id,
            m.message_id,
            reply_markup=g.b.end_game_Buttons()
        )
        return g.dlt()
    bot.edit_message_text(
        f'{x_sgn} {name_X}{turn_sgn*g.isX}\n' +
        f'{o_sgn} {name_O}{turn_sgn*(not g.isX)}',
        m.chat.id,
        m.message_id,
        reply_markup=g.b.game_Buttons(robot_sgn, -1)
    )
    g.push()


@bot.inline_handler(lambda q: True)
def inline_query(q):
    g = xo(q.id, new=True)
    pl = tg_user(q.from_user)
    ul = pl.lang()
    query = q.query.lower()
    s = 0
    for i in range(3, 8):
        if str(i) in query:
            s = i
            query = query.replace(str(i), '')
            break
    if 'r' in query:
        s = next(random_list)
        query = query.replace('r', '')
    button = InlineButtons(
        tuple(
            (f'{i}', f'start{i}')
            for i in range(3, 9)
        )+(
            (ul.random, 'start0'),
        )
    )
    res = (
        telebot.types.InlineQueryResultCachedSticker(
            f'{n}{s}{q.id}',
            'CAADAgADKQAD-8YTE7geSMCRsyDEAg'*(1-n) +
            'CAADAgADKAAD-8YTE4byaCljfP--Ag'*n,
            reply_markup=button,
            input_message_content=telebot.types.
            InputTextMessageContent(ul.startN)
        ) for sign, n in [['x', 0], ['o', 1]]
        if (sign in query) or not query
    )
    return bot.answer_inline_query(q.id, res)


@bot.chosen_inline_handler(func=lambda cr: cr)
def chosen_inline_query(cr):
    g = xo(cr.result_id[2:])
    g.upd_id(cr.inline_message_id)
    if cr.result_id[0] == '0':
        g.plX = tg_user(cr.from_user)
    elif cr.result_id[0] == '1':
        g.plO = tg_user(cr.from_user)
    g.s = int(cr.result_id[1])
    if g.s == 0:
        g.push()
        return 1
    g.b = Board(''.join([cell for i in range(g.s**2)]))
    g.game_xo(())
    g.push()


@bot.callback_query_handler(search_callback('choice_size'))
def choice_size(c):
    g = xo(c.inline_message_id)
    g.s = int(c.data[-1])
    if g.s == 0:
        g.s = next(random_list)
    g.b = Board(''.join([cell for i in range(g.s**2)]))
    if not g.plX and g.plO.id != c.from_user.id:
        g.plX = tg_user(c.from_user)
    elif not g.plO and g.plX.id != c.from_user.id:
        g.plO = tg_user(c.from_user)
    name_X = g.plX.first_name
    name_O = g.plO.first_name
    button = g.b.game_Buttons(friend_sgn, -1)
    bot.edit_message_text(
        f'{x_sgn} {name_X}{turn_sgn}\n' +
        f'{o_sgn} {name_O}',
        inline_message_id=g.id,
        reply_markup=button
    )
    g.push()


@bot.callback_query_handler(search_callback('confirm/end'))
def confirm_or_end(c):
    pl = tg_user(c.from_user)
    g = xo(c.inline_message_id)
    name_X = g.plX.first_name
    name_O = g.plO.first_name
    ul = g.game_language()
    ul_this = pl.lang()
    if c.data == 'cancelend':
        if pl.id in (g.plX.id, g.plO.id):
            g.tie_id = 0
            g.giveup_user = tg_user(tg_user_default)
            return g.game_xo(())
        return bot.answer_callback_query(
            c.id,
            ul_this.dont_touch,
            show_alert=True
        )
    elif c.data == 'cancelstart':
        g.dlt()
        return bot.edit_message_text(
            ul.cnld,
            inline_message_id=g.id,
        )
    elif g.tie_id:
        if g.plX and g.plO and\
            pl.id in (g.plX.id, g.plO.id) and\
                g.tie_id != pl.id:
            return g.end('tie', None)
        return bot.answer_callback_query(
            c.id,
            ul_this.dont_touch,
            show_alert=True
        )
    elif g.giveup_user:
        if g.giveup_user.id == pl.id and (g.plO or g.plX):
            g.queue = int(g.plO.id == pl.id)
            return g.end('giveup', None)
        return bot.answer_callback_query(
            c.id,
            ul_this.dont_touch,
            show_alert=True
        )
    elif c.data == 'tie':
        if g.plX and g.plO and\
                pl.id in (g.plX.id, g.plO.id):
            g.tie_id = pl.id
            g.push()
            return g.Timeout_confirm('tie', pl)
        return bot.answer_callback_query(
            c.id,
            ul_this.dont_touch,
            show_alert=True
        )
    elif c.data == 'giveup':
        if (g.plX or g.plO) and\
                pl.id in (g.plX.id, g.plO.id):
            g.giveup_user = pl
            g.queue = int(not g.queue)
            g.push()
            return g.Timeout_confirm('giveup', pl)
        return bot.answer_callback_query(
            c.id,
            ul_this.dont_touch,
            show_alert=True
        )


@bot.callback_query_handler(search_callback('friend'))
def main_xo(c):
    first_turn = False
    pl = tg_user(c.from_user)
    g = xo(c.inline_message_id)
    name_X = g.plX.first_name
    name_O = g.plO.first_name
    ul = g.game_language()
    if not free(c.data[1:]):
        return bot.answer_callback_query(
            c.id,
            text=ul.dont_touch,
            show_alert=True
        )
    choice = tuple(map(int, c.data[1:]))
    if (g.plX or g.plO) and\
        ((pl == g.plX and not g.queue) or
         (pl == g.plO and g.queue)):
        return bot.answer_callback_query(c.id, text=ul.stop)
    if not g.plX and g.queue and pl != g.plO:
        g.plX = tg_user(c.from_user)
        bot.answer_callback_query(c.id, text=ul.start_pl_2)
    if g.plX and pl == g.plX:
        if g.queue:
            return g.game_xo(choice)
        return bot.answer_callback_query(c.id, text=ul.stop)
    elif g.plX and not g.plO:
        first_turn = True
        bot.answer_callback_query(c.id, text=ul.start_pl_2)
        g.plO = tg_user(c.from_user)
        name_O = g.plO.first_name
        g.push()
    if g.plX and not g.queue and pl == g.plO:
        return g.game_xo(choice)
    if first_turn:
        return g.game_xo(())
    return bot.answer_callback_query(c.id, text=ul.stop_game)

#webhook_func(bot)
bot.remove_webhook()
bot.polling(none_stop=True)
