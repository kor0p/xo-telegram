import time
import threading
from datetime import datetime
from typing import Optional, Union, Literal

from telebot import types

from .. import database as db
from ..boards import is_cell_free, Board, BoardBig
from ..bot import bot
from ..const import (
    how_many_to_win,
    CONSTS,
    GameType,
    ActionType,
    UserSignsEnum,
    UserSignsNames,
    UserSigns,
    GameState,
    GameEndAction,
    Choice,
    SIGNS_TYPE,
    CHOICE_NULL,
)
from ..button import inline_buttons
from ..game import Game, Players
from ..languages import Language
from ..user import TGUser
from ..utils import random_list_size, get_markdown_user_url, callback


class XO(Game):
    DB = db.XO

    queue: int = 0
    board: Union[Board, BoardBig] = Board.create(3)
    deleted_at: Optional[datetime] = None
    players: Players

    def __init__(self, _id, new=False):
        super().__init__(_id, new)

    def set(self, obj: DB):
        self._set(**obj.to_dict(nested=True))

    def _set(self, id: int, queue: int, board: str, deleted_at: datetime, players_games: list[dict, ...]):
        self.queue = queue
        self.board = Board.create(board)
        self.deleted_at = deleted_at

        self.players = Players(
            self.id,
            [db.UsersGames.to_obj(**game, user=db.Users.get(id=game['user_id'])) for game in players_games],
        )

    def __bool__(self):
        return super().__bool__() or self.players.get_game_actions(ActionType.TIE, ActionType.GIVE_UP) or False

    def pass_turn(self, update: int = 1):
        self.queue = (self.queue + update) % len(self.players.possible_signs)

    def edit_message(self, text, reply_markup=None, **kwargs):
        return bot.edit_message_text(text=text, inline_message_id=self.id, reply_markup=reply_markup, **kwargs)

    def game_language(self) -> Language:
        return Language.sum(user.lang for user in self.players)

    def create_base_game(self, user: types.User, size: int, sign: UserSignsNames):
        self.players.add_player_to_db(UserSignsEnum[sign], TGUser(user))

        if size == 0:
            self.push()
            return

        self.timeout((size ** 2) * 30, GameState.GAME)
        self.board = Board.create(size)
        self.game_xo()

    def start_game_with_possible_new_player(self, user: types.User, size: int):
        new_player = self.players.add_player(TGUser(user))
        if new_player:
            self.pass_turn(-1)

        if size == 0:
            size = next(random_list_size)

        self.timeout((size ** 2) * 30, GameState.GAME)
        self.board = Board.create(size)
        self.game_xo()

    def confirm_or_end_callback(self, user: types.User, action: str, choice: Choice) -> Optional[str]:
        player = TGUser(user)

        player_game = self.players.get_game_player(player)

        if action == GameEndAction.CANCEL:
            if player_game and player_game.action != ActionType.GAME:
                player_game.update(action=ActionType.GAME)
                return self.game_xo(choice)
            return player.lang.stop_game

        if self.players.get_game_actions(ActionType.TIE):
            if player_game and player_game.action == ActionType.TIE:
                return self.end(GameState.TIE, choice)
            return player.lang.stop_game

        if self.players.get_game_actions(ActionType.GIVE_UP):
            if player_game and player_game.action == ActionType.GIVE_UP:
                return self.end(GameState.GIVE_UP, choice)
            return player.lang.stop_game

        if action == GameEndAction.TIE:
            if player_game:
                player_game.update(action=ActionType.TIE)
                return self.timeout_confirm(GameState.TIE, player, choice)
            return player.lang.dont_touch

        if action == GameEndAction.GIVE_UP:
            if not player_game:
                return player.lang.dont_touch

            player_game.update(action=ActionType.GIVE_UP)
            if choice[0] != CHOICE_NULL:  # WTF ??? Why we not updating queue TODO: Check this.
                self.pass_turn()  # ############# Can be second turn for player in 4, 9, 16 sizes games
                self.push()
            return self.timeout_confirm(GameState.GIVE_UP, player, choice)

    def main(self, user: types.User, data: Union[Choice, SIGNS_TYPE, Literal[CONSTS.LOCK]]):
        player = TGUser(user)
        ul_this = player.lang
        if isinstance(data, str) and (not is_cell_free(data)):
            return ul_this.dont_touch
            # return bot.answer_callback_query(query_id, ul_this.dont_touch, show_alert=True)

        player_game = self.players.get_game_player(player)

        if player_game and player_game.index != self.queue:
            return ul_this.stop

        if data[:2] == [CHOICE_NULL] * 2:
            return ul_this.start9

        for index, sign in enumerate(UserSignsEnum):
            # index is used for calculate queue

            if sign not in self.players and self.queue == index and player_game is None:
                self.players.add_player_to_db(sign, player, index=index)
                return ul_this.start_pl_2

            if sign in self.players:
                if player_game and player_game.user_sign == sign:
                    if self.queue == player_game.index:
                        return self.game_xo(data)
                    return ul_this.stop
                for new_index, new_sign in enumerate(tuple(UserSignsEnum)[index + 1 :]):
                    if new_sign not in self.players:
                        self.players.add_player_to_db(new_sign, player, index=new_index + 1)
                        self.game_xo(data)
                        return ul_this.start_pl_2
                if player_game and player_game.user_sign == sign and player_game.index == index:
                    return self.game_xo(data)

        return ul_this.stop_game

    def end(self, game_state: Optional[GameState], index_last_turn=None, text=''):
        ul = self.game_language()

        if game_state == GameState.TIE:
            text += self.build_game_text(0, '') + (ul.canceled if self.board else '')
        elif game_state == GameState.END:
            text += self.build_game_text(self.queue, CONSTS.WIN)
        elif game_state == GameState.GIVE_UP:
            if player_game := self.players.get_game_actions(ActionType.GIVE_UP):
                self.queue = player_game.index
            else:
                print('WTF?')
            text += self.build_game_text(self.queue, CONSTS.WIN, CONSTS.LOSE) + ul.player.format(
                (pg := self.players.get_game_actions(ActionType.GIVE_UP)) and pg.user.name
            )
        elif game_state:
            text += self.build_game_text(0, '')
        if index_last_turn and index_last_turn[0] == CHOICE_NULL:
            index_last_turn = ()
        self.edit_message(
            self.board.board_text(index_last_turn) + '\n' + text,
            self.board.end_game_buttons(self.id, str(self.board), '_'.join(str(u.id) for u in self.players)),
        )
        if index_last_turn:
            self.timeout(5, text_for_final_board=text)
        else:
            self.delete()

    def game_xo(self, choice: Optional[Choice] = None):
        with self.DB.session.no_autoflush:
            if isinstance(self.board, BoardBig):
                return self.game_xo_big(choice)
            ul = self.game_language()
            if choice:
                self.board[choice] = win_sign = UserSigns[self.queue]
                if self.board.check_win_for_sign(win_sign):
                    return self.end(GameState.END, choice)
                elif not self.board:
                    return self.end(GameState.TIE, choice)
            if any(sign in self.board for sign in UserSigns):
                self.pass_turn()
            self.push()
            self.edit_message(
                ul.to_win.format(how_many_to_win(self.board.size)) + '\n' + self.build_game_text(self.queue),
                self.board.game_buttons(GameType.USER, ul, choice),
            )

    def game_xo_big(self, choice):
        ul = self.game_language()
        last_turn = ()
        if choice and choice[0] != CHOICE_NULL:
            last_turn = choice
            self.board[choice] = UserSigns[self.queue]
            self.board.s_value = self.board.small_value(True)
            if self.board.check_win_for_sign(self.board[choice]):
                return self.end(GameState.END, choice)
            elif not self.board:
                return self.end(GameState.TIE, choice)
        if any(sign in self.board for sign in UserSigns):
            self.pass_turn()
        elif choice:
            last_turn = choice[2:] * 2
        self.push()
        self.edit_message(
            self.board.board_text(last_turn) + '\n\n' + self.build_game_text(self.queue),
            self.board.game_buttons(GameType.USER, ul, choice),
        )

    def timeout(
        self,
        seconds_sleep_time: int,
        game_state: Optional[GameState] = None,
        last_turn: Optional[Choice] = None,
        text_for_final_board: str = CONSTS.TIME,
    ):
        def __inner():
            time.sleep(seconds_sleep_time)
            if (10 <= seconds_sleep_time <= 60) and not self:
                return
            if seconds_sleep_time > 10:
                time.sleep(5)
            if not self:  # game ended or there is no TIE or GIVE_UP state any more
                return
            self.end(game_state, last_turn, text_for_final_board + '\n')

        threading.Thread(target=__inner, daemon=True).start()

    def timeout_confirm(self, game_state: Literal[GameState.TIE, GameState.GIVE_UP], user: TGUser, last_turn: Choice):
        game_language = self.game_language()

        if game_state == GameState.TIE:
            players = [player for player in self.players if player != user]
            user_language = Language.sum(user.lang for user in players)
            text = ', '.join(get_markdown_user_url(user) for user in players) + ',\n'
        else:
            user_language = user.lang
            text = get_markdown_user_url(user) + ',\n'

        self.edit_message(
            text + user_language.confirm[game_state.name],
            inline_buttons(
                (
                    user_language.confirm['default'],
                    callback.confirm_end.create(GameEndAction[game_state.name], last_turn),
                ),
                (game_language.cancel, callback.confirm_end.create(GameEndAction.CANCEL, last_turn)),
            ),
            parse_mode='Markdown',
        )
        self.timeout(30, game_state, last_turn)
