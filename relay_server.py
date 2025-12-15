"""
Simple WebSocket relay server for REPUBLIC multiplayer.

This is a standalone server that can be self-hosted to enable online multiplayer.

Run locally:
    python relay_server.py

Deploy to free hosting services:
    - Heroku (free tier with limitations)
    - Glitch (free) - https://glitch.com
    - Railway (free tier) - https://railway.app
    - Render (free tier) - https://render.com
    - Fly.io (free tier) - https://fly.io
    - Any VPS with Python

Requirements:
    pip install websockets

Environment Variables:
    PORT - Port to run on (default: 8765)

Usage:
    1. Run this server somewhere accessible (localhost for LAN, or deploy for internet)
    2. In the game, connect to the server URL:
       - Local: ws://localhost:8765
       - Deployed: wss://your-server-url.com
"""

import asyncio
import json
import os
import time
from collections import defaultdict
from typing import Dict, Optional, Set

try:
    import websockets
    from websockets.server import WebSocketServerProtocol
except ImportError:
    print("ERROR: websockets library not installed")
    print("Install with: pip install websockets")
    exit(1)


# =============================================================================
# Data Structures
# =============================================================================


class Room:
    """Represents a game room."""

    def __init__(self, code: str, host_id: str):
        self.code = code
        self.host_id = host_id
        self.players: Dict[str, WebSocketServerProtocol] = {}
        self.player_info: Dict[str, dict] = {}
        self.game_started = False
        self.created_at = time.time()
        self.last_activity = time.time()

    def add_player(
        self, player_id: str, websocket: WebSocketServerProtocol, info: dict
    ):
        """Add a player to the room."""
        self.players[player_id] = websocket
        self.player_info[player_id] = info
        self.last_activity = time.time()

    def remove_player(self, player_id: str):
        """Remove a player from the room."""
        if player_id in self.players:
            del self.players[player_id]
        if player_id in self.player_info:
            del self.player_info[player_id]
        self.last_activity = time.time()

    def is_empty(self) -> bool:
        """Check if the room is empty."""
        return len(self.players) == 0

    def is_full(self) -> bool:
        """Check if the room is full (max 4 players)."""
        return len(self.players) >= 4

    def get_player_count(self) -> int:
        """Get the number of players in the room."""
        return len(self.players)


# Global state
rooms: Dict[str, Room] = {}  # room_code -> Room
player_rooms: Dict[str, str] = {}  # player_id -> room_code
connected_clients: Set[WebSocketServerProtocol] = set()

# Statistics
stats = {
    "total_connections": 0,
    "total_rooms_created": 0,
    "total_games_played": 0,
    "server_start_time": time.time(),
}


# =============================================================================
# Message Handling
# =============================================================================


async def send_json(
    websocket: WebSocketServerProtocol, msg_type: str, data: dict = None
):
    """Send a JSON message to a client."""
    message = {
        "type": msg_type,
        "data": data or {},
        "timestamp": time.time(),
    }
    try:
        await websocket.send(json.dumps(message))
    except Exception as e:
        print(f"Error sending message: {e}")


async def broadcast_to_room(
    room: Room, msg_type: str, data: dict, exclude_id: str = None
):
    """Broadcast a message to all players in a room."""
    message = json.dumps(
        {
            "type": msg_type,
            "data": data,
            "timestamp": time.time(),
        }
    )

    for player_id, websocket in room.players.items():
        if player_id != exclude_id:
            try:
                await websocket.send(message)
            except Exception as e:
                print(f"Error broadcasting to {player_id}: {e}")


async def handle_create_room(
    websocket: WebSocketServerProtocol, sender_id: str, data: dict
):
    """Handle room creation request."""
    room_code = data.get("room_code", "").upper()
    player_name = data.get("player_name", "Host")
    color_key = data.get("color_key", "red")

    if not room_code or len(room_code) != 4:
        await send_json(websocket, "room_error", {"message": "Invalid room code"})
        return

    if room_code in rooms:
        await send_json(
            websocket,
            "room_error",
            {"message": "Room already exists. Try a different code."},
        )
        return

    # Create the room
    room = Room(room_code, sender_id)
    room.add_player(
        sender_id,
        websocket,
        {
            "player_id": sender_id,
            "name": player_name,
            "color_key": color_key,
            "is_host": True,
            "is_ready": True,
        },
    )

    rooms[room_code] = room
    player_rooms[sender_id] = room_code

    stats["total_rooms_created"] += 1

    await send_json(websocket, "room_created", {"room_code": room_code})
    print(f"[ROOM] Created: {room_code} by {player_name} ({sender_id[:8]}...)")


async def handle_join_room(
    websocket: WebSocketServerProtocol, sender_id: str, data: dict
):
    """Handle room join request."""
    room_code = data.get("room_code", "").upper()
    player_name = data.get("player_name", "Player")
    color_key = data.get("color_key", "blue")

    if not room_code or room_code not in rooms:
        await send_json(
            websocket,
            "room_error",
            {"message": "Room not found. Check the code and try again."},
        )
        return

    room = rooms[room_code]

    if room.is_full():
        await send_json(
            websocket, "room_error", {"message": "Room is full (max 4 players)."}
        )
        return

    if room.game_started:
        await send_json(
            websocket, "room_error", {"message": "Game already in progress."}
        )
        return

    # Check for duplicate color
    used_colors = {info.get("color_key") for info in room.player_info.values()}
    if color_key in used_colors:
        # Assign a different color
        available_colors = ["red", "blue", "green", "purple"]
        for c in available_colors:
            if c not in used_colors:
                color_key = c
                break

    # Add player to room
    player_info = {
        "player_id": sender_id,
        "name": player_name,
        "color_key": color_key,
        "is_host": False,
        "is_ready": True,
    }
    room.add_player(sender_id, websocket, player_info)
    player_rooms[sender_id] = room_code

    # Send join confirmation with existing players
    existing_players = [
        info for pid, info in room.player_info.items() if pid != sender_id
    ]
    await send_json(
        websocket,
        "room_joined",
        {
            "room_code": room_code,
            "players": existing_players,
            "assigned_color": color_key,
        },
    )

    # Notify other players
    await broadcast_to_room(
        room, "player_joined", {"player": player_info}, exclude_id=sender_id
    )

    print(
        f"[ROOM] {player_name} ({sender_id[:8]}...) joined {room_code} ({room.get_player_count()} players)"
    )


async def handle_leave_room(sender_id: str):
    """Handle a player leaving a room."""
    if sender_id not in player_rooms:
        return

    room_code = player_rooms[sender_id]
    del player_rooms[sender_id]

    if room_code not in rooms:
        return

    room = rooms[room_code]
    player_info = room.player_info.get(sender_id, {})
    player_name = player_info.get("name", "Unknown")

    room.remove_player(sender_id)

    # Notify remaining players
    await broadcast_to_room(room, "player_left", {"player_id": sender_id})

    print(
        f"[ROOM] {player_name} ({sender_id[:8]}...) left {room_code} ({room.get_player_count()} players)"
    )

    # Clean up empty rooms
    if room.is_empty():
        del rooms[room_code]
        print(f"[ROOM] Deleted empty room: {room_code}")
    elif sender_id == room.host_id and room.players:
        # Transfer host to another player
        new_host_id = next(iter(room.players.keys()))
        room.host_id = new_host_id
        if new_host_id in room.player_info:
            room.player_info[new_host_id]["is_host"] = True
        await broadcast_to_room(room, "host_changed", {"new_host_id": new_host_id})
        print(f"[ROOM] Host transferred in {room_code}")


async def handle_game_message(
    sender_id: str, message_str: str, msg_type: str, data: dict
):
    """Handle game-related messages (state, actions, etc.)."""
    room_code = data.get("room_code") or player_rooms.get(sender_id)

    if not room_code or room_code not in rooms:
        return

    room = rooms[room_code]
    room.last_activity = time.time()

    if msg_type == "game_start":
        room.game_started = True
        stats["total_games_played"] += 1
        print(f"[GAME] Started in room {room_code}")

    # Broadcast the message to all other players in the room
    for player_id, websocket in room.players.items():
        if player_id != sender_id:
            try:
                await websocket.send(message_str)
            except Exception as e:
                print(f"Error forwarding message to {player_id}: {e}")


async def handle_message(websocket: WebSocketServerProtocol, message_str: str):
    """Handle an incoming message from a client."""
    try:
        message = json.loads(message_str)
        msg_type = message.get("type")
        data = message.get("data", {})
        sender_id = message.get("sender_id")

        if not sender_id:
            await send_json(websocket, "error", {"message": "Missing sender_id"})
            return

        if msg_type == "create_room":
            await handle_create_room(websocket, sender_id, data)

        elif msg_type == "join_room":
            await handle_join_room(websocket, sender_id, data)

        elif msg_type == "leave_room":
            await handle_leave_room(sender_id)

        elif msg_type in (
            "game_state",
            "game_action",
            "turn_end",
            "game_start",
            "chat",
        ):
            await handle_game_message(sender_id, message_str, msg_type, data)

        elif msg_type == "ping":
            await send_json(websocket, "pong", {"server_time": time.time()})

        elif msg_type == "get_stats":
            await send_json(
                websocket,
                "stats",
                {
                    "active_rooms": len(rooms),
                    "connected_players": len(connected_clients),
                    "uptime": time.time() - stats["server_start_time"],
                    **stats,
                },
            )

        else:
            print(f"[WARN] Unknown message type: {msg_type}")

    except json.JSONDecodeError:
        print(f"[ERROR] Invalid JSON received")
        await send_json(websocket, "error", {"message": "Invalid JSON"})

    except Exception as e:
        print(f"[ERROR] Error handling message: {e}")
        await send_json(websocket, "error", {"message": str(e)})


# =============================================================================
# Connection Handling
# =============================================================================


async def connection_handler(websocket: WebSocketServerProtocol, path: str = "/"):
    """Handle a WebSocket connection."""
    connected_clients.add(websocket)
    stats["total_connections"] += 1
    player_id = None

    remote = websocket.remote_address
    print(f"[CONNECT] New connection from {remote}")

    try:
        async for message in websocket:
            # Extract player_id from first message for tracking
            try:
                msg = json.loads(message)
                if not player_id:
                    player_id = msg.get("sender_id")
            except:
                pass

            await handle_message(websocket, message)

    except websockets.ConnectionClosed as e:
        print(f"[DISCONNECT] Connection closed: {e.code} {e.reason}")

    except Exception as e:
        print(f"[ERROR] Connection error: {e}")

    finally:
        connected_clients.discard(websocket)
        if player_id:
            await handle_leave_room(player_id)
        print(f"[DISCONNECT] Client disconnected ({len(connected_clients)} remaining)")


async def cleanup_stale_rooms():
    """Periodically clean up stale/inactive rooms."""
    while True:
        await asyncio.sleep(300)  # Run every 5 minutes

        current_time = time.time()
        stale_rooms = []

        for room_code, room in rooms.items():
            # Remove rooms inactive for more than 1 hour
            if current_time - room.last_activity > 3600:
                stale_rooms.append(room_code)

        for room_code in stale_rooms:
            room = rooms.pop(room_code, None)
            if room:
                # Clean up player mappings
                for player_id in room.players:
                    player_rooms.pop(player_id, None)
                print(f"[CLEANUP] Removed stale room: {room_code}")

        if stale_rooms:
            print(f"[CLEANUP] Removed {len(stale_rooms)} stale rooms")


async def print_status():
    """Periodically print server status."""
    while True:
        await asyncio.sleep(60)  # Every minute
        print(
            f"[STATUS] Rooms: {len(rooms)} | Clients: {len(connected_clients)} | "
            f"Total connections: {stats['total_connections']} | "
            f"Games played: {stats['total_games_played']}"
        )


# =============================================================================
# Main Entry Point
# =============================================================================


async def main():
    """Start the relay server."""
    port = int(os.environ.get("PORT", 8765))
    host = "0.0.0.0"  # Listen on all interfaces

    print("=" * 60)
    print("  REPUBLIC Multiplayer Relay Server")
    print("=" * 60)
    print(f"  Host: {host}")
    print(f"  Port: {port}")
    print(f"  WebSocket URL: ws://localhost:{port}")
    print("=" * 60)
    print()
    print("For local network play, share your local IP address.")
    print("For internet play, deploy this server to a hosting service.")
    print()
    print("Waiting for connections...")
    print()

    # Start background tasks
    asyncio.create_task(cleanup_stale_rooms())
    asyncio.create_task(print_status())

    # Start the WebSocket server
    async with websockets.serve(
        connection_handler,
        host,
        port,
        ping_interval=30,
        ping_timeout=10,
        max_size=10 * 1024 * 1024,  # 10 MB max message size
    ):
        await asyncio.Future()  # Run forever


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[SERVER] Shutting down...")
