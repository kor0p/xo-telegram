def join(strg, arr_to_str):
    return strg.join(map(str, arr_to_str))


class Base:
    value = []
    size = 0

    def __getitem__(self, key):
        if isinstance(key, tuple):
            return self.value[key[0]][key[1]]
        return self.value[key]

    def __setitem__(self, key, item):
        self.value[key] = item

    def __repr__(self):
        return join('', self)

    def __len__(self):
        return self.size


class Row(Base):

    def __init__(self, board):
        if isinstance(board, str):
            board = list(board)
        self.value = board
        self.size = int(len(board)**.5)
