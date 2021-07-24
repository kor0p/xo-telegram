from __future__ import annotations

from typing import Optional, Any, Union
from datetime import datetime

from telebot import logger

from ..database import Base, UsersGames, Users
from ..const import CONSTS, UserSignsEnum, ActionType
from ..user import TGUser


class Game:
    DB = Base
    players: Players

    def __repr__(self):
        return str(self.__dict__)

    def __str__(self):
        return ', '.join((f'{name} = {value}' for name, value in self.__dict__.items()))

    def __init__(self, id, new=False, must_exists_if_not_new=True):
        if id:
            self.id = id
        if existing := self.get():
            if new:
                self.delete(existing)
            else:
                self.set(existing)
        if (new or must_exists_if_not_new) and not existing:
            self.set(self.DB.create(**self.data()))

    def get(self) -> DB:
        return self.DB.get(id=self.id, deleted_at=None)

    def push(self, **data) -> bool:
        if data:
            for k, v in data.items():
                setattr(self, k, v)
        else:
            data = self.data()
        if value := self.get():
            if value.to_dict() == data:
                return False
            value.update(**data)
            return True

    def set(self, obj: DB):
        self._set(**obj.to_dict())

    def _set(self, **kwargs: Any) -> None:
        raise NotImplementedError

    def delete(self, existing_obj: Optional[DB] = None) -> DB:
        if existing_obj is None:
            existing_obj = self.get()
        if self.push(deleted_at=datetime.now()):
            logger.debug('Deleted')
        return existing_obj

    def __bool__(self):
        return bool(self.get())

    def data(self):
        return {
            k: (v if isinstance((v := getattr(self, k)), (bool, int, str, datetime, type(None))) else str(v))
            for k in self.DB.columns
        }

    def build_game_text(
        self,
        turn_index: int,
        extra_sign_player: str = CONSTS.TURN,
        extra_sign_other_player: str = '',
    ):
        result = '\n'.join(
            f'{user_sign.value} {self.players[user_sign]}'
            + (extra_sign_player if index == turn_index else extra_sign_other_player)
            for index, user_sign in enumerate(self.players.possible_signs)
        )
        return result + '\n'


class Players:
    __slots__ = ('game_id', 'games', 'users', 'signs_to_users', 'possible_signs')

    def __init__(
        self,
        game_id: str,
        players_games: list[UsersGames, ...],
        possible_signs: Optional[list[UserSignsEnum, ...]] = None,
    ):
        self.game_id = game_id
        self.games: list[UsersGames, ...] = players_games
        self.possible_signs = possible_signs or list(UserSignsEnum)

        self.users: list[TGUser, ...] = []
        self.signs_to_users: dict[UserSignsEnum, TGUser] = {}

        for game in players_games:
            self._append_game(game)

    def _append_game(self, game: UsersGames):
        user = TGUser(game.user)
        self.users.append(user)
        self.signs_to_users[game.user_sign] = user

    def get_game_actions(self, *actions: ActionType) -> Optional[UsersGames]:
        for game in self.games:
            if game.action in actions:
                return game

    def get_game_player(self, player: Union[TGUser, Users]) -> Optional[UsersGames]:
        for game in self.games:
            if game.user_id == player.id:
                return game

    def add_player(self, player: TGUser) -> Optional[UsersGames]:
        for index, sign in enumerate(self.possible_signs):
            if sign not in self and not self.get_game_player(player):
                return self.add_player_to_db(sign, player, index=index)

    def add_player_to_db(self, sign: UserSignsEnum, user: TGUser, index=None, action=ActionType.GAME) -> UsersGames:
        if index is None:
            index = self.possible_signs.index(sign)
        user_game, _ = UsersGames.get_or_create(
            dict(
                game_id=self.game_id,
                user=Users.add_tg_user(user),
            ),
            user_sign=sign,
            action=action,
            index=index,
        )
        self._append_game(user_game)
        return user_game

    def __contains__(self, key: UserSignsEnum):
        return key in self.signs_to_users

    def __getitem__(self, key: UserSignsEnum) -> TGUser:
        return self.signs_to_users.get(key) or TGUser()

    def __iter__(self):
        return iter(self.users)

    def __len__(self):
        return len(self.users)
