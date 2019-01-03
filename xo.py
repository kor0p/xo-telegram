import telebot
from config import *
from random import randint


@bot.callback_query_handler(search_callback('reset_start'))
@bot.message_handler(commands=['start', 'new', 'game'])
def start(message):
    pl = tg_user(message.from_user)
    ul = pl.lang()  # ul for user language
    try:
        if 'new' in message.text:
            bot.delete_message(
                pl.id,
                bot.send_message(
                    pl.id,
                    ul['start'],
                    reply_markup=telebot.types.
                    ReplyKeyboardRemove(selective=False)
                )   .message_id,
            )
    except:
        pass
    bot.send_message(
        pl.id,
        ul['start'],
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
            f'{o_sgn} {ul["bot"]}'
        g.isX = 1
        g.b = cell * 9
    elif text == o_sgn:
        text_out = f'{x_sgn} {ul["bot"]}\n' +\
            f'{o_sgn} {name}{turn_sgn}'
        g.isX = 0
        g.b = cell * 4 + x_sgn + cell * 4
    bot.edit_message_text(
        text_out,
        pl.id,
        c.message.message_id,
        reply_markup=game_Buttons(g.b, 3, robot_sgn, -1)
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
            text=ul['don’t touch']
        )
    choice = int(c.data[1:])
    g.b = g.b[:choice] + usr_sign + g.b[choice + 1:]
    try:
        assert g.b[4]
    except BaseException:
        return bot.edit_message_text(
            ul['don’t touch'],
            m.chat.id,
            m.message_id,
            reply_markup=end_game_Buttons(3, current_chat=False)
        )
    bot_choice = bot_choice_func(g.b, bot_sign, usr_sign)
    if free(g.b[4]):
        bot_choice = 4
    if bot_choice > -1:
        g.b = g.b[:bot_choice] + bot_sign + g.b[bot_choice + 1:]
    name_X = [ul['bot'], player][g.isX]
    name_O = [ul['bot'], player][not g.isX]
    b = g.b
    for s in x_sgn, o_sgn:
        queue = int(s != o_sgn)
        if winxo(b, s, 3):
            b_text = board_text(b, 3, None)
            sign_X = end_signs[queue]
            sign_O = end_signs[not queue]
            bot.edit_message_text(
                b_text +
                f'\n{x_sgn} {name_X} {sign_X}' +
                f'\n{o_sgn} {name_O} {sign_O}\n' +
                ul['new'],
                m.chat.id,
                m.message_id,
                reply_markup=end_game_Buttons(3, current_chat=False)
            )
            return g.dlt()
    if cell not in b:
        b_text = board_text(b, 3, None)
        bot.edit_message_text(
            b_text +
            f'\n{x_sgn}{name_X} {tie_sgn} {name_O}{o_sgn}\n' +
            ul['new'] + '\n',
            m.chat.id,
            m.message_id,
            reply_markup=end_game_Buttons(3, current_chat=False)
        )
        return g.dlt()
    bot.edit_message_text(
        f'{x_sgn} {name_X}{turn_sgn*g.isX}\n' +
        f'{o_sgn} {name_O}{turn_sgn*(not g.isX)}',
        m.chat.id,
        m.message_id,
        reply_markup=game_Buttons(b, 3, robot_sgn, -1)
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
        s = randint(3, 8)
        query = query.replace('r', '')
    button = InlineButtons([
        (f'{i}', f'start{i}')
        for i in range(3, 9)
    ]+[
        (ul['random'], 'start0')
    ])
    res = [telebot.types.InlineQueryResultPhoto(
        f'{n}{s}{q.id}',
        f't.me/be_utest/{2790+2*n}',
        f't.me/be_utest/{2791+2*n}',
        reply_markup=button,
        input_message_content=telebot.types.
        InputTextMessageContent(ul['startN'])
    ) for sign, n in [['x', 1], ['o', 2]]
        if (sign in query) or not query]
    return bot.answer_inline_query(q.id, res)


@bot.chosen_inline_handler(func=lambda cr: cr)
def chosen_inline_query(cr):
    g = xo(cr.result_id[2:])
    g.upd_id(cr.inline_message_id)
    if cr.result_id[0] == '1':
        g.plX = tg_user(cr.from_user)
    elif cr.result_id[0] == '2':
        g.plO = tg_user(cr.from_user)
    g.s = int(cr.result_id[1])
    if g.s == 0:
        g.push()
        return 1
    g.b = ''.join([cell for i in range(g.s**2)])
    name_X = g.plX.first_name
    name_O = g.plO.first_name
    button = game_Buttons(g.b, g.s, friend_sgn, -1)
    bot.edit_message_text(
        inline_message_id=g.id,
        text=f'{x_sgn} {name_X}{turn_sgn}\n' +
        f'{o_sgn} {name_O}',
        reply_markup=button
    )
    g.push()


@bot.callback_query_handler(search_callback('choice_size'))
def choice_size(c):
    g = xo(c.inline_message_id)
    g.s = int(c.data[-1])
    if g.s == 0:
        g.s = randint(3, 8)
    g.b = ''.join([cell for i in range(g.s**2)])
    if not g.plX and g.plO.id != c.from_user.id:
        g.plX = tg_user(c.from_user)
    elif not g.plO and g.plX.id != c.from_user.id:
        g.plO = tg_user(c.from_user)
    name_X = g.plX.first_name
    name_O = g.plO.first_name
    button = game_Buttons(g.b, g.s, friend_sgn, -1)
    bot.edit_message_text(
        inline_message_id=g.id,
        text=f'{x_sgn} {name_X}{turn_sgn}\n' +
        f'{o_sgn} {name_O}',
        reply_markup=button
    )
    g.push()


@bot.callback_query_handler(search_callback('confirm/end'))
def confirm_or_end(c):
    pl = tg_user(c.from_user)
    g = xo(c.inline_message_id)
    name_X = g.plX.first_name
    name_O = g.plO.first_name
    ul1 = g.plX.lang()
    ul2 = g.plO.lang()
    if ul1 == ul2:
        ul = ul1
    else:
        ul = {k: (ul1[k] + '\n' + ul2[k]
                  if type(ul1[k]) == str else
                  (merge_user_languages(ul1[k], ul2[k])))
              for k in ul1
              }
    if c.data == 'cancelend':
        if pl.id in [g.plX.id, g.plO.id]:
            g.tie_id = 0
            g.giveup_user = tg_user(tg_user_default)
            g.push()
            button = game_Buttons(g.b, g.s, friend_sgn, -1)
            return bot.edit_message_text(
                inline_message_id=g.id,
                text=f'{x_sgn} {name_X}{turn_sgn*g.queue}\n' +
                f'{o_sgn} {name_O}{turn_sgn*(not g.queue)}',
                reply_markup=button
            )
        return bot.answer_callback_query(
            c.id,
            ul['don’t touch'],
            show_alert=True
        )
    elif c.data == 'cancelstart':
        g.dlt()
        return bot.edit_message_text(
            inline_message_id=g.id,
            text=ul['cnld']
        )
    elif c.data == 'tie':
        if g.plX and g.plO and\
                pl.id in [g.plX.id, g.plO.id]:
            g.tie_id = pl.id
            g.push()
            button = InlineButtons([
                (ul['cnf'], 'confirmtie'), (ul['cnl'], 'cancelend')
            ])
            return bot.edit_message_text(
                ul['confirmtie'],
                inline_message_id=g.id,
                reply_markup=button
            )
        return bot.answer_callback_query(
            c.id,
            ul['don’t touch'],
            show_alert=True
        )
    elif g.tie_id:
        if g.plX and g.plO and\
            pl.id in [g.plX.id, g.plO.id] and\
                g.tie_id != pl.id:
            return end(
                g,
                f'{x_sgn} {name_X} {tie_sgn} {name_O} {o_sgn}\n' +
                ul['cnld'],
                None
            )
        return bot.answer_callback_query(
            c.id,
            ul['don’t touch'],
            show_alert=True
        )
    elif c.data == 'giveup':
        if (g.plX or g.plO) and\
                pl.id in [g.plX.id, g.plO.id]:
            g.giveup_user = tg_user(c.from_user)
            g.push()
            button = InlineButtons([
                (ul['cnf'], 'confirmloss'),
                (ul['cnl'], 'cancelend')
            ])
            return bot.edit_message_text(
                ul['confirmloss'],
                inline_message_id=g.id,
                reply_markup=button
            )
        return bot.answer_callback_query(
            c.id,
            ul['don’t touch'],
            show_alert=True
        )
    elif g.giveup_user:
        if g.giveup_user.id == pl.id and (g.plO or g.plX):
            g.queue = int(g.plO.id == pl.id)
            sign_X = end_signs[g.queue]
            sign_O = end_signs[not g.queue]
            return end(
                g,
                f'{x_sgn} {name_X} {sign_X}\n' +
                f'{o_sgn} {name_O} {sign_O}\n' +
                ul['player'](g.giveup_user.first_name),
                None
            )
        return bot.answer_callback_query(
            c.id,
            ul['don’t touch'],
            show_alert=True
        )


@bot.callback_query_handler(search_callback('friend'))
def main_xo(c):
    first_turn = False
    pl = tg_user(c.from_user)
    g = xo(c.inline_message_id)
    name_X = g.plX.first_name
    name_O = g.plO.first_name
    ul1 = g.plX.lang()
    ul2 = g.plO.lang()
    if ul1 == ul2:
        ul = ul1
    else:
        ul = {k: (ul1[k] + '\n' + ul2[k]
                  if type(ul1[k]) == str else
                  (merge_user_languages(ul1[k], ul2[k])))
              for k in ul1
              }
    if not free(c.data[1:]):
        return bot.answer_callback_query(
            c.id,
            text=ul['don’t touch'],
            show_alert=True
        )
    if (g.plX or g.plO) and\
        ((pl == g.plX and not g.queue) or
         (pl == g.plO and g.queue)):
        return bot.answer_callback_query(c.id, text=ul['stop'])
    if not g.plX and g.queue and pl != g.plO:
        g.plX = tg_user(c.from_user)
        bot.answer_callback_query(c.id, text=ul['start-pl-2'])
    if g.plX and pl == g.plX:
        if g.queue:
            return game_xo(g, int(c.data[1:]), ul)
        return bot.answer_callback_query(c.id, text=ul['stop'])
    elif g.plX and not g.plO:
        first_turn = True
        bot.answer_callback_query(c.id, text=ul['start-pl-2'])
        g.plO = tg_user(c.from_user)
        name_O = g.plO.first_name
        g.push()
    if g.plX and not g.queue and pl == g.plO:
        return game_xo(g, int(c.data[1:]), ul)
    if first_turn:
        button = game_Buttons(g.b, g.s, friend_sgn, -1)
        return bot.edit_message_text(
            inline_message_id=g.id,
            text=f'{x_sgn} {name_X}{turn_sgn*g.queue}\n' +
            f'{o_sgn} {name_O}{turn_sgn*(not g.queue)}',
            reply_markup=button
        )
    return bot.answer_callback_query(c.id, text=ul['stop+game'])

bot.remove_webhook()
# webhook_func(bot)
bot.polling(none_stop=True)
