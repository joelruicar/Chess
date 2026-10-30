from const import *
from square import Square
from piece import *
from move import Move
import copy
class Board:
    def __init__(self):
        self.squares = [[0,0,0,0,0,0,0,0] for col in range(COLS)]
        self.last_move = None
        self._create()
        self._add_pieces('white')
        self._add_pieces('black')

    def move(self, piece,move):
        initial = move.initial
        final = move.final

        self.squares[initial.row][initial.col].piece = None
        self.squares[final.row][final.col].piece = piece

        if isinstance(piece, Pawn):
            self.check_promotion(piece, final)

        if isinstance(piece, King):
            if self.castling(initial, final):
                diff = final.col - initial.col
                rook = piece.left_rook if (diff < 0) else piece.right_rook
                self.move(rook,rook.moves[-1])

        piece.moved = True
        piece.clear_moves()
        self.last_move = move

    def valid_move(self,piece, move):
        final_square = self.squares[move.final.row][move.final.col]
        return (
            move in piece.moves
            and (final_square.isEmpty() or final_square.has_enemy_piece(piece.color))
        )

    def castling(self,initial,final):
        return abs(initial.col - final.col) == 2 

    def check_promotion(self,piece,final):
        if final.row == 0 or final.row == 7:
            self.squares[final.row][final.col].piece = Queen(piece.color)

    def calc_moves(self, piece, row, col, bool=True):
        """
        calculate all the possible or valid movis of an 
        specific piece on a specific position
        """
        piece.clear_moves()

        def pawn_moves():
            steps = 1 if piece.moved else 2

            start = row + piece.dir
            end = row + (piece.dir * (1+steps))

            for possible_move_row in range(start, end, piece.dir):
                if Square.in_range(possible_move_row):
                    if self.squares[possible_move_row][col].isEmpty():
                        initial = Square(row, col)
                        final = Square(possible_move_row, col)
                        move = Move(initial, final)

                        #chech if is checkmate
                        if bool:
                            if not self.in_check(piece, move):
                                piece.add_move(move)
                        else:
                            piece.add_move(move)

                    else: break
                else: break

            possible_move_row = row + piece.dir
            possible_move_cols = [col-1, col+1]
            for possible_move_col in possible_move_cols:
                if Square.in_range(possible_move_row, possible_move_col):
                    if self.squares[possible_move_row][possible_move_col].has_enemy_piece(piece.color):
                        initial = Square(row, col)
                        final = Square(possible_move_row, possible_move_col)
                        move = Move(initial, final)
                        if bool:
                            if not self.in_check(piece, move):
                                piece.add_move(move)
                        else:
                            piece.add_move(move)

        def knight_moves():
            # 8 possible moves
            possible_moves = [
                (row-2, col+1),(row-1, col+2),(row+1,col+2),(row+2, col+1),(row+2,col-1),(row+1,col-2),(row-1,col-2),(row-2,col-1)
            ]

            for possible_move in possible_moves:
                possible_move_row, possible_move_col = possible_move
                if Square.in_range(possible_move_row, possible_move_col):
                    if self.squares[possible_move_row][possible_move_col].isempty_or_enemy(piece.color):
                        initial = Square(row, col)

                        final_piece = self.squares[possible_move_row][possible_move_col].piece
                        final = Square(possible_move_row, possible_move_col, final_piece)
                        move = Move(initial, final)
                        if bool:
                            if not self.in_check(piece, move):
                                piece.add_move(move)
                            else:
                                break
                        else:
                            piece.add_move(move)

        def straightline_moves(incrs):
            for incr in incrs:
                row_incr, col_incr = incr
                possible_move_row = row + row_incr
                possible_move_col = col + col_incr

                while True:
                    if Square.in_range(possible_move_row, possible_move_col):
                        # create squares of the possible new move
                        initial = Square(row, col)
                        final_piece = self.squares[possible_move_row][possible_move_col].piece
                        final = Square(possible_move_row, possible_move_col, final_piece)
                        # create a possible new move
                        move = Move(initial, final)
                        if self.squares[possible_move_row][possible_move_col].isEmpty():
                            if bool:
                                if not self.in_check(piece, move):
                                    piece.add_move(move)
                            else:
                                piece.add_move(move)
                        elif self.squares[possible_move_row][possible_move_col].has_enemy_piece(piece.color):
                            if bool:
                                if not self.in_check(piece, move):
                                    piece.add_move(move)
                            else:
                                piece.add_move(move)
                            break
                        elif self.squares[possible_move_row][possible_move_col].has_team_piece(piece.color):
                            break
                    else:
                        break

                    possible_move_row, possible_move_col = possible_move_row + row_incr, possible_move_col + col_incr

        def king_moves():
            possible_moves = [
                        (row-1, col+0),
                        (row-1, col+1),
                        (row+0, col+1),
                        (row+1, col+1),
                        (row+1, col+0),
                        (row+1, col-1),
                        (row+0, col-1),
                        (row-1, col-1)
                    ]
        
            for possible_move in possible_moves:
                possible_move_row, possible_move_col = possible_move
                if Square.in_range(possible_move_row, possible_move_col):
                    if self.squares[possible_move_row][possible_move_col].isempty_or_enemy(piece.color):
                        initial = Square(row, col)
                        final = Square(possible_move_row, possible_move_col)
                        move = Move(initial, final)
                        if bool:
                            if not self.in_check(piece, move):
                                piece.add_move(move)
                            else:
                                break
                        else:
                            piece.add_move(move)

            if not piece.moved:
                # queen castling
                left_rook = self.squares[row][0].piece
                if isinstance(left_rook, Rook):
                    if not left_rook.moved:
                        for c in range(1, 4):
                            # castling is not possible because there are pieces in between ?
                            if self.squares[row][c].has_piece():
                                break

                            if c == 3:
                                # adds left rook to king
                                piece.left_rook = left_rook

                                # rook move
                                initial = Square(row, 0)
                                final = Square(row, 3)
                                moveR = Move(initial, final)

                                # king move
                                initial = Square(row, col)
                                final = Square(row, 2)
                                moveK = Move(initial, final)

                                # check potencial checks
                                if bool:
                                    if not self.in_check(piece, moveK) and not self.in_check(left_rook, moveR):
                                        # append new move to rook
                                        left_rook.add_move(moveR)
                                        # append new move to king
                                        piece.add_move(moveK)
                                else:
                                    # append new move to rook
                                    left_rook.add_move(moveR)
                                    # append new move king
                                    piece.add_move(moveK)

                # king castling
                right_rook = self.squares[row][7].piece
                if isinstance(right_rook, Rook):
                    if not right_rook.moved:
                        for c in range(5, 7):
                            # castling is not possible because there are pieces in between ?
                            if self.squares[row][c].has_piece():
                                break

                            if c == 6:
                                # adds right rook to king
                                piece.right_rook = right_rook

                                # rook move
                                initial = Square(row, 7)
                                final = Square(row, 5)
                                moveR = Move(initial, final)

                                # king move
                                initial = Square(row, col)
                                final = Square(row, 6)
                                moveK = Move(initial, final)

                                # check potencial checks
                                if bool:
                                    if not self.in_check(piece, moveK) and not self.in_check(right_rook, moveR):
                                        # append new move to rook
                                        right_rook.add_move(moveR)
                                        # append new move to king
                                        piece.add_move(moveK)
                                else:
                                    # append new move to rook
                                    right_rook.add_move(moveR)
                                    # append new move king
                                    piece.add_move(moveK)

        if isinstance(piece, Pawn): 
            pawn_moves()

        elif isinstance(piece, Knight): 
            knight_moves()

        elif isinstance(piece, Bishop): 
            straightline_moves([
                (-1, 1), # up-right
                (-1, -1), # up-left
                (1, 1), # down-right
                (1, -1), # down-left
            ])

        elif isinstance(piece, Rook): 
            straightline_moves([
                (-1, 0), # up
                (0, 1), # right
                (1, 0), # down
                (0, -1), # left
            ])

        elif isinstance(piece, Queen): 
            straightline_moves([
                (-1, 1), # up-right
                (-1, -1), # up-left
                (1, 1), # down-right
                (1, -1), # down-left
                (-1, 0), # up
                (0, 1), # right
                (1, 0), # down
                (0, -1) # left
            ])
        elif isinstance(piece, King): king_moves()

    def _create(self):
        
        for row in range(ROWS):
            for col in range(COLS):
                self.squares[row][col] = Square(row,col)

    def _add_pieces(self, color):
        row_pawn, row_other = (6,7) if color == 'white' else (1,0)

        for col in range(COLS):
            self.squares[row_pawn][col] = Square(row_pawn, col, Pawn(color))

        self.squares[row_other][1] = Square(row_other, 1, Knight(color))
        self.squares[row_other][6] = Square(row_other, 6, Knight(color))

        self.squares[row_other][2] = Square(row_other, 2, Bishop(color))
        self.squares[row_other][5] = Square(row_other, 5, Bishop(color))

        self.squares[row_other][0] = Square(row_other, 0, Rook(color))
        self.squares[row_other][7] = Square(row_other, 7, Rook(color))

        self.squares[row_other][3] = Square(row_other, 3, Queen(color))

        self.squares[row_other][4] = Square(row_other, 4, King(color))

    def in_check(self,piece,move):
        temp_board = copy.deepcopy(self)
        temp_piece = temp_board.squares[move.initial.row][move.initial.col].piece

        temp_board.move(temp_piece, move)
        king_position = None
        for row in range(ROWS):
            for col in range(COLS):
                candidate = temp_board.squares[row][col].piece
                if isinstance(candidate, King) and candidate.color == piece.color:
                    king_position = (row, col)
                    break
            if king_position is not None:
                break

        if king_position is None:
            return True

        return temp_board.is_attacked(
            king_position[0], king_position[1], 'black' if piece.color == 'white' else 'white'
        )

    def is_attacked(self, row, col, by_color):
        for attacker_row in range(ROWS):
            for attacker_col in range(COLS):
                attacker = self.squares[attacker_row][attacker_col].piece
                if attacker is None or attacker.color != by_color:
                    continue

                row_distance = row - attacker_row
                col_distance = col - attacker_col

                if isinstance(attacker, Pawn):
                    if row_distance == attacker.dir and abs(col_distance) == 1:
                        return True
                elif isinstance(attacker, Knight):
                    if (abs(row_distance), abs(col_distance)) in ((1, 2), (2, 1)):
                        return True
                elif isinstance(attacker, King):
                    if max(abs(row_distance), abs(col_distance)) == 1:
                        return True
                else:
                    is_diagonal = abs(row_distance) == abs(col_distance)
                    is_straight = row_distance == 0 or col_distance == 0
                    if not (is_diagonal or is_straight):
                        continue

                    row_step = 0 if row_distance == 0 else (1 if row_distance > 0 else -1)
                    col_step = 0 if col_distance == 0 else (1 if col_distance > 0 else -1)
                    check_row = attacker_row + row_step
                    check_col = attacker_col + col_step
                    blocked = False
                    while (check_row, check_col) != (row, col):
                        if self.squares[check_row][check_col].has_piece():
                            blocked = True
                            break
                        check_row += row_step
                        check_col += col_step

                    if not blocked:
                        if isinstance(attacker, Bishop) and is_diagonal:
                            return True
                        if isinstance(attacker, Rook) and is_straight:
                            return True
                        if isinstance(attacker, Queen):
                            return True

        return False