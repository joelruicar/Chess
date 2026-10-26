class Piece:
    def __init__(self, name, color, value, texture, texture_rect=None):
        pass


class Pawn(Piece):
    def __init__(self, name, color ):
        self.dir = -1 if color == 'white' else 1