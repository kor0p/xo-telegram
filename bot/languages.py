class Language:
    data = dict(
        start=dict(
            en='Choose your side and get started!',
            ua='Обирай сторону і почнімо!',
            ru='Выбери сторону и начнём!',
        ), bot=dict(
            en='Bot',
            ua='Бот',
            ru='Бот',
        ), dont_touch=dict(
            en='Oh, you can\'t go there',
            ua='Ой, сюди заборонено ходити)',
            ru='Ой, ты не можеш сюда идти!',
        ), cnld=dict(
            en='Canceled',
            ua='Відмінено',
            ru='Отменено',
        ), new=dict(
            en='Start a new game?',
            ua='Зіграємо ще раз?',
            ru='Сыграем ещё раз?',
        ), to_win=dict(
            en='{0} in the row to win!',
            ua='{0} поспіль для перемоги!',
            ru='{0} в ряд для победы!',
        ), stop=dict(
            en='Stop! Wait your turn',
            ua='Стоп! Не твій хід)',
            ru='Стопэ! Не твой ход!',
        ), stop_game=dict(
            en='Stop! There already playing',
            ua='Стоп! Тут уже грають)',
            ru='Стопэ! Здесь уже играют!',
        ), do_tie=dict(
            en='Tie',
            ua='Нічия',
            ru='Ничья',
        ), confirm_tie=dict(
            en='Accept tie?',
            ua='Приймаєш нічию?',
            ru='Принимаешь ничью?'
        ), confirm_giveup=dict(
            en='Confirm giving up!',
            ua='Підтвердь поразку!',
            ru='Подтвердите проиграш!',
        ), start_pl_2=dict(
            en='Let’s go!',
            ua='Почнімо!',
            ru='Начнём!',
        ), player=dict(
            en='Player {0} gives up',
            ua='Гравець {0} здався',
            ru='Игрок {0} сдался'
        ), giveup=dict(
            en='Give up',
            ua='Здатися',
            ru='Сдаться',
        ), cnf=dict(
            en='Confirm',
            ua='Підтверджую',
            ru='Подтверждаю',
        ), cnl=dict(
            en='Cancel',
            ua='Відміна',
            ru='Отмена',
        ), startN=dict(
            en='Choose size and get started!',
            ua='Обирай тип і до бою!',
            ru='Выбери тип и к бою!',
        ), random=dict(
            en='Random',
            ua='Однаково',
            ru='Рандом',
        ), timeout=dict(
            en='Seconds remains: {0}',
            ua='Секунд лишилось: {0}',
            ru='Секунд осталось: {0}',
        ), start9=dict(
            en='It\'s double-turn, keep going!',
            ua='Твій хід ще триває, продовжуй!',
            ru='Этот ход ещё не кончился, продолжай!',
        ), rules=dict(
            en='Rules',
            ua='Правила',
            ru='Правила',
        )
    )

    def __init__(self, language_code='en', second_language_code=None):
        self.language_code = language_code
        self.second_language_code = second_language_code

    def __getattr__(self, key):
        if key in ['data', 'language_code', 'second_language_code']:
            return super().__getattribute__(key)

        data = self.data[key]
        base = data.get(self.language_code, data['en'])
        if self.second_language_code:
            base += '\n' + data.get(self.second_language_code, '')
        return base

    def __add__(self, other):
        if self.language_code == other.language_code:
            return self
        return Language(self.language_code, other.language_code)

    def __repr__(self):
        return {k: v.get(self.language_code, v['en']) for k, v in self.data}

    def __len__(self):
        print('WHY __len__???')
        return 0
