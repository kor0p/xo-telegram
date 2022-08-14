import os
import json
import logging
from typing import Union, Callable, Optional
from functools import wraps

from telebot import TeleBot, types, logger
from telebot.apihelper import ApiException, ApiTelegramException
from sqlalchemy.exc import SQLAlchemyError

from .const import Choice
from .database import Messages, Users
from .languages import Language
from .utils import JSON_COMMON_DATA, InvalidGameConfigError

logger.setLevel(logging.DEBUG)


CallbackDataType = Union[str, dict[str, JSON_COMMON_DATA]]  # parsed json data


def auto_answer_queries(task, answer_query, pending_queries_set: set, message_id, error):
    @wraps(task)
    def wrapper(*args, **kwargs):
        try:
            return task(*args, **kwargs)
        except (ApiException, SQLAlchemyError, AttributeError):  # try to send error to user
            logger.exception('1')
            try:
                answer_query(message_id, error)
            except ApiTelegramException:
                logger.exception('2', exc_info=True)
                pending_queries_set.discard(message_id)
        except Exception:  # if there was error, just answer query to remove it from queue
            logger.exception('3', exc_info=True)
            try:
                answer_query(message_id)
            except ApiTelegramException:  # if query is too old
                pending_queries_set.discard(message_id)
        except:
            answer_query()

    return wrapper


class ExtraTeleBot(TeleBot):
    callback_query_handlers: dict[str, CallbackDataType]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.callback_query_handlers = {}
        self.pending_callback_ids = set()

    def callback_query_handler(self, func: Callable[[types.CallbackQuery, Optional[CallbackDataType]], None], **kwargs):
        return super().callback_query_handler(func, **kwargs)

    def add_callback_query_handler(self, handler_dict: dict):
        self.callback_query_handlers[handler_dict['filters']['func'].name] = handler_dict['function']

    def process_new_callback_query(self, messages: list[types.CallbackQuery, ...]):
        for message in messages:
            self.pending_callback_ids.add(message.id)
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

            self._exec_task(
                auto_answer_queries(
                    self.callback_query_handlers[_type],
                    self.answer_callback_query,
                    self.pending_callback_ids,
                    message.id,
                    Language.get_localized('exception', message.from_user.language_code),
                ),
                *args,
            )

    def answer_callback_query(
        self,
        callback_query_id: Union[str, int],
        text: Optional[str] = None,
        show_alert: Optional[bool] = None,
        url: Optional[str] = None,
        cache_time: Optional[int] = None,
    ) -> bool:
        if callback_query_id not in self.pending_callback_ids:
            return True

        success = super().answer_callback_query(callback_query_id, text, show_alert, url, cache_time)
        if success:
            self.pending_callback_ids.discard(callback_query_id)

        return success

    def process_new_messages(self, new_messages: list[types.Message, ...]):
        for message in new_messages:
            Messages.add_tg_message(message)
        super().process_new_messages(new_messages)

    def send_message(self, user_id, *args, **kwargs) -> types.Message:
        message = None
        try:
            message = super().send_message(user_id, *args, **kwargs)
            print(message)
            Messages.add_tg_message(message, user=Users.get_bot(Language('en')))
        except ApiTelegramException as e:
            print(e)
            pass

        # message.id is None - unsuccessful message - bot is blocked by user
        Users.get(id=user_id).update(bot_can_message=message is not None and message.id is not None)

        return message


class ErrorHandler:
    def handle(self, error):
        if isinstance(error, InvalidGameConfigError):
            return True


bot = ExtraTeleBot(
    os.environ.get('BOT_TOKEN'),
    parse_mode='HTML',
    num_threads=8,
    exception_handler=ErrorHandler(),
)
