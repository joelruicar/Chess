class Square:
    def __init__(self, row, col, piece=None):
        self.row = row
        self.col = col
        self.piece = piece
        
    def has_piece(self):
        return self.piece is not None

    def isEmpty(self):
        return not self.has_piece()        

    def has_enemy_piece(self, color):
        return self.has_piece() and self.piece.color != color

    def has_team_piece(self, color):
        return self.has_piece() and self.piece.color == color

    def isempty_or_enemy(self,color):
        return self.isEmpty() or self.has_enemy_piece(color)

    @staticmethod
    def in_range(*args):
        for arg in args:
            if arg < 0 or arg > 7:
                return False

        return True