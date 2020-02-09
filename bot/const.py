from .util import JSON
from .config import token
from telebot import TeleBot

how_many_to_win = {
    2: 2,
    3: 3, 4: 3,
    5: 4, 6: 4,
    7: 5, 8: 5
}
list_of_sizes = (4, 9, 16, 3, 5, 6, 7, 8)

sgn = JSON(
    cell='⬜',
    x='❌',
    o='⭕',
)
new_sgn = JSON(
    cell='◻',
    x='✖',
    o='🔴'
)

cnst = JSON(
    lock='🔒',
    time='⏳',
    win='🏆',
    lose='☠️',
    tie='🤜🤛',
    turn=' 👈',
    repeat='🔄',
    robot='🤖',
    friend='🙎'
)

game_signs = (sgn.o, sgn.x)
end_signs = (cnst.lose, cnst.win)
new_game_signs = {
    sgn.x: new_sgn.x,
    sgn.o: new_sgn.o,
    sgn.cell: new_sgn.cell,
    new_sgn.x: sgn.x,
    new_sgn.o: sgn.o,
    new_sgn.cell: sgn.cell
}

bot = TeleBot(token, threaded=False)
