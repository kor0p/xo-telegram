from datetime import datetime
from typing import Optional

from telebot.types import Message, User

from .. import database as db
from ..boards import Board
from ..bot import bot
from ..const import CONSTS, GameType, UserSigns, UserSignsEnum, SIGNS_TYPE, Choice
from ..game import Game, Players
from ..user import TGUser
from ..utils import resolve_text


class TextXO(Game):
    DB = db.TextXO

    is_x: bool = 0
    board: Board = Board.create(3)
    deleted_at: Optional[datetime] = None
    message_id: int = None
    player: TGUser

    def __init__(self, user: User, msg: Message, new=False):
        self.message_id = msg.id
        tg_user = TGUser(user)
        db.Users.add_tg_user(tg_user)

        self.player = tg_user
        super().__init__(tg_user.id, new=new)

    def _set(self, id: int, is_x: bool, board: str, deleted_at: datetime, message_id: int):
        self.is_x = is_x
        self.board = Board.create(board)
        self.deleted_at = deleted_at
        self.message_id = message_id
        self.set_players()

    def set_players(self):
        bot_sign, user_sign = resolve_text(self.is_x, UserSignsEnum)
        self.players = Players(
            '',
            [
                db.UsersGames.to_obj(user_sign=user_sign, user=db.Users.add_tg_user(self.player)),
                db.UsersGames.to_obj(user_sign=bot_sign, user=db.Users.get_bot(self.player.lang)),
            ],
        )

    def delete(self, remove_message: bool = True) -> db:
        existing_obj = super().delete()
        if remove_message:
            bot.delete_message(self.id, existing_obj.message_id)
        return existing_obj

    def edit_message(self, text: str, *, end: bool = False) -> Message:
        return bot.edit_message_text(
            text,
            self.id,
            self.message_id,
            reply_markup=self.board.end_game_buttons() if end else self.board.game_buttons(GameType.ROBOT),
        )

    def start(self, user_sign: SIGNS_TYPE):
        self.board = Board.create(3)

        sign_index = UserSigns.index(user_sign)
        self.is_x = sign_index == 0
        self.set_players()
        if not self.is_x:
            self.board[1][1] = UserSigns[0]

        self.edit_message(self.build_game_text(sign_index))
        self.push()

    def end_turn(self, text: str):
        self.edit_message(self.board.board_text() + '\n' + text, end=True)
        self.delete(remove_message=False)

    def main(self, choice: Choice):
        user_language = self.player.lang
        bot_sign, user_sign = resolve_text(self.is_x, UserSigns)

        board = self.board
        board[choice] = user_sign
        if bot_choice := board.bot_choice_func(bot_sign, user_sign):
            board[bot_choice] = bot_sign
        for sign in UserSigns:
            if not board.check_win_for_sign(sign):
                continue
            return self.end_turn(self.build_game_text(UserSigns.index(sign), CONSTS.WIN) + user_language.new)
        if not board:
            return self.end_turn(self.build_game_text(0, ''))

        self.edit_message(self.build_game_text(not self.is_x))
        self.push()
