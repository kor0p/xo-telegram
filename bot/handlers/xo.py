from __future__ import annotations

import json
import random
from typing import Union, Literal

from telebot import types
from telebot.types import CallbackQuery, InlineQuery

from ..bot import bot
from ..button import inline_buttons
from ..const import CONSTS, URLS, STICKERS, GAME_SIZES, UserSignsNames, SIGNS_TYPE, Choice, GameEndAction
from ..languages import Language
from ..game.xo import XO
from ..utils import random_list_size, callback


@bot.inline_handler(lambda q: True)
def inline_query_handler(inline_query: InlineQuery):
    language = Language(inline_query.from_user.language_code)

    size = 0
    if query := inline_query.query.lower():
        if 'r' in query:
            size = next(random_list_size)
            query = query.replace('r', '')
        else:
            for game_size in GAME_SIZES:
                if (str_size := str(game_size)) in query:
                    size = game_size
                    query = query.replace(str_size, '')
                    break

    buttons = inline_buttons(
        *((str(i), callback.start.create(i)) for i in GAME_SIZES),
        (language.random, callback.start.create(0)),
        (not size or random.randint(0, 30) == 0) and {'text': language.donate, 'url': URLS.DONATE},
        width=3,
    )
    return bot.answer_inline_query(
        inline_query.id,
        (
            types.InlineQueryResultCachedSticker(
                json.dumps({'size': size, 'sign': sign}),
                STICKERS[sign],
                reply_markup=buttons,
                input_message_content=types.InputTextMessageContent(language.startN),
            )
            for sign in UserSignsNames
            if not query or sign.lower() in query
        ),
    )


@bot.chosen_inline_handler(func=lambda cr: cr)
def chosen_inline_query(inline_request):
    data = json.loads(inline_request.result_id)
    if not inline_request.inline_message_id:
        return  # future message
    XO(inline_request.inline_message_id, new=True).create_base_game(user=inline_request.from_user, **data)


@bot.callback_query_handler(callback.start)
def choice_size(cbq: CallbackQuery, size: int):
    XO(cbq.inline_message_id).start_game_with_possible_new_player(cbq.from_user, size)


@bot.callback_query_handler(callback.confirm_end)
def confirm_or_end(cbq: CallbackQuery, action: str, choice: Choice):
    error_text = XO(cbq.inline_message_id).confirm_or_end_callback(cbq.from_user, GameEndAction[action], choice)

    if error_text:
        return bot.answer_callback_query(cbq.id, error_text, show_alert=True)


@bot.callback_query_handler(callback.game)
def main_xo(cbq: CallbackQuery, data: Union[Choice, SIGNS_TYPE, Literal[CONSTS.LOCK]]):
    def alert_text(text, **kwargs):
        return bot.answer_callback_query(cbq.id, text=text, **kwargs)

    XO(cbq.inline_message_id).main(cbq.from_user, data, alert_text)
