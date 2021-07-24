from telebot.types import Message, User

from . import xo, text_xo
from ..languages import Language


def _request_lang(language):
    return text_xo.request_admin_support(
        Message(0, User(first_name='', id=0, is_bot=True), 0, 0, 'text', dict(text=f'AUTO_REQUEST: {language=}'), '')
    )


Language._request_lang = _request_lang
