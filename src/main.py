import argparse
import sys

import pygame

from const import *
from game import Game
from move import Move
from online import OnlineClient
from square import Square


class Main:
    def __init__(self, online_url=None, room=None):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Chess")
        self.game = Game()
        self.online = None
        if online_url:
            self.online = OnlineClient(online_url, room)
            self.online.start()

    def _inside_board(self, pos):
        return 0 <= pos[0] < WIDTH and 0 <= pos[1] < HEIGHT

    def _apply_move(self, move):
        board = self.game.board
        piece = board.squares[move.initial.row][move.initial.col].piece
        if piece is None:
            return
        captured = board.squares[move.final.row][move.final.col].has_piece()
        board.move(piece, move)
        self.game.play_sound(captured)
        self.game.next_turn()

    def _process_online_messages(self):
        if self.online is None:
            return
        for message in self.online.poll():
            message_type = message.get("type")
            if message_type == "joined":
                self.online.color = message["color"]
                pygame.display.set_caption(
                    f"Chess - sala {self.online.room} - {message['color']}"
                )
            elif message_type == "move":
                initial = message["initial"]
                final = message["final"]
                self._apply_move(Move(
                    Square(initial["row"], initial["col"]),
                    Square(final["row"], final["col"]),
                ))
            elif message_type == "error":
                pygame.display.set_caption(f"Chess - {message['message']}")
            elif message_type == "disconnected":
                pygame.display.set_caption("Chess - desconectado")

    def mainloop(self):
        game = self.game
        screen = self.screen
        dragger = game.dragger
        board = game.board

        while True:
            self._process_online_messages()
            for event in pygame.event.get():
                if event.type == pygame.MOUSEBUTTONDOWN and self._inside_board(event.pos):
                    dragger.update_mouse(event.pos)
                    clicked_row = dragger.mouseY // SQSIZE
                    clicked_col = dragger.mouseX // SQSIZE
                    square = board.squares[clicked_row][clicked_col]
                    if square.has_piece() and square.piece.color == game.next_player:
                        if self.online and self.online.color != game.next_player:
                            continue
                        board.calc_moves(square.piece, clicked_row, clicked_col, bool=True)
                        dragger.save_initial(event.pos)
                        dragger.drag_piece(square.piece)

                elif event.type == pygame.MOUSEMOTION and self._inside_board(event.pos):
                    motion_row = event.pos[1] // SQSIZE
                    motion_col = event.pos[0] // SQSIZE
                    game.set_hover(motion_row, motion_col)
                    if dragger.dragging:
                        dragger.update_mouse(event.pos)
                        game.show_hover(screen)

                elif event.type == pygame.MOUSEBUTTONUP:
                    if dragger.dragging and self._inside_board(event.pos):
                        dragger.update_mouse(event.pos)
                        released_row = dragger.mouseY // SQSIZE
                        released_col = dragger.mouseX // SQSIZE
                        move = Move(
                            Square(dragger.initial_row, dragger.initial_col),
                            Square(released_row, released_col),
                        )
                        if board.valid_move(dragger.piece, move):
                            if self.online:
                                self.online.send_move(move.initial, move.final)
                            else:
                                self._apply_move(move)
                    dragger.undrag_piece()

                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_t:
                        game.change_theme()
                    elif event.key == pygame.K_r and self.online is None:
                        game.reset()
                        game = self.game
                        dragger = game.dragger
                        board = game.board
                    elif event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()

                elif event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

            game.show_bg(screen)
            game.show_moves(screen)
            game.show_last_move(screen)
            game.show_pieces(screen)
            game.show_hover(screen)
            if dragger.dragging:
                dragger.update_blit(screen)
            pygame.display.update()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Cliente de ajedrez Pygame")
    parser.add_argument("--online", metavar="WS_URL", help="URL WebSocket del servidor")
    parser.add_argument("--room", default="partida", help="Código de sala compartido")
    args = parser.parse_args()
    Main(args.online, args.room).mainloop()
