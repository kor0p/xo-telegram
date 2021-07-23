import bot.handlers.__main__
from bot.bot import bot

from telebot import types


def handle_telegram(request):
    body = request.get_json()
    bot.process_new_updates([types.Update.de_json(body)])
    return '{"success":true}'
