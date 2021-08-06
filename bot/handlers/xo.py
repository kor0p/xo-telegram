from __future__ import annotations

from typing import Union, Literal

from telebot import types
from telebot.types import CallbackQuery, InlineQuery

from ..bot import bot
from ..button import choose_game_sizes
from ..const import CONSTS, Choice, GameEndAction, GameSigns
from ..languages import Language
from ..game.xo import XO
from ..utils import callback


@bot.inline_handler(lambda q: True)
def inline_query_handler(inline_query: InlineQuery):
    language = Language(inline_query.from_user.language_code)
    query = inline_query.query

    return bot.answer_inline_query(
        inline_query.id,
        (
            types.InlineQueryResultArticle(
                sign, sign, types.InputTextMessageContent(language.startN), choose_game_sizes(language)
            )
            for sign in GameSigns(CONSTS.ALL_GAMES_SIGNS)
            if sign in query or not query
        ),
    )


@bot.chosen_inline_handler(func=lambda cr: cr)
def chosen_inline_query(inline_request):
    if not inline_request.inline_message_id:
        return  # future message
    XO(inline_request.inline_message_id, new=True).create_base_game(inline_request.from_user, inline_request.result_id)


@bot.callback_query_handler(callback.start_size)
def choice_size(cbq: CallbackQuery, size: int):
    XO(cbq.inline_message_id).start_game_with_size_chosen(cbq.from_user, size)


@bot.callback_query_handler(callback.start_players_count)
def choice_players_count(cbq: CallbackQuery, players_count: int):
    XO(cbq.inline_message_id).start_game_with_players_count_chosen(cbq.from_user, players_count)


@bot.callback_query_handler(callback.confirm_end)
def confirm_or_end(cbq: CallbackQuery, action: str, choice: Choice):
    error_text = XO(cbq.inline_message_id).confirm_or_end_callback(cbq.from_user, GameEndAction[action], choice)

    if error_text:
        return bot.answer_callback_query(cbq.id, error_text, show_alert=True)


@bot.callback_query_handler(callback.game)
def main_xo(cbq: CallbackQuery, data: Union[Choice, str, Literal[CONSTS.LOCK]]):
    def alert_text(text, **kwargs):
        return bot.answer_callback_query(cbq.id, text=text, **kwargs)

    XO(cbq.inline_message_id).main(cbq.from_user, data, alert_text)
