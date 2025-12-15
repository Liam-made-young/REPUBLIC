# REPUBLIC - Turn-Based Strategy Game

A turn-based strategy game built with Python and Pygame, featuring fog of war, multiple unit types, territorial conquest, upgradeable buildings, and online multiplayer support.

![REPUBLIC Game](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux%20%7C%20Web-blue)
![Python](https://img.shields.io/badge/Python-3.8%2B-green)
![License](https://img.shields.io/badge/License-Educational-orange)

## Features

- **2-4 Player Support** - Local hot-seat or online multiplayer
- **Online Multiplayer** - Play with friends anywhere via room codes
- **Multiple Unit Types**:
  - **Warrior** - Balanced fighter (10 HP, 5 DMG, 3 MOV)
  - **Swordsman** - High damage dealer (8 HP, 8 DMG, 3 MOV)
  - **Shieldman** - Defensive tank (15 HP, 3 DMG, 2 MOV)
  - **Runner** - Fast scout (6 HP, 4 DMG, 6 MOV)
  - **Tank** - Heavy unit with chain attacks (30 HP, 20 DMG, 4 MOV)
  - **Seer** - Automated scout that explores fog of war
- **Buildings** (all upgradeable with SHIFT+Click):
  - **Capital** - Spawn point for units (10g) → Upgrade (20g) = 50% off troops
  - **Hospital** - Heals nearby units 5x5 (8g) → Upgrade (20g) = 9x9 heal radius
  - **Mine** - On granite, +1 gold/turn (6g) → Upgrade (10g) = +2 gold/turn
- **Economy**:
  - **Chickens** - Spawn on grass tiles, worth 1 gold
  - **Black Chickens** - Rare inverted chickens worth 3 gold!
  - **Gold** - Spawns on granite/rock tiles, worth 1 gold
  - **Shiny Gold** - Rare bright gold worth 3 gold!
  - **Mines** - Passive income on granite tiles
- **Fog of War** - Strategic visibility system
- **LAN Multiplayer** - One-click LAN server toggle in main menu
- **Dark Souls-inspired UI** - Ornate panels and gold accents
- **Cross-platform** - Windows, macOS, Linux, and Web

---

## Quick Start

### Option 1: Run from Source

```bash
# Clone the repository
git clone https://github.com/yourusername/republic.git
cd republic

# Install dependencies
pip install -r requirements.txt

# Run the game
python republic_main.py
```

### Option 2: Download Executable

Download the pre-built executable for your platform from the [Releases](https://github.com/yourusername/republic/releases) page.

- **Windows**: `REPUBLIC.exe`
- **macOS**: `REPUBLIC.app` or `REPUBLIC.dmg`
- **Linux**: `REPUBLIC`

---

## Building Executables

### Prerequisites

```bash
pip install pyinstaller pygame-ce noise
```

### Build for Your Platform

```bash
# Simple build (recommended)
python build_exe.py

# Clean build (removes previous artifacts)
python build_exe.py --clean

# Build as directory (faster startup, larger size)
python build_exe.py --onedir

# macOS: Create DMG installer
python build_exe.py --dmg
```

### Build Output

- **Windows**: `dist/REPUBLIC.exe`
- **macOS**: `dist/REPUBLIC.app` or `dist/REPUBLIC.dmg`
- **Linux**: `dist/REPUBLIC`

### Distribution

**Windows:**
- Share the `REPUBLIC.exe` file directly
- Users can double-click to run

**macOS:**
- Share the `.app` bundle or `.dmg` file
- Users may need to right-click → Open on first run (Gatekeeper)

**Linux:**
- Share the `REPUBLIC` file
- Users may need to run: `chmod +x REPUBLIC`

---

## Online Multiplayer

REPUBLIC supports online multiplayer through a WebSocket relay server. Players can create or join games using a 4-character room code.

### How It Works

1. **Host** creates a room and gets a code (e.g., `ABCD`)
2. **Host** shares the code with friends
3. **Friends** join using the code
4. Game state syncs automatically between players

### Option A: Use a Public Server

If a public server is available, the game will connect automatically. Check the game's network settings for the server URL.

### Option B: Built-in LAN Server (Easiest!)

The game has a built-in LAN server toggle:

1. Open the main menu (ESC or hamburger button)
2. Click **"LAN Server: OFF"** to turn it **ON**
3. The button will show your local IP address (e.g., `ws://192.168.1.100:8765`)
4. Share this address with friends on your network
5. They connect using this address in their game

The server automatically stops when you close the game.

### Option C: Manual Relay Server

For more control, run the relay server manually:

```bash
# Install websockets
pip install websockets

# Run the relay server
python relay_server.py
```

The server will start on port `8765` by default.

### Option C: Deploy to Free Hosting

Deploy `relay_server.py` to a free hosting service:

| Service | Free Tier | Setup Difficulty |
|---------|-----------|------------------|
| [Render](https://render.com) | Yes | Easy |
| [Railway](https://railway.app) | Yes | Easy |
| [Fly.io](https://fly.io) | Yes | Medium |
| [Glitch](https://glitch.com) | Yes | Easy |
| [Heroku](https://heroku.com) | Limited | Medium |

**Example Render deployment:**
1. Create a new Web Service
2. Connect your GitHub repo or upload `relay_server.py`
3. Set start command: `python relay_server.py`
4. Set environment variable: `PORT=10000`
5. Deploy and get your URL (e.g., `wss://republic-relay.onrender.com`)

### Sharing the Game with Friends

To play online with friends:

1. **Send them the executable** (or have them download from releases)
2. **Share the relay server URL** (if self-hosting)
3. **Create a room** and share the 4-character code
4. **They join** using the code
5. **Play!**

---

## Web Version (GitHub Pages)

The game can run in a web browser using [Pygbag](https://pygame-web.github.io/).

### Building for Web

```bash
# Install Pygbag
pip install pygbag

# Build the web version
pygbag --build .

# Test locally
pygbag .
# Then open http://localhost:8000
```

### Deploying to GitHub Pages

1. Build the web version (creates `build/web/` folder)
2. Copy contents of `build/web/` to your repository's root or `docs/` folder
3. Enable GitHub Pages in repository Settings → Pages
4. Access at `https://yourusername.github.io/repository-name/`

---

## Controls

| Key | Action |
|-----|--------|
| **Left Click** | Select units, move, attack, interact with UI |
| **Right Click** | Cancel selection / placement mode |
| **ESC** | Open menu / Cancel current action |
| **Enter** | End turn |
| **F11** | Toggle fullscreen |
| **W/A/S/D** | Pan camera |
| **Q/E** | Zoom out/in |
| **SHIFT+Click** | Upgrade building (capital/hospital/mine) |

---

## How to Play

### Basic Gameplay

1. **Start a New Game** - Click "New Game" and configure players, colors, and map size
2. **Spawn Units** - Click on your capital to open the unit creation menu
3. **Move Units** - Click a unit to select it, then click a destination tile
4. **Attack Enemies** - Move your unit onto an enemy unit to attack
5. **Build Structures** - Use the "Create" menu to place new capitals or hospitals
6. **Spawn Seers** - Seers automatically explore the fog of war each turn
7. **End Turn** - Click "End Turn" or press Enter

### Win Condition

Destroy all enemy capitals and units to win!

### Tips

- **Fog of War**: You can only see tiles revealed by your capitals, units, and seers
- **Chickens & Gold**: Chickens spawn on grass, gold spawns on granite - both give money!
- **Rare Pickups**: Black chickens and shiny gold are worth 3x normal value!
- **Seers**: Cost-effective scouts (8 gold) that move automatically toward unexplored areas
- **Hospitals**: Build near the front lines (8 gold) to heal troops (1 gold per heal)
- **Mines**: Build on granite tiles (6 gold) for +1 gold passive income each turn
- **Upgrades**: SHIFT+Click any building to upgrade it!
  - **Capital** (20g): Halves the cost of all troops spawned from it
  - **Hospital** (20g): Expands heal radius from 5x5 to 9x9
  - **Mine** (10g): Doubles income from 1 to 2 gold per turn
- **Tank Chain Attacks**: Tanks can continue moving after killing an enemy
- **Capital Placement**: New capitals (10 gold) must be placed on revealed tiles, 14+ tiles from other capitals
- **Defeated Players**: Players who lose all capitals and units are eliminated and their turns are skipped

---

## Project Structure

```
REPUBLIC/
├── republic_main.py    # Main game entry point
├── game_state.py       # Turn management and game state
├── team.py             # Team/player management
├── character.py        # Unit types and combat
├── capital.py          # Capital buildings
├── hospital.py         # Hospital healing mechanics
├── seer.py             # Automated scout units
├── world.py            # Map generation
├── camera.py           # Camera and viewport
├── renderer.py         # Game rendering
├── ui.py               # In-game UI elements
├── main_menu.py        # Main menu system
├── fog_of_war.py       # Visibility system
├── money.py            # Economy/gold pickups
├── assets.py           # Asset loading
├── network.py          # Online multiplayer support
├── relay_server.py     # Self-hostable relay server (auto-started from menu)
├── mine.py             # Mine building (gold generation)
├── build_exe.py        # Executable build script
├── assets/             # Game assets (textures, sprites)
├── index.html          # Web version entry point
└── requirements.txt    # Python dependencies
```

---

## Requirements

### For Running from Source
- Python 3.8+
- pygame-ce >= 2.5.0
- noise >= 1.2.2

### For Building Executables
- pyinstaller >= 6.0.0

### For Web Version
- pygbag >= 0.9.0

### For Online Multiplayer
- websockets >= 12.0

Install all with:
```bash
pip install -r requirements.txt
```

---

## Troubleshooting

### Game won't start
- Ensure Python 3.8+ is installed
- Run `pip install -r requirements.txt`
- Check console for error messages

### Executable shows antivirus warning
- This is common for PyInstaller executables
- Add an exception in your antivirus software
- The source code is available for inspection

### macOS: "App is damaged" or "unidentified developer"
- Right-click the app → Open
- Or: System Preferences → Security → "Open Anyway"
- Or: `xattr -cr REPUBLIC.app` in Terminal

### Online play not connecting
- Check if the relay server is running
- Verify the server URL is correct
- Ensure port 8765 is not blocked by firewall
- For internet play, ensure port forwarding is set up

### Screen scaling issues
- Press F11 to toggle fullscreen
- The game supports window resizing
- UI elements will reposition automatically

---

## License

This project is for educational purposes.

---

## Credits

Built with:
- [Pygame](https://www.pygame.org/) - Game framework
- [Pygbag](https://pygame-web.github.io/) - Web deployment
- [PyInstaller](https://pyinstaller.org/) - Executable packaging
- [Websockets](https://websockets.readthedocs.io/) - Online multiplayer

---

## Contributing

Contributions are welcome! Feel free to:
- Report bugs
- Suggest features
- Submit pull requests

---

*Conquer. Build. Rule.*