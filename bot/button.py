from typing import Union, Sequence

from telebot import types

from .const import UserSigns
from .utils import callback


def inline_buttons(*buttons: Union[dict, Sequence[str], bool], width=3) -> types.InlineKeyboardMarkup:
    result_buttons = types.InlineKeyboardMarkup(row_width=width)
    result_buttons.add(
        *(
            types.InlineKeyboardButton(
                text=button['text'],
                url=button.get('url') or None,
                callback_data=button.get('callback') or None,
                switch_inline_query=button.get('another_chat') or None,
                switch_inline_query_current_chat=button.get('current_chat') or None,
                callback_game=button.get('game') or None,
                pay=button.get('pay') or None,
            )
            if isinstance(button, dict)
            else types.InlineKeyboardButton(
                text=button[0],
                callback_data=button[1],
            )
            for button in buttons
            if button
        )
    )
    return result_buttons


def main_menu_buttons(length=2):
    return inline_buttons(*((sign, callback.text__start.create(sign)) for sign in UserSigns[:length]))
