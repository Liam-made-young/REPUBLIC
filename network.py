"""
Network module for REPUBLIC online multiplayer.

This module provides simple peer-to-peer online play using a relay server approach.
Players can create or join game rooms using a room code.

Architecture:
- Uses WebSocket connection to a relay server
- Room-based matchmaking with 4-character codes
- Turn-based synchronization (syncs game state after each action)
- Works with both desktop (exe) and web versions

Usage:
    # Host a game
    network = NetworkManager()
    room_code = await network.create_room()
    print(f"Share this code: {room_code}")

    # Join a game
    network = NetworkManager()
    await network.join_room("ABCD")

    # Send game state after each turn
    await network.send_game_state(game_state_dict)

    # Receive opponent's moves
    state = await network.receive_game_state()
"""

import asyncio
import json
import random
import string
import time
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional

# Try to import websockets, fall back gracefully if not available
try:
    import websockets
    from websockets.client import WebSocketClientProtocol

    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False
    WebSocketClientProtocol = None


class ConnectionState(Enum):
    """Network connection states."""

    DISCONNECTED = auto()
    CONNECTING = auto()
    CONNECTED = auto()
    IN_ROOM = auto()
    GAME_ACTIVE = auto()
    ERROR = auto()


class MessageType(Enum):
    """Types of network messages."""

    # Room management
    CREATE_ROOM = "create_room"
    JOIN_ROOM = "join_room"
    LEAVE_ROOM = "leave_room"
    ROOM_CREATED = "room_created"
    ROOM_JOINED = "room_joined"
    PLAYER_JOINED = "player_joined"
    PLAYER_LEFT = "player_left"
    ROOM_ERROR = "room_error"

    # Game state
    GAME_START = "game_start"
    GAME_STATE = "game_state"
    GAME_ACTION = "game_action"
    TURN_END = "turn_end"
    GAME_OVER = "game_over"

    # Utility
    PING = "ping"
    PONG = "pong"
    CHAT = "chat"
    ERROR = "error"


@dataclass
class NetworkMessage:
    """A network message structure."""

    type: MessageType
    data: Dict[str, Any] = field(default_factory=dict)
    sender_id: Optional[str] = None
    timestamp: float = field(default_factory=time.time)

    def to_json(self) -> str:
        """Serialize message to JSON."""
        return json.dumps(
            {
                "type": self.type.value,
                "data": self.data,
                "sender_id": self.sender_id,
                "timestamp": self.timestamp,
            }
        )

    @classmethod
    def from_json(cls, json_str: str) -> "NetworkMessage":
        """Deserialize message from JSON."""
        obj = json.loads(json_str)
        return cls(
            type=MessageType(obj["type"]),
            data=obj.get("data", {}),
            sender_id=obj.get("sender_id"),
            timestamp=obj.get("timestamp", time.time()),
        )


@dataclass
class Player:
    """Represents a connected player."""

    player_id: str
    name: str
    color_key: str
    is_host: bool = False
    is_ready: bool = False
    is_connected: bool = True


class NetworkManager:
    """
    Manages network connections for online multiplayer.

    This class handles:
    - WebSocket connection to relay server
    - Room creation and joining
    - Game state synchronization
    - Message sending and receiving
    """

    # Default relay servers (can be self-hosted or use public ones)
    DEFAULT_RELAY_SERVERS = [
        "wss://republic-relay.glitch.me",  # Primary (needs to be set up)
        "wss://republic-game-relay.herokuapp.com",  # Backup
    ]

    def __init__(self, relay_url: Optional[str] = None):
        """
        Initialize the network manager.

        Args:
            relay_url: Custom relay server URL. If None, uses default servers.
        """
        if not WEBSOCKETS_AVAILABLE:
            print("WARNING: websockets library not installed. Online play disabled.")
            print("Install with: pip install websockets")

        self.relay_url = relay_url or self.DEFAULT_RELAY_SERVERS[0]
        self.websocket: Optional[WebSocketClientProtocol] = None
        self.state = ConnectionState.DISCONNECTED

        # Player info
        self.player_id: Optional[str] = None
        self.player_name: str = "Player"
        self.player_color: str = "red"
        self.is_host: bool = False

        # Room info
        self.room_code: Optional[str] = None
        self.players: Dict[str, Player] = {}

        # Callbacks
        self.on_player_joined: Optional[Callable[[Player], None]] = None
        self.on_player_left: Optional[Callable[[str], None]] = None
        self.on_game_state: Optional[Callable[[Dict], None]] = None
        self.on_game_action: Optional[Callable[[Dict], None]] = None
        self.on_chat_message: Optional[Callable[[str, str], None]] = None
        self.on_error: Optional[Callable[[str], None]] = None

        # Message queue for async processing
        self.message_queue: asyncio.Queue = asyncio.Queue()
        self.receive_task: Optional[asyncio.Task] = None

        # Connection settings
        self.reconnect_attempts = 3
        self.reconnect_delay = 2.0
        self.ping_interval = 30.0
        self.last_ping_time = 0

    def _generate_player_id(self) -> str:
        """Generate a unique player ID."""
        return "".join(random.choices(string.ascii_letters + string.digits, k=16))

    def _generate_room_code(self) -> str:
        """Generate a 4-character room code."""
        # Use uppercase letters and digits, excluding confusing characters
        chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
        return "".join(random.choices(chars, k=4))

    async def connect(self) -> bool:
        """
        Connect to the relay server.

        Returns:
            True if connected successfully, False otherwise.
        """
        if not WEBSOCKETS_AVAILABLE:
            self._handle_error("websockets library not installed")
            return False

        if self.state != ConnectionState.DISCONNECTED:
            return self.state in (
                ConnectionState.CONNECTED,
                ConnectionState.IN_ROOM,
                ConnectionState.GAME_ACTIVE,
            )

        self.state = ConnectionState.CONNECTING
        self.player_id = self._generate_player_id()

        for attempt in range(self.reconnect_attempts):
            try:
                print(f"Connecting to relay server (attempt {attempt + 1})...")
                self.websocket = await asyncio.wait_for(
                    websockets.connect(
                        self.relay_url,
                        ping_interval=self.ping_interval,
                        ping_timeout=10.0,
                    ),
                    timeout=10.0,
                )

                self.state = ConnectionState.CONNECTED
                print("Connected to relay server!")

                # Start background receive task
                self.receive_task = asyncio.create_task(self._receive_loop())

                return True

            except asyncio.TimeoutError:
                print(f"Connection attempt {attempt + 1} timed out")
            except Exception as e:
                print(f"Connection attempt {attempt + 1} failed: {e}")

            if attempt < self.reconnect_attempts - 1:
                await asyncio.sleep(self.reconnect_delay)

        self.state = ConnectionState.ERROR
        self._handle_error("Failed to connect to relay server")
        return False

    async def disconnect(self):
        """Disconnect from the relay server."""
        if self.receive_task:
            self.receive_task.cancel()
            try:
                await self.receive_task
            except asyncio.CancelledError:
                pass

        if self.websocket:
            await self.websocket.close()
            self.websocket = None

        self.state = ConnectionState.DISCONNECTED
        self.room_code = None
        self.players.clear()
        print("Disconnected from relay server")

    async def create_room(
        self, player_name: str = "Host", color_key: str = "red"
    ) -> Optional[str]:
        """
        Create a new game room.

        Args:
            player_name: The host player's display name.
            color_key: The host player's color.

        Returns:
            The room code if successful, None otherwise.
        """
        if self.state == ConnectionState.DISCONNECTED:
            if not await self.connect():
                return None

        self.player_name = player_name
        self.player_color = color_key
        self.is_host = True
        self.room_code = self._generate_room_code()

        # Send create room message
        message = NetworkMessage(
            type=MessageType.CREATE_ROOM,
            data={
                "room_code": self.room_code,
                "player_name": player_name,
                "color_key": color_key,
            },
            sender_id=self.player_id,
        )

        await self._send_message(message)

        # Wait for confirmation
        try:
            response = await asyncio.wait_for(self.message_queue.get(), timeout=5.0)
            if response.type == MessageType.ROOM_CREATED:
                self.state = ConnectionState.IN_ROOM
                # Add self as first player
                self.players[self.player_id] = Player(
                    player_id=self.player_id,
                    name=player_name,
                    color_key=color_key,
                    is_host=True,
                    is_ready=True,
                )
                print(f"Room created! Code: {self.room_code}")
                return self.room_code
            elif response.type == MessageType.ROOM_ERROR:
                self._handle_error(
                    response.data.get("message", "Failed to create room")
                )
                return None
        except asyncio.TimeoutError:
            self._handle_error("Timeout waiting for room creation confirmation")
            return None

        return None

    async def join_room(
        self, room_code: str, player_name: str = "Player", color_key: str = "blue"
    ) -> bool:
        """
        Join an existing game room.

        Args:
            room_code: The 4-character room code to join.
            player_name: The joining player's display name.
            color_key: The joining player's color.

        Returns:
            True if joined successfully, False otherwise.
        """
        if self.state == ConnectionState.DISCONNECTED:
            if not await self.connect():
                return False

        self.player_name = player_name
        self.player_color = color_key
        self.is_host = False
        self.room_code = room_code.upper()

        # Send join room message
        message = NetworkMessage(
            type=MessageType.JOIN_ROOM,
            data={
                "room_code": self.room_code,
                "player_name": player_name,
                "color_key": color_key,
            },
            sender_id=self.player_id,
        )

        await self._send_message(message)

        # Wait for confirmation
        try:
            response = await asyncio.wait_for(self.message_queue.get(), timeout=5.0)
            if response.type == MessageType.ROOM_JOINED:
                self.state = ConnectionState.IN_ROOM
                # Add self as player
                self.players[self.player_id] = Player(
                    player_id=self.player_id,
                    name=player_name,
                    color_key=color_key,
                    is_host=False,
                    is_ready=True,
                )
                # Add existing players from response
                for player_data in response.data.get("players", []):
                    pid = player_data["player_id"]
                    if pid != self.player_id:
                        self.players[pid] = Player(**player_data)
                print(f"Joined room: {self.room_code}")
                return True
            elif response.type == MessageType.ROOM_ERROR:
                self._handle_error(response.data.get("message", "Failed to join room"))
                return False
        except asyncio.TimeoutError:
            self._handle_error("Timeout waiting for room join confirmation")
            return False

        return False

    async def leave_room(self):
        """Leave the current room."""
        if self.room_code:
            message = NetworkMessage(
                type=MessageType.LEAVE_ROOM,
                data={"room_code": self.room_code},
                sender_id=self.player_id,
            )
            await self._send_message(message)

        self.room_code = None
        self.players.clear()
        self.state = ConnectionState.CONNECTED

    async def send_game_state(self, game_state: Dict[str, Any]):
        """
        Send the full game state to all players in the room.

        Args:
            game_state: Dictionary containing the full game state.
        """
        if self.state not in (ConnectionState.IN_ROOM, ConnectionState.GAME_ACTIVE):
            return

        message = NetworkMessage(
            type=MessageType.GAME_STATE,
            data={"room_code": self.room_code, "game_state": game_state},
            sender_id=self.player_id,
        )
        await self._send_message(message)

    async def send_game_action(self, action: Dict[str, Any]):
        """
        Send a game action to all players in the room.

        This is more efficient than sending full state for single actions.

        Args:
            action: Dictionary describing the action (e.g., move, attack, build).
        """
        if self.state not in (ConnectionState.IN_ROOM, ConnectionState.GAME_ACTIVE):
            return

        message = NetworkMessage(
            type=MessageType.GAME_ACTION,
            data={"room_code": self.room_code, "action": action},
            sender_id=self.player_id,
        )
        await self._send_message(message)

    async def send_turn_end(self):
        """Signal that the current player's turn has ended."""
        if self.state not in (ConnectionState.IN_ROOM, ConnectionState.GAME_ACTIVE):
            return

        message = NetworkMessage(
            type=MessageType.TURN_END,
            data={"room_code": self.room_code},
            sender_id=self.player_id,
        )
        await self._send_message(message)

    async def send_chat(self, text: str):
        """
        Send a chat message to all players in the room.

        Args:
            text: The chat message text.
        """
        if self.state not in (ConnectionState.IN_ROOM, ConnectionState.GAME_ACTIVE):
            return

        message = NetworkMessage(
            type=MessageType.CHAT,
            data={
                "room_code": self.room_code,
                "text": text,
                "player_name": self.player_name,
            },
            sender_id=self.player_id,
        )
        await self._send_message(message)

    async def start_game(self, initial_state: Dict[str, Any]):
        """
        Start the game (host only).

        Args:
            initial_state: The initial game state to send to all players.
        """
        if not self.is_host:
            print("Only the host can start the game")
            return

        self.state = ConnectionState.GAME_ACTIVE

        message = NetworkMessage(
            type=MessageType.GAME_START,
            data={"room_code": self.room_code, "initial_state": initial_state},
            sender_id=self.player_id,
        )
        await self._send_message(message)

    async def _send_message(self, message: NetworkMessage):
        """Send a message to the relay server."""
        if not self.websocket:
            return

        try:
            await self.websocket.send(message.to_json())
        except Exception as e:
            print(f"Error sending message: {e}")
            self._handle_error(str(e))

    async def _receive_loop(self):
        """Background task to receive messages from the server."""
        if not self.websocket:
            return

        try:
            async for raw_message in self.websocket:
                try:
                    message = NetworkMessage.from_json(raw_message)
                    await self._handle_message(message)
                except json.JSONDecodeError:
                    print(f"Invalid message received: {raw_message}")
                except Exception as e:
                    print(f"Error processing message: {e}")
        except websockets.ConnectionClosed:
            print("Connection closed by server")
            self.state = ConnectionState.DISCONNECTED
        except Exception as e:
            print(f"Receive loop error: {e}")
            self.state = ConnectionState.ERROR

    async def _handle_message(self, message: NetworkMessage):
        """Handle an incoming message."""
        # Messages that should go to the queue for await-based receiving
        queue_types = {
            MessageType.ROOM_CREATED,
            MessageType.ROOM_JOINED,
            MessageType.ROOM_ERROR,
        }

        if message.type in queue_types:
            await self.message_queue.put(message)
            return

        # Handle other message types with callbacks
        if message.type == MessageType.PLAYER_JOINED:
            player_data = message.data.get("player", {})
            player = Player(**player_data)
            self.players[player.player_id] = player
            if self.on_player_joined:
                self.on_player_joined(player)

        elif message.type == MessageType.PLAYER_LEFT:
            player_id = message.data.get("player_id")
            if player_id in self.players:
                del self.players[player_id]
            if self.on_player_left:
                self.on_player_left(player_id)

        elif message.type == MessageType.GAME_STATE:
            if self.on_game_state:
                self.on_game_state(message.data.get("game_state", {}))

        elif message.type == MessageType.GAME_ACTION:
            if self.on_game_action:
                self.on_game_action(message.data.get("action", {}))

        elif message.type == MessageType.GAME_START:
            self.state = ConnectionState.GAME_ACTIVE
            if self.on_game_state:
                self.on_game_state(message.data.get("initial_state", {}))

        elif message.type == MessageType.CHAT:
            if self.on_chat_message:
                self.on_chat_message(
                    message.data.get("player_name", "Unknown"),
                    message.data.get("text", ""),
                )

        elif message.type == MessageType.ERROR:
            self._handle_error(message.data.get("message", "Unknown error"))

        elif message.type == MessageType.PONG:
            # Handle ping response (for latency measurement)
            pass

    def _handle_error(self, error_message: str):
        """Handle an error."""
        print(f"Network error: {error_message}")
        if self.on_error:
            self.on_error(error_message)

    def get_player_count(self) -> int:
        """Get the number of players in the room."""
        return len(self.players)

    def get_players_list(self) -> List[Player]:
        """Get a list of all players in the room."""
        return list(self.players.values())

    def is_connected(self) -> bool:
        """Check if connected to the relay server."""
        return self.state in (
            ConnectionState.CONNECTED,
            ConnectionState.IN_ROOM,
            ConnectionState.GAME_ACTIVE,
        )

    def is_in_room(self) -> bool:
        """Check if currently in a room."""
        return self.state in (ConnectionState.IN_ROOM, ConnectionState.GAME_ACTIVE)

    def is_game_active(self) -> bool:
        """Check if a game is currently active."""
        return self.state == ConnectionState.GAME_ACTIVE


# =============================================================================
# Simple Relay Server (for self-hosting)
# =============================================================================

RELAY_SERVER_CODE = '''
"""
Simple WebSocket relay server for REPUBLIC multiplayer.

Run with: python -m websockets ws://localhost:8765

Or deploy to a service like:
- Heroku (free tier)
- Glitch (free)
- Railway (free tier)
- Render (free tier)
- Any VPS with Python

Requirements:
    pip install websockets
"""

import asyncio
import json
import websockets
from collections import defaultdict

# Store rooms and their players
rooms = {}  # room_code -> {players: {player_id: websocket}, host_id: str}
player_rooms = {}  # player_id -> room_code

async def handle_message(websocket, message_str):
    """Handle an incoming message from a client."""
    try:
        message = json.loads(message_str)
        msg_type = message.get("type")
        data = message.get("data", {})
        sender_id = message.get("sender_id")

        if msg_type == "create_room":
            room_code = data.get("room_code")
            if room_code in rooms:
                # Room already exists
                await websocket.send(json.dumps({
                    "type": "room_error",
                    "data": {"message": "Room already exists"}
                }))
                return

            rooms[room_code] = {
                "players": {sender_id: websocket},
                "host_id": sender_id,
                "player_info": {sender_id: {
                    "player_id": sender_id,
                    "name": data.get("player_name", "Host"),
                    "color_key": data.get("color_key", "red"),
                    "is_host": True
                }}
            }
            player_rooms[sender_id] = room_code

            await websocket.send(json.dumps({
                "type": "room_created",
                "data": {"room_code": room_code}
            }))
            print(f"Room created: {room_code}")

        elif msg_type == "join_room":
            room_code = data.get("room_code")
            if room_code not in rooms:
                await websocket.send(json.dumps({
                    "type": "room_error",
                    "data": {"message": "Room not found"}
                }))
                return

            room = rooms[room_code]
            if len(room["players"]) >= 4:
                await websocket.send(json.dumps({
                    "type": "room_error",
                    "data": {"message": "Room is full"}
                }))
                return

            # Add player to room
            room["players"][sender_id] = websocket
            player_info = {
                "player_id": sender_id,
                "name": data.get("player_name", "Player"),
                "color_key": data.get("color_key", "blue"),
                "is_host": False
            }
            room["player_info"][sender_id] = player_info
            player_rooms[sender_id] = room_code

            # Send join confirmation with existing players
            existing_players = [info for pid, info in room["player_info"].items() if pid != sender_id]
            await websocket.send(json.dumps({
                "type": "room_joined",
                "data": {
                    "room_code": room_code,
                    "players": existing_players
                }
            }))

            # Notify other players
            for pid, ws in room["players"].items():
                if pid != sender_id:
                    await ws.send(json.dumps({
                        "type": "player_joined",
                        "data": {"player": player_info}
                    }))

            print(f"Player {sender_id} joined room {room_code}")

        elif msg_type == "leave_room":
            await handle_leave(sender_id)

        elif msg_type in ("game_state", "game_action", "turn_end", "game_start", "chat"):
            # Broadcast to all other players in the room
            room_code = data.get("room_code") or player_rooms.get(sender_id)
            if room_code and room_code in rooms:
                room = rooms[room_code]
                for pid, ws in room["players"].items():
                    if pid != sender_id:
                        await ws.send(message_str)

    except Exception as e:
        print(f"Error handling message: {e}")
        await websocket.send(json.dumps({
            "type": "error",
            "data": {"message": str(e)}
        }))

async def handle_leave(player_id):
    """Handle a player leaving."""
    if player_id not in player_rooms:
        return

    room_code = player_rooms[player_id]
    del player_rooms[player_id]

    if room_code not in rooms:
        return

    room = rooms[room_code]
    if player_id in room["players"]:
        del room["players"][player_id]
    if player_id in room["player_info"]:
        del room["player_info"][player_id]

    # Notify remaining players
    for pid, ws in room["players"].items():
        await ws.send(json.dumps({
            "type": "player_left",
            "data": {"player_id": player_id}
        }))

    # Clean up empty rooms
    if not room["players"]:
        del rooms[room_code]
        print(f"Room {room_code} deleted (empty)")

    print(f"Player {player_id} left room {room_code}")

async def handler(websocket, path):
    """Handle a WebSocket connection."""
    player_id = None
    try:
        async for message in websocket:
            msg = json.loads(message)
            player_id = msg.get("sender_id")
            await handle_message(websocket, message)
    except websockets.ConnectionClosed:
        pass
    finally:
        if player_id:
            await handle_leave(player_id)

async def main():
    """Start the relay server."""
    port = 8765
    print(f"Starting REPUBLIC relay server on port {port}...")
    async with websockets.serve(handler, "0.0.0.0", port):
        await asyncio.Future()  # Run forever

if __name__ == "__main__":
    asyncio.run(main())
'''


def create_relay_server_file(output_path: str = "relay_server.py"):
    """
    Create a standalone relay server file that can be self-hosted.

    Args:
        output_path: Path where to save the relay server script.
    """
    with open(output_path, "w") as f:
        f.write(RELAY_SERVER_CODE)
    print(f"Relay server script created at: {output_path}")
    print("\nTo run locally: python relay_server.py")
    print("Then connect with: NetworkManager('ws://localhost:8765')")


# =============================================================================
# Game State Serialization Helpers
# =============================================================================


def serialize_game_state(game) -> Dict[str, Any]:
    """
    Serialize the game state for network transmission.

    Args:
        game: The Game instance from republic_main.py

    Returns:
        Dictionary containing serializable game state.
    """
    state = {
        "turn_count": game.game_state.turn_count,
        "current_phase": game.game_state.current_phase.value,
        "game_over": game.game_state.game_over,
        "winner": game.game_state.winner.value if game.game_state.winner else None,
        "teams": [],
        "money_pickups": [],
    }

    # Serialize teams
    for team in game.teams:
        team_data = {
            "side": team.side.value,
            "name": team.name,
            "color_key": team.color_key,
            "money": team.money,
            "characters": [],
            "capitals": [],
            "seers": [],
            "hospitals": [],
            "revealed_tiles": list(team.revealed_tiles),
        }

        # Serialize characters
        for char in team.characters:
            char_data = {
                "x": char.x,
                "y": char.y,
                "char_type": char.char_type.value
                if hasattr(char.char_type, "value")
                else char.char_type,
                "health": char.health,
                "max_health": char.max_health,
                "damage": char.damage,
                "movement_range": char.movement_range,
                "has_moved": char.has_moved,
                "has_attacked": char.has_attacked,
            }
            team_data["characters"].append(char_data)

        # Serialize capitals
        for cap in team.capitals:
            cap_data = {
                "x": cap.x,
                "y": cap.y,
                "has_spawned_this_turn": cap.has_spawned_this_turn,
            }
            team_data["capitals"].append(cap_data)

        # Serialize seers
        for seer in team.seers:
            seer_data = {
                "x": seer.x,
                "y": seer.y,
                "moves_remaining": seer.moves_remaining,
            }
            team_data["seers"].append(seer_data)

        # Serialize hospitals
        for hosp in team.hospitals:
            hosp_data = {
                "x": hosp.x,
                "y": hosp.y,
                "has_healed_this_turn": hosp.has_healed_this_turn,
            }
            team_data["hospitals"].append(hosp_data)

        state["teams"].append(team_data)

    # Serialize money pickups
    for money in game.money_pickups:
        state["money_pickups"].append(
            {
                "x": money.x,
                "y": money.y,
                "amount": money.amount,
            }
        )

    return state


def serialize_action(action_type: str, **kwargs) -> Dict[str, Any]:
    """
    Create a serializable action dictionary.

    Args:
        action_type: Type of action (move, attack, build, spawn, etc.)
        **kwargs: Action-specific parameters

    Returns:
        Dictionary describing the action.
    """
    return {"type": action_type, "timestamp": time.time(), **kwargs}


# Example actions:
# serialize_action("move
