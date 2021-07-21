from __future__ import annotations

import os
from typing import Any, Union, Iterable, Callable
from importlib import import_module
from pathlib import Path


def get_unique_tuple(value: tuple) -> tuple:
    return tuple(dict.fromkeys(value))


def join(values: Iterable[Union[str, dict]], joiner='\n'):
    values = list(values)
    if isinstance(values[0], str):
        return joiner.join(values)

    return {key: join(v[key] for v in values) for key, value in values[0].items()}


locales_dir = os.listdir(os.path.join(Path(__file__).parent, 'locales'))
locales_list = [file.split('.', 1)[0] for file in locales_dir if file not in ('__init__.py', '__pycache__')]


class Language:
    NONE: Language
    language_codes: tuple[str]
    locales: dict[str, Any] = {locale: import_module(f'bot.locales.{locale}') for locale in locales_list}
    _request_lang: Callable = None  # assigned in handlers.__main__

    def __init__(self, *languages: str, default_codes=('en',)):
        languages = tuple((lang.split('-')[0] if '-' in lang else lang) for lang in languages if lang)
        self.language_codes = languages or default_codes

    @classmethod
    def get_localized(cls, key, language_code):
        if language_code not in cls.locales:
            cls._request_lang(language_code)
            language_code = 'en'
        return getattr(cls.locales[language_code], key)

    @property
    def code(self):
        return self.language_codes[0]

    @classmethod
    def sum(cls, languages: Iterable[Language]) -> Language:
        return sum(languages, cls.NONE)

    def __getattr__(self, key: str):
        if key in dir(self):
            return super().__getattribute__(key)
        return join(self.get_localized(key, c) for c in self.language_codes)

    def __add__(self, other: Language) -> Language:
        return type(self)(*get_unique_tuple((*self.language_codes, *other.language_codes)))

    def __repr__(self):
        return str({c: self.locales[c] for c in self.language_codes})

    def __len__(self):
        return len(self.language_codes)

    def __bool__(self):
        return bool(self.language_codes)


# use this for sum
Language.NONE = Language(default_codes=())
