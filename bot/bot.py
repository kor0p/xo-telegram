import os
import json
import logging
from typing import Union, Callable, Optional

from telebot import TeleBot, types, logger
from telebot.apihelper import ApiTelegramException

from .const import Choice
from .database import Messages, Users
from .utils import JSON_COMMON_DATA

logger.setLevel(logging.DEBUG)


CallbackDataType = Union[str, dict[str, JSON_COMMON_DATA]]  # parsed json data


class ExtraTeleBot(TeleBot):
    callback_query_handlers: dict[str, CallbackDataType]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.callback_query_handlers = {}

    def callback_query_handler(self, func: Callable[[types.CallbackQuery, Optional[CallbackDataType]], None], **kwargs):
        return super().callback_query_handler(func, **kwargs)

    def add_callback_query_handler(self, handler_dict: dict):
        self.callback_query_handlers[handler_dict['filters']['func'].name] = handler_dict['function']

    def process_new_callback_query(self, messages: list[types.CallbackQuery, ...]):
        for message in messages:
            try:
                data = json.loads(message.data)
                _type = data['type']
                if _type not in self.callback_query_handlers:
                    continue
            except json.JSONDecodeError:
                continue

            args = (message,)
            if (callback_data := data['data']) and callback_data != 'null':
                args += tuple(Choice(*i) if isinstance(i, list) else i for i in callback_data)

            self._exec_task(self.callback_query_handlers[_type], *args)
            break

    def process_new_messages(self, new_messages: list[types.Message, ...]):
        for message in new_messages:
            Messages.add_tg_message(message)
        super().process_new_messages(new_messages)

    def send_message(self, user_id, *args, **kwargs) -> types.Message:
        message = None
        try:
            message = super().send_message(user_id, *args, **kwargs)
        except ApiTelegramException:
            # message.id is None - unsuccessful message - bot is blocked by user
            Users.get(id=user_id).update(bot_can_message=message is not None and message.id is not None)

        return message


bot = ExtraTeleBot(os.environ.get('BOT_TOKEN'), threaded=False)
