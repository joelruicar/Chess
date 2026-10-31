import argparse
import asyncio
import json
from dataclasses import dataclass, field

from board import Board
from move import Move
from square import Square
from websockets.exceptions import ConnectionClosed
from websockets.asyncio.server import serve


@dataclass
class Room:
    board: Board = field(default_factory=Board)
    clients: dict = field(default_factory=dict)
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    moves_played: int = 0
    move_history: list = field(default_factory=list)


rooms = {}


async def send(websocket, message):
    await websocket.send(json.dumps(message))


async def broadcast(room, message):
    payload = json.dumps(message)
    disconnected = []
    for websocket in room.clients:
        try:
            await websocket.send(payload)
        except ConnectionClosed:
            disconnected.append(websocket)
    for websocket in disconnected:
        room.clients.pop(websocket, None)


async def handler(websocket):
    room = None
    try:
        first_message = json.loads(await websocket.recv())
        if first_message.get("type") != "join":
            await send(websocket, {"type": "error", "message": "El primer mensaje debe ser join."})
            return

        room_name = str(first_message.get("room", "")).strip()
        if not room_name or len(room_name) > 32:
            await send(websocket, {"type": "error", "message": "La sala debe tener entre 1 y 32 caracteres."})
            return

        room = rooms.setdefault(room_name, Room())
        async with room.lock:
            if len(room.clients) >= 2:
                await send(websocket, {"type": "error", "message": "La sala ya tiene dos jugadores."})
                return
            color = "white" if "white" not in room.clients.values() else "black"
            room.clients[websocket] = color
            await send(websocket, {
                "type": "joined",
                "color": color,
                "players": len(room.clients),
            })
            for move in room.move_history:
                await send(websocket, move)
            if len(room.clients) == 2:
                await broadcast(room, {"type": "start"})

        async for raw_message in websocket:
            message = json.loads(raw_message)
            if message.get("type") != "move":
                continue
            await process_move(room, websocket, message)
    except (ConnectionClosed, json.JSONDecodeError):
        pass
    finally:
        if room is not None:
            room.clients.pop(websocket, None)
            if not room.clients:
                rooms.pop(next((name for name, value in rooms.items() if value is room), None), None)


async def process_move(room, websocket, message):
    async with room.lock:
        color = room.clients.get(websocket)
        initial_data = message.get("initial", {})
        final_data = message.get("final", {})
        try:
            initial = Square(int(initial_data["row"]), int(initial_data["col"]))
            final = Square(int(final_data["row"]), int(final_data["col"]))
        except (KeyError, TypeError, ValueError):
            await send(websocket, {"type": "error", "message": "Movimiento con formato inválido."})
            return

        if not Square.in_range(initial.row, initial.col, final.row, final.col):
            await send(websocket, {"type": "error", "message": "Casillas fuera del tablero."})
            return
        piece = room.board.squares[initial.row][initial.col].piece
        expected_color = "white" if room.moves_played % 2 == 0 else "black"
        if color != expected_color or piece is None or piece.color != color:
            await send(websocket, {"type": "error", "message": "No es tu turno."})
            return

        room.board.calc_moves(piece, initial.row, initial.col)
        move = Move(initial, final)
        if not room.board.valid_move(piece, move):
            await send(websocket, {"type": "error", "message": "Movimiento ilegal."})
            return

        captured = room.board.squares[final.row][final.col].has_piece()
        room.board.move(piece, move)
        room.moves_played += 1
        move_message = {
            "type": "move",
            "initial": {"row": initial.row, "col": initial.col},
            "final": {"row": final.row, "col": final.col},
            "captured": captured,
        }
        room.move_history.append(move_message)
        await broadcast(room, move_message)


async def main(host, port):
    async with serve(handler, host, port):
        print(f"Servidor de ajedrez escuchando en ws://{host}:{port}")
        await asyncio.Future()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Servidor WebSocket para Chess")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    asyncio.run(main(args.host, args.port))
