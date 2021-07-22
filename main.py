from .bot.handlers.__main__ import bot

from telebot import types


def handle_telegram(request):
    body = request.get_json()
    bot.process_new_updates([types.Update.de_json(body)])
    return '{"success":true}'
