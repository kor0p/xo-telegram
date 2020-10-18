from .util import JSON
from .locales import en, ru, uk


class Language:
    language_codes = {'en'}
    locales = dict(
        en=en,
        ru=ru,
        uk=uk,
    )

    def __init__(self, *languages):
        super().__init__()
        self.language_codes = languages or ('en',)

    def __getattr__(self, key):
        if key in dir(self):
            return super().__getattribute__(key)
        return '\n'.join(
            getattr(self.locales[c], key) for c in self.language_codes
        )

    def __add__(self, other):
        return Language(*tuple(set(self.language_codes) | set(other.language_codes)))

    def __repr__(self):
        return str({c: self.locales[c] for c in self.language_codes})

    def __len__(self):
        return 0
