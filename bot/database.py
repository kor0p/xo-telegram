from __future__ import annotations

import os
from typing import Any, Union

import sqlalchemy
from sqlalchemy import Column, ForeignKey, JSON, Text, String, Integer, DateTime, Boolean, Enum
from sqlalchemy.orm import scoped_session, sessionmaker, relationship, declarative_base, Session, Query
from sqlalchemy_mixins import AllFeaturesMixin
from sqlalchemy_mixins.utils import classproperty
from telebot import types

from .const import ActionType, CONSTS
from .user import TGUser
from .languages import Language

DATABASE_URL = os.environ['DB_URL']
engine = sqlalchemy.create_engine(
    DATABASE_URL,
    pool_size=5,
    max_overflow=2,
    pool_timeout=30,  # 30 seconds
    pool_recycle=1800,  # 30 minutes
    convert_unicode=True,
    # echo=True,  # verbose mode
)
engine.dialect.description_encoding = None


class CustomQuery(Query):
    def update(self, **values):
        return super().update(values)


session = scoped_session(sessionmaker(autocommit=True, autoflush=True, bind=engine, query_cls=CustomQuery))
metadata = sqlalchemy.MetaData(bind=engine)


class Base(declarative_base(metadata=metadata), AllFeaturesMixin):
    __abstract__ = True

    columns: list[str, ...]
    primary_keys: list[str, ...]

    @classmethod
    def to_obj(cls, **kwargs: Any) -> Base:
        return cls(**kwargs, _without_session=True)

    def get_from_db(self):
        where = {pk: getattr(self, pk) for pk in self.primary_keys}
        return self.get(**where)

    def __init__(self, _without_session=False, **kwargs: Any):
        super().__init__(**kwargs)
        if _without_session:
            self.session.expunge(self)

    def __bool__(self):
        return any(getattr(self, pk, None) is not None for pk in self.primary_keys)

    query: CustomQuery
    session: Union[scoped_session, Session]

    @classproperty
    def query(cls):
        return super().query

    @classmethod
    def where(cls, **filters) -> CustomQuery:
        return super().where(**filters)

    def update(self, **kwargs: Any) -> Base:
        return super().update(**kwargs)

    @classmethod
    def get(cls, **where) -> Base:
        return cls.where(**where).first()

    @classmethod
    def get_or_create(cls, get=None, **create) -> tuple[Base, bool]:
        if get is None:
            get = {}
        elif not isinstance(get, dict):
            get = dict(id=get)
        if existing_obj := cls.get(**get):
            return existing_obj, False
        return cls.create(**(get | create)), True


class TextXO(Base):
    __tablename__ = 'xo_text'

    id = Column(Integer, ForeignKey('users.id'), primary_key=True)
    is_x = Column(Boolean)
    board = Column(String)
    message_id = Column(Integer, primary_key=True)
    deleted_at = Column(DateTime, default=None)


class UsersGames(Base):
    __tablename__ = 'users_games'

    user_id = Column(Integer, ForeignKey('users.id'), primary_key=True)
    game_id = Column(String, ForeignKey('xo.id'), primary_key=True)

    index = Column(Integer)
    user_sign = Column(String)
    action = Column(Enum(ActionType))


class XO(Base):
    __tablename__ = 'xo'

    id = Column(String, primary_key=True)

    queue = Column(Integer)
    board = Column(String)
    deleted_at = Column(DateTime, default=None)
    signs = Column(String, default=CONSTS.DEFAULT_GAMES_SIGNS)

    players_games = relationship(UsersGames, backref='game')


class Users(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    username = Column(String)
    lang = Column(String)
    deleted_at = Column(DateTime, default=None)
    bot_can_message = Column(Boolean, default=True)

    users_games = relationship(UsersGames, backref='user')
    xo_text = relationship(TextXO, backref='player')

    def active_xo_text(self):
        return TextXO.where(deleted_at=None, user=self)

    @classmethod
    def add_tg_user(cls, tg_user: TGUser) -> Users:
        user: Users
        user, created = cls.get_or_create(tg_user.id, **tg_user.to_dict())
        if not created and user.lang != tg_user.lang.code:
            return user.update(lang=tg_user.lang.code)
        return user

    @classmethod
    def get_bot(cls, language: Language):
        return cls.get(username=CONSTS.BOT_USERNAME, lang=language.code)


class Messages(Base):
    __tablename__ = 'messages'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), primary_key=True)
    text = Column(Text)
    content_type = Column(String)
    data = Column(JSON)

    user = relationship(Users, backref='messages')

    @classmethod
    def add_tg_message(cls, message: types.Message, *, user=None):
        if user is None:
            user = Users.add_tg_user(TGUser(message.from_user))
        return cls.get_or_create(
            dict(id=message.id, user=user),
            text=message.text,
            content_type=message.content_type,
            data=message.json,
        )


Base.set_session(session)
metadata.create_all(bind=engine)

for index, language_code in enumerate(Language.locales):
    Users.get_or_create(
        dict(username=CONSTS.BOT_USERNAME, lang=language_code),
        id=index,
        name=Language.get_localized('bot', language_code),
        bot_can_message=False,
    )
