from .util import JSON
from .languages import Language


class TGUser:
    def __init__(self, data=None):
        if not data:
            self.id = 0
            self.first_name = '?'
            self.username = ''
            self.language_code = 'en'
            self.lang = Language()
            return
        if isinstance(data, str):
            data = eval(data)
        if isinstance(data, dict):
            data = JSON(**data)
        self.id = data.id
        self.first_name = data.first_name
        self.username = data.username

        data.language_code = data.language_code or 'en'
        if '-' in data.language_code:
            data.language_code = data.language_code.split('-')[0]

        self.language_code = data.language_code
        self.lang = Language(data.language_code)

    def __repr__(self):
        res = dict(**self.__dict__)
        res.pop('lang')
        return str(res)

    def __bool__(self):
        return self.id != 0

    def __eq__(self, other):
        return self.id == other.id

    def __ne__(self, other):
        return self.id != other.id
