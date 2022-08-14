from __future__ import annotations

import json
from typing import Union, Any
from functools import wraps

import telebot.apihelper
from telebot.types import Message, CallbackQuery

from ..bot import bot
from ..button import main_menu_buttons
from ..const import CONSTS, Choice
from ..database import Users
from ..languages import Language
from ..game.text_xo import TextXO
from ..user import TGUser
from ..utils import make_html_user_url, callback


def admin_panel(fn):
    @wraps(fn)
    def _command(message: Message):
        if message.from_user.id != CONSTS.SUPER_ADMIN_USER_ID:
            return

        command, text = message.text.split('\n', 1)
        if ' ' in command:
            options = dict(option.split('=') for option in command.split(' ')[1:])
            for option, value in options.items():
                options[option] = json.loads(value)
        else:
            options = {}
        return fn(message, text, options)

    return _command


@bot.message_handler(commands=['admin:send_message'])
@admin_panel
def admin_send_message(message: Message, text: str, options: dict[str, Any]):
    options = {
        'parse_mode': 'HTML',
        'disable_notification': False,
        'disable_web_page_preview': False,
    } | options

    users = list(Users.all())
    print(users)
    for user in users:
        bot.send_message(user.id, text, **options)


@bot.callback_query_handler(callback.text__reset_start)
def start_callback(cbq: CallbackQuery):
    player = TGUser(cbq.from_user)
    bot.answer_callback_query(cbq.id, player.lang.start_pl_2)
    bot.send_message(player.id, player.lang.start, reply_markup=main_menu_buttons())


@bot.message_handler(commands=['start', 'new', 'game'])
def pre_start(message: Message):
    user = message.from_user
    try:
        bot.send_message(user.id, Language.get_localized('start', user.language_code), reply_markup=main_menu_buttons())
    except telebot.apihelper.ApiTelegramException as e:
        telebot.logger.error(e)


@bot.message_handler(commands=['request_lang'])
def request_admin_support(message: Message):
    bot.send_message(
        CONSTS.SUPER_ADMIN_USER_ID,
        f'''user: {make_html_user_url(message.from_user)}
text: <code>{message.text}</code>
json: <code>{message.json}</code>''',
    )


@bot.callback_query_handler(callback.text__start)
def start_xo_text(cbq: CallbackQuery, data: str):
    TextXO(cbq.from_user, cbq.message, new=True).start(data)


@bot.callback_query_handler(callback.text__game)
def main_xo_text(cbq: CallbackQuery, data: Union[Choice, str]):
    if isinstance(data, str) and data in CONSTS.DEFAULT_GAMES_SIGNS:
        return bot.answer_callback_query(cbq.id, Language.get_localized('dont_touch', cbq.from_user.language_code))

    TextXO(cbq.from_user, cbq.message).main(data)
