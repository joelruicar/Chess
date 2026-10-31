# Chess

A Pygame chess client with local and online multiplayer modes.

## Requirements
Python 3.10+ is required. Install dependencies with:

```bash
python -m pip install -r requirements.txt
```

## Local game
```bash
python src/main.py
```

Controls: drag pieces to move; `T` changes the theme; `R` resets a local game;
`Esc` quits.

## Online game
The Python WebSocket server is authoritative. It assigns `white` or `black`,
validates moves, keeps each room in memory, and broadcasts valid moves to both
players. Each room supports two players.

Start the server locally:

```bash
PYTHONPATH=src python src/server.py --host 127.0.0.1 --port 8765
```

Start two clients with the same room:

```bash
python src/main.py --online ws://127.0.0.1:8765 --room local-game
```

For a public TLS endpoint:

```bash
python src/main.py --online wss://ajedrez.example.com --room game-42
```

Players only need the client. Docker and Cloudflare are needed only on the
machine hosting the server.

## Docker server
```bash
docker build -t chess-server .
docker run -d \
  --name chess-server \
  --restart unless-stopped \
  -p 127.0.0.1:8765:8765 \
  chess-server
```

Check the service with:

```bash
docker ps
docker logs -f chess-server
```

## Cloudflare Tunnel
Use a Cloudflare Tunnel to expose the local server without opening port 8765:

```text
ajedrez.example.com
    -> Cloudflare Tunnel
    -> http://127.0.0.1:8765
    -> chess-server
```

In the Cloudflare dashboard, create a published application with:

```text
Hostname: ajedrez.example.com
Service URL: http://127.0.0.1:8765
```

The client uses `wss://`; the tunnel origin uses `http://`. Do not use
`https://` or `wss://` for the origin because the Python server does not
terminate TLS.

If `cloudflared` runs in Docker, use host networking:

```bash
docker run -d \
  --name cloudflared \
  --restart unless-stopped \
  --network host \
  cloudflare/cloudflared:latest \
  tunnel --no-autoupdate run --token YOUR_TUNNEL_TOKEN
```

Keep the tunnel token private. Test the public endpoint with:

```bash
python - <<'PY'
import asyncio
import json
import websockets

async def main():
    async with websockets.connect("wss://ajedrez.example.com") as ws:
        await ws.send(json.dumps({"type": "join", "room": "health-check"}))
        print(await ws.recv())

asyncio.run(main())
PY
```

The expected response contains:

```json
{"type": "joined", "color": "white", "players": 1}
```

## Standalone clients
The `Build Chess client` GitHub Actions workflow creates independent clients
for Windows and Linux. It runs manually or when a `v*` tag is pushed.

Build locally on the current operating system:

```bash
python -m pip install -r requirements.txt -r build-requirements.txt
pyinstaller --clean Chess.spec
```

Build separately for each operating system.

Windows:

```powershell
.\Chess.exe --online wss://ajedrez.example.com --room game-42
```

Linux:

```bash
tar -xzf Chess-Linux.tar.gz
chmod +x Chess
./Chess --online wss://ajedrez.example.com --room game-42
```

Standalone clients include Python, Pygame, images, and sounds. Players do not
need to install Python or clone the repository.
## Current limitations
- Rooms and games are in memory and disappear when the server restarts.
- There is no authentication, matchmaking, persistence, or reconnection.
- A room is identified only by its name; use an unpredictable room code.
