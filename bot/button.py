from .const import *
from telebot import types


def callback_buttons(buttons, width=3):
    temp_buttons = types.InlineKeyboardMarkup(
        row_width=width if width else len(buttons[0]))
    temp_buttons.add(*[
        types.InlineKeyboardButton(
            button[0],
            callback_data=button[1]
        ) for button in buttons])
    return temp_buttons


def main_menu_buttons():
    return callback_buttons([
        [sgn.x, cnst.repeat + sgn.x],
        [sgn.o, cnst.repeat + sgn.o]
    ])


def inline_buttons_(buttons, width=3):
    temp_buttons = types.InlineKeyboardMarkup(
        row_width=width if width else len(buttons[0]))
    temp_buttons.add(*[
        types.InlineKeyboardButton(
            button['text'],
            url=button.get('url'),
            callback_data=button.get('callback'),
            switch_inline_query=button.get('another_chat'),
            switch_inline_query_current_chat=button.get('current_chat'),
            callback_game=button.get('game'),
            pay=button.get('pay')
        ) for i in buttons for button in i])
    return temp_buttons
