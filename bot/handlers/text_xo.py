from __future__ import annotations

from typing import Union

from telebot.types import Message, CallbackQuery

from ..bot import bot
from ..button import main_menu_buttons
from ..const import CONSTS, SIGNS_TYPE, UserSigns, Choice
from ..languages import Language
from ..game.text_xo import TextXO
from ..user import TGUser
from ..utils import get_markdown_user_url, callback


@bot.callback_query_handler(callback.text__reset_start)
def start_callback(cbq: CallbackQuery):
    player = TGUser(cbq.from_user)
    bot.answer_callback_query(cbq.id, player.lang.start_pl_2)
    bot.send_message(player.id, player.lang.start, reply_markup=main_menu_buttons())


@bot.message_handler(commands=['start', 'new', 'game'])
def pre_start(message: Message):
    user = message.from_user
    bot.send_message(user.id, Language.get_localized('start', user.language_code), reply_markup=main_menu_buttons())


@bot.message_handler(commands=['request_lang'])
def request_admin_support(message: Message):
    bot.send_message(
        CONSTS.SUPER_ADMIN_USER_ID,
        f'''user: {get_markdown_user_url(message.from_user)}
text: `{message.text}`
json: `{message.json}`''',
        parse_mode='Markdown',
    )


@bot.callback_query_handler(callback.text__start)
def start_xo_text(cbq: CallbackQuery, data: SIGNS_TYPE):
    TextXO(cbq.from_user, cbq.message, new=True).start(data)


@bot.callback_query_handler(callback.text__game)
def main_xo_text(cbq: CallbackQuery, data: Union[Choice, SIGNS_TYPE]):
    if data in UserSigns:
        return bot.answer_callback_query(cbq.id, Language.get_localized('dont_touch', cbq.from_user.language_code))

    TextXO(cbq.from_user, cbq.message).main(data)
