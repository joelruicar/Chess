import asyncio
import json
import threading
from queue import Empty, Queue

import websockets


class OnlineClient:
    """Small asyncio/WebSocket client used by the Pygame main thread."""

    def __init__(self, url, room):
        self.url = url
        self.room = room
        self.color = None
        self._incoming = Queue()
        self._outgoing = Queue()
        self._ready = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._loop = None
        self._websocket = None
        self._closed = False

    def start(self):
        self._thread.start()

    def _run(self):
        asyncio.run(self._connection_loop())

    async def _connection_loop(self):
        self._loop = asyncio.get_running_loop()
        try:
            async with websockets.connect(self.url) as websocket:
                self._websocket = websocket
                await websocket.send(json.dumps({
                    "type": "join",
                    "room": self.room,
                }))
                self._ready.set()
                await self._receive_messages(websocket)
        except (OSError, websockets.WebSocketException) as error:
            self._incoming.put({
                "type": "error",
                "message": f"No se pudo conectar al servidor: {error}",
            })
        finally:
            self._closed = True
            self._incoming.put({"type": "disconnected"})

    async def _receive_messages(self, websocket):
        async for raw_message in websocket:
            self._incoming.put(json.loads(raw_message))
            await self._flush_outgoing(websocket)

    async def _flush_outgoing(self, websocket):
        while True:
            try:
                message = self._outgoing.get_nowait()
            except Empty:
                return
            await websocket.send(json.dumps(message))

    def send_move(self, initial, final):
        self._outgoing.put({
            "type": "move",
            "initial": {"row": initial.row, "col": initial.col},
            "final": {"row": final.row, "col": final.col},
        })
        if self._loop is not None and self._websocket is not None:
            asyncio.run_coroutine_threadsafe(
                self._flush_outgoing(self._websocket), self._loop
            )

    def poll(self):
        messages = []
        while True:
            try:
                messages.append(self._incoming.get_nowait())
            except Empty:
                return messages

    @property
    def connected(self):
        return self._ready.is_set() and not self._closed
