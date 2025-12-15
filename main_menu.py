import asyncio
import socket
import subprocess
import sys
import threading
import time

import pygame

# Available colors for players
PLAYER_COLORS = {
    "red": {
        "name": "Red",
        "rgb": (200, 50, 50),
        "light": (255, 100, 100),
        "dark": (120, 30, 30),
    },
    "blue": {
        "name": "Blue",
        "rgb": (50, 100, 200),
        "light": (100, 150, 255),
        "dark": (30, 60, 120),
    },
    "green": {
        "name": "Green",
        "rgb": (50, 180, 50),
        "light": (100, 220, 100),
        "dark": (30, 100, 30),
    },
    "purple": {
        "name": "Purple",
        "rgb": (150, 50, 180),
        "light": (200, 100, 220),
        "dark": (90, 30, 110),
    },
}

# Available map sizes
MAP_SIZES = {
    "small": {"name": "Small", "width": 25, "height": 25},
    "medium": {"name": "Medium", "width": 75, "height": 75},
    "big": {"name": "Big", "width": 125, "height": 125},
    "huge": {"name": "Huge", "width": 200, "height": 200},
}

# UI Colors (matching main game style)
DARK_BG = (15, 12, 10)
DARK_PANEL = (25, 22, 18)
DARK_BORDER = (60, 50, 40)
GOLD_ACCENT = (180, 150, 80)
GOLD_BRIGHT = (220, 190, 100)
BONE_WHITE = (200, 195, 180)
SHADOW_BLACK = (5, 5, 5, 200)

# Greek-style fonts to try
GREEK_FONTS = [
    "Cinzel",
    "Trajan Pro",
    "Palatino Linotype",
    "Book Antiqua",
    "Garamond",
    "Times New Roman",
    "Georgia",
]


class PlayerSetup:
    """Stores setup information for a single player."""

    def __init__(self, player_num, color_key="red"):
        self.player_num = player_num
        self.color_key = color_key
        self.name = f"Player {player_num + 1}"

    def get_color_data(self):
        """Returns the color data dictionary for this player's color."""
        return PLAYER_COLORS.get(self.color_key, PLAYER_COLORS["red"])

    def get_rgb(self):
        """Returns the RGB tuple for this player's color."""
        return self.get_color_data()["rgb"]

    def get_light_color(self):
        """Returns the light version of this player's color."""
        return self.get_color_data()["light"]

    def get_dark_color(self):
        """Returns the dark version of this player's color."""
        return self.get_color_data()["dark"]


class GameSettings:
    """Stores all game setup settings."""

    def __init__(self):
        self.num_players = 2
        self.players = [PlayerSetup(0, "red"), PlayerSetup(1, "blue")]
        self.map_size_key = "big"

    def set_num_players(self, count):
        """Sets the number of players and initializes their setups."""
        self.num_players = max(2, min(4, count))

        # Default color assignments
        default_colors = ["red", "blue", "green", "purple"]

        # Preserve existing player setups where possible
        new_players = []
        for i in range(self.num_players):
            if i < len(self.players):
                # Keep existing player setup
                new_players.append(self.players[i])
            else:
                # Create new player with default color
                new_players.append(PlayerSetup(i, default_colors[i]))

        self.players = new_players
        self._ensure_unique_colors()

    def _ensure_unique_colors(self):
        """Ensures all players have unique colors."""
        used_colors = set()
        available_colors = list(PLAYER_COLORS.keys())

        for player in self.players:
            if player.color_key in used_colors:
                # Find an unused color
                for color in available_colors:
                    if color not in used_colors:
                        player.color_key = color
                        break
            used_colors.add(player.color_key)

    def set_player_color(self, player_index, color_key):
        """Sets a player's color, swapping if necessary."""
        if player_index >= len(self.players):
            return

        if color_key not in PLAYER_COLORS:
            return

        # Check if another player has this color
        for i, player in enumerate(self.players):
            if i != player_index and player.color_key == color_key:
                # Swap colors
                player.color_key = self.players[player_index].color_key
                break

        self.players[player_index].color_key = color_key

    def set_player_name(self, player_index, name):
        """Sets a player's display name."""
        if player_index < len(self.players):
            self.players[player_index].name = name[:20]  # Limit name length

    def get_map_dimensions(self):
        """Returns (width, height) tuple for the selected map size."""
        size_data = MAP_SIZES.get(self.map_size_key, MAP_SIZES["big"])
        return (size_data["width"], size_data["height"])


class MainMenu:
    """Handles the main menu UI for game setup."""

    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height

        # Menu state
        self.is_open = False
        self.is_in_new_game_setup = False
        self.game_settings = GameSettings()

        # Text input state
        self.active_input_player = None  # Which player's name is being edited
        self.input_text = ""

        # LAN Server state
        self.lan_server_running = False
        self.lan_server_process = None
        self.lan_server_thread = None
        self.local_ip = self._get_local_ip()
        self.lan_server_button_rect = None
        
        # Audio state
        self.music_enabled = True
        self.music_button_rect = None

        # Initialize fonts
        if not pygame.font.get_init():
            pygame.font.init()

        greek_font = self._find_greek_font()

        try:
            self.title_font = pygame.font.SysFont(greek_font, 48, bold=True)
            self.heading_font = pygame.font.SysFont(greek_font, 28, bold=True)
            self.font = pygame.font.SysFont(greek_font, 22)
            self.small_font = pygame.font.SysFont(greek_font, 18)
        except pygame.error:
            self.title_font = pygame.font.Font(None, 52)
            self.heading_font = pygame.font.Font(None, 32)
            self.font = pygame.font.Font(None, 26)
            self.small_font = pygame.font.Font(None, 20)

        # UI dimensions
        self.corner_radius = 8
        self.panel_padding = 20

        # Menu button (top right corner) - moved left to make room for timers
        self.menu_button_rect = pygame.Rect(screen_width - 55, 10, 40, 40)

        # Timer display area (to the left of menu button)
        self.timer_rect = pygame.Rect(screen_width - 170, 10, 110, 40)

        # Main menu panel (centered)
        self.menu_width = 500
        self.menu_height = 550
        self.menu_rect = pygame.Rect(
            (screen_width - self.menu_width) // 2,
            (screen_height - self.menu_height) // 2,
            self.menu_width,
            self.menu_height,
        )

        # Button rects (will be set up in draw methods)
        self.new_game_button_rect = None
        self.resume_button_rect = None
        self.start_game_button_rect = None
        self.back_button_rect = None

        # Player count buttons
        self.player_count_buttons = []

        # Map size buttons
        self.map_size_buttons = []

        # Color selection buttons (per player)
        self.color_buttons = {}  # {player_index: {color_key: rect}}

        # Name input rects
        self.name_input_rects = {}  # {player_index: rect}

    def _get_local_ip(self):
        """Gets the local IP address for LAN play."""
        try:
            # Create a socket to determine local IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"

    def toggle_lan_server(self):
        """Toggles the LAN relay server on/off."""
        if self.lan_server_running:
            self._stop_lan_server()
        else:
            self._start_lan_server()

    def _start_lan_server(self):
        """Starts the LAN relay server in a background process."""
        try:
            # Start relay_server.py as a subprocess
            import os

            script_dir = os.path.dirname(os.path.abspath(__file__))
            relay_path = os.path.join(script_dir, "relay_server.py")

            if not os.path.exists(relay_path):
                print("relay_server.py not found!")
                return

            # Start the server process
            # Use CREATE_NO_WINDOW on Windows to hide console
            kwargs = {
                "stdout": subprocess.PIPE,
                "stderr": subprocess.PIPE,
            }
            if sys.platform == "win32":
                kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW

            self.lan_server_process = subprocess.Popen(
                [sys.executable, relay_path],
                **kwargs,
            )

            self.lan_server_running = True
            print(f"LAN Server started on ws://{self.local_ip}:8765")

        except Exception as e:
            print(f"Failed to start LAN server: {e}")
            self.lan_server_running = False

    def _stop_lan_server(self):
        """Stops the LAN relay server."""
        if self.lan_server_process:
            try:
                self.lan_server_process.terminate()
                self.lan_server_process.wait(timeout=2)
            except Exception as e:
                print(f"Error stopping server: {e}")
                try:
                    self.lan_server_process.kill()
                except:
                    pass
            self.lan_server_process = None

        self.lan_server_running = False
        print("LAN Server stopped")

    def cleanup(self):
        """Cleanup method to stop server when game closes."""
        self._stop_lan_server()

    def _update_rects(self):
        """Updates all rect positions after a resize."""
        # Menu button (top right corner)
        self.menu_button_rect = pygame.Rect(self.screen_width - 55, 10, 40, 40)

        # Timer display area (to the left of menu button)
        self.timer_rect = pygame.Rect(self.screen_width - 170, 10, 110, 40)

        # Main menu panel (centered)
        self.menu_rect = pygame.Rect(
            (self.screen_width - self.menu_width) // 2,
            (self.screen_height - self.menu_height) // 2,
            self.menu_width,
            self.menu_height,
        )

    def _find_greek_font(self):
        """Finds the best available Greek-style font on the system."""
        available_fonts = pygame.font.get_fonts()

        for font_name in GREEK_FONTS:
            if font_name.lower().replace(" ", "") in available_fonts:
                return font_name
            clean_name = font_name.lower().replace(" ", "")
            for avail in available_fonts:
                if clean_name in avail.lower():
                    return font_name

        return "Georgia"

    def toggle_menu(self):
        """Toggles the main menu visibility."""
        if self.is_open:
            self.close_menu()
        else:
            self.open_menu()

    def open_menu(self):
        """Opens the main menu."""
        self.is_open = True
        self.is_in_new_game_setup = False
        self.active_input_player = None

    def close_menu(self):
        """Closes the main menu."""
        self.is_open = False
        self.is_in_new_game_setup = False
        self.active_input_player = None

    def start_new_game_setup(self):
        """Enters the new game setup screen."""
        self.is_in_new_game_setup = True
        self.game_settings = GameSettings()  # Reset settings

    def handle_event(self, event):
        """
        Handles pygame events for the menu.

        Returns:
            str or None: "new_game" if starting a new game, "resume" if resuming, None otherwise
        """
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            return self._handle_click(event.pos)

        if event.type == pygame.KEYDOWN:
            return self._handle_keydown(event)

        return None

    def _handle_click(self, pos):
        """Handles mouse clicks."""
        # Menu toggle button
        if self.menu_button_rect.collidepoint(pos):
            self.toggle_menu()
            return None

        if not self.is_open:
            return None

        # Click outside menu closes it (unless in setup)
        if not self.menu_rect.collidepoint(pos):
            if not self.is_in_new_game_setup:
                self.close_menu()
            return None

        if self.is_in_new_game_setup:
            return self._handle_setup_click(pos)
        else:
            return self._handle_main_menu_click(pos)

    def _handle_main_menu_click(self, pos):
        """Handles clicks in the main menu view."""
        if self.new_game_button_rect and self.new_game_button_rect.collidepoint(pos):
            self.start_new_game_setup()
            return None

        if self.resume_button_rect and self.resume_button_rect.collidepoint(pos):
            self.close_menu()
            return "resume"

        # LAN Server toggle
        if self.lan_server_button_rect and self.lan_server_button_rect.collidepoint(
            pos
        ):
            self.toggle_lan_server()
            return None
            
        # Music toggle
        if self.music_button_rect and self.music_button_rect.collidepoint(pos):
            self.music_enabled = not self.music_enabled
            return "toggle_music"

        return None

    def _handle_setup_click(self, pos):
        """Handles clicks in the new game setup view."""
        # Back button
        if self.back_button_rect and self.back_button_rect.collidepoint(pos):
            self.is_in_new_game_setup = False
            return None

        # Start game button
        if self.start_game_button_rect and self.start_game_button_rect.collidepoint(
            pos
        ):
            self.close_menu()
            return "new_game"

        # Player count buttons
        for i, rect in enumerate(self.player_count_buttons):
            if rect.collidepoint(pos):
                self.game_settings.set_num_players(i + 2)  # 2, 3, or 4 players
                self.active_input_player = None
                return None

        # Map size buttons
        size_keys = list(MAP_SIZES.keys())
        for i, rect in enumerate(self.map_size_buttons):
            if rect.collidepoint(pos):
                self.game_settings.map_size_key = size_keys[i]
                return None

        # Color buttons
        for player_idx, color_rects in self.color_buttons.items():
            for color_key, rect in color_rects.items():
                if rect.collidepoint(pos):
                    self.game_settings.set_player_color(player_idx, color_key)
                    return None

        # Name input rects
        for player_idx, rect in self.name_input_rects.items():
            if rect.collidepoint(pos):
                self.active_input_player = player_idx
                self.input_text = self.game_settings.players[player_idx].name
                return None

        # Click elsewhere deactivates input
        self.active_input_player = None
        return None

    def _handle_keydown(self, event):
        """Handles keyboard input."""
        if not self.is_open:
            return None

        # ESC closes menu or goes back
        if event.key == pygame.K_ESCAPE:
            if self.is_in_new_game_setup:
                if self.active_input_player is not None:
                    self.active_input_player = None
                else:
                    self.is_in_new_game_setup = False
            else:
                self.close_menu()
            return None

        # Handle text input for player names
        if self.active_input_player is not None:
            if event.key == pygame.K_RETURN:
                # Confirm name
                self.game_settings.set_player_name(
                    self.active_input_player, self.input_text
                )
                self.active_input_player = None
            elif event.key == pygame.K_BACKSPACE:
                self.input_text = self.input_text[:-1]
            elif event.unicode and len(self.input_text) < 20:
                # Only allow printable characters
                if event.unicode.isprintable():
                    self.input_text += event.unicode
            return None

        return None

    def draw(self, surface, game_in_progress=False, turn_time=0, total_time=0):
        """Draws the menu elements. Call once per frame."""
        if self.is_open:
            # Draw semi-transparent overlay
            overlay = pygame.Surface(
                (self.screen_width, self.screen_height), pygame.SRCALPHA
            )
            overlay.fill((0, 0, 0, 180))
            surface.blit(overlay, (0, 0))

            if self.is_in_new_game_setup:
                self._draw_setup_screen(surface)
            else:
                self._draw_main_menu(surface, game_in_progress)

        # Always draw timers and button last (on top)
        self._draw_timers(surface, turn_time, total_time)
        self._draw_menu_button(surface)

    def _draw_timers(self, surface, turn_time, total_time):
        """Draws the turn timer and total game timer."""
        # Draw timer background panel with shadow
        shadow_rect = self.timer_rect.copy()
        shadow_rect.x += 2
        shadow_rect.y += 2
        pygame.draw.rect(
            surface, (0, 0, 0, 100), shadow_rect, border_radius=self.corner_radius
        )

        pygame.draw.rect(
            surface, DARK_PANEL, self.timer_rect, border_radius=self.corner_radius
        )
        pygame.draw.rect(
            surface, DARK_BORDER, self.timer_rect, 1, border_radius=self.corner_radius
        )

        x = self.timer_rect.x + 8
        y = self.timer_rect.y + 4

        # Format times
        turn_mins = int(turn_time) // 60
        turn_secs = int(turn_time) % 60
        total_mins = int(total_time) // 60
        total_secs = int(total_time) % 60

        # Turn time (top)
        turn_text = f"Turn: {turn_mins}:{turn_secs:02d}"
        turn_surf = self.small_font.render(turn_text, True, GOLD_ACCENT)
        surface.blit(turn_surf, (x, y))

        # Total time (bottom)
        y += 18
        total_text = f"Game: {total_mins}:{total_secs:02d}"
        total_surf = self.small_font.render(total_text, True, BONE_WHITE)
        surface.blit(total_surf, (x, y))

    def _draw_menu_button(self, surface):
        """Draws the menu toggle button (hamburger icon)."""
        mouse_pos = pygame.mouse.get_pos()
        hover = self.menu_button_rect.collidepoint(mouse_pos)

        # Draw shadow
        shadow_rect = self.menu_button_rect.copy()
        shadow_rect.x += 2
        shadow_rect.y += 2
        pygame.draw.rect(
            surface, (0, 0, 0, 100), shadow_rect, border_radius=self.corner_radius
        )

        bg_color = (45, 40, 35) if hover else DARK_PANEL
        border_color = GOLD_BRIGHT if hover else GOLD_ACCENT

        pygame.draw.rect(
            surface, bg_color, self.menu_button_rect, border_radius=self.corner_radius
        )
        pygame.draw.rect(
            surface,
            border_color,
            self.menu_button_rect,
            2,
            border_radius=self.corner_radius,
        )

        # Draw hamburger lines
        line_color = GOLD_BRIGHT if hover else BONE_WHITE
        cx = self.menu_button_rect.centerx
        cy = self.menu_button_rect.centery
        line_width = 20
        line_height = 2
        gap = 7

        for i in range(-1, 2):
            y = cy + i * gap
            pygame.draw.rect(
                surface,
                line_color,
                (cx - line_width // 2, y - line_height // 2, line_width, line_height),
            )

    def _draw_ornate_panel(
        self, surface, rect, border_color=DARK_BORDER, bg_color=DARK_PANEL
    ):
        """Draws an ornate panel with rounded corners."""
        # Shadow
        shadow_rect = rect.copy()
        shadow_rect.x += 6
        shadow_rect.y += 6
        shadow_surf = pygame.Surface(shadow_rect.size, pygame.SRCALPHA)
        pygame.draw.rect(
            shadow_surf,
            SHADOW_BLACK,
            shadow_surf.get_rect(),
            border_radius=self.corner_radius,
        )
        surface.blit(shadow_surf, shadow_rect.topleft)

        # Main panel
        pygame.draw.rect(surface, bg_color, rect, border_radius=self.corner_radius)

        # Borders
        pygame.draw.rect(surface, DARK_BG, rect, 4, border_radius=self.corner_radius)
        pygame.draw.rect(
            surface, border_color, rect, 2, border_radius=self.corner_radius
        )
        pygame.draw.rect(
            surface, GOLD_ACCENT, rect, 1, border_radius=self.corner_radius
        )

    def _draw_button(self, surface, rect, text, font, enabled=True, selected=False):
        """Draws a styled button."""
        mouse_pos = pygame.mouse.get_pos()
        hover = rect.collidepoint(mouse_pos) and enabled

        if selected:
            bg_color = (50, 45, 35)
            border_color = GOLD_BRIGHT
        elif hover:
            bg_color = (40, 36, 30)
            border_color = GOLD_BRIGHT
        elif enabled:
            bg_color = DARK_PANEL
            border_color = GOLD_ACCENT
        else:
            bg_color = (20, 18, 15)
            border_color = (50, 45, 40)

        text_color = BONE_WHITE if enabled else (80, 75, 70)

        pygame.draw.rect(surface, bg_color, rect, border_radius=self.corner_radius - 2)
        pygame.draw.rect(
            surface, border_color, rect, 2, border_radius=self.corner_radius - 2
        )

        text_surf = font.render(text, True, text_color)
        text_rect = text_surf.get_rect(center=rect.center)
        surface.blit(text_surf, text_rect)

    def _draw_color_button(
        self, surface, rect, color_key, selected=False, enabled=True
    ):
        """Draws a color selection button."""
        color_data = PLAYER_COLORS[color_key]
        rgb = color_data["rgb"]

        mouse_pos = pygame.mouse.get_pos()
        hover = rect.collidepoint(mouse_pos) and enabled

        if not enabled:
            # Grayed out
            rgb = (60, 55, 50)

        pygame.draw.rect(surface, rgb, rect, border_radius=4)

        if selected:
            pygame.draw.rect(surface, GOLD_BRIGHT, rect, 3, border_radius=4)
        elif hover and enabled:
            pygame.draw.rect(surface, BONE_WHITE, rect, 2, border_radius=4)
        else:
            pygame.draw.rect(surface, DARK_BG, rect, 1, border_radius=4)

    def _draw_main_menu(self, surface, game_in_progress):
        """Draws the main menu view."""
        self._draw_ornate_panel(surface, self.menu_rect)

        x = self.menu_rect.x + self.panel_padding
        y = self.menu_rect.y + self.panel_padding

        # Title
        title_surf = self.title_font.render("REPUBLIC", True, GOLD_BRIGHT)
        title_rect = title_surf.get_rect(centerx=self.menu_rect.centerx, top=y)
        surface.blit(title_surf, title_rect)

        y += 80

        # Subtitle
        subtitle_surf = self.small_font.render(
            "A Turn-Based Strategy Game", True, BONE_WHITE
        )
        subtitle_rect = subtitle_surf.get_rect(centerx=self.menu_rect.centerx, top=y)
        surface.blit(subtitle_surf, subtitle_rect)

        y += 60

        # Buttons
        button_width = 200
        button_height = 50
        button_x = self.menu_rect.centerx - button_width // 2

        # New Game button
        self.new_game_button_rect = pygame.Rect(
            button_x, y, button_width, button_height
        )
        self._draw_button(surface, self.new_game_button_rect, "New Game", self.font)

        y += button_height + 20

        # Resume button (only if game in progress)
        if game_in_progress:
            self.resume_button_rect = pygame.Rect(
                button_x, y, button_width, button_height
            )
            self._draw_button(
                surface, self.resume_button_rect, "Resume Game", self.font
            )
            y += button_height + 20
        else:
            self.resume_button_rect = None

        # LAN Server toggle button
        lan_button_width = 220
        lan_button_x = self.menu_rect.centerx - lan_button_width // 2
        self.lan_server_button_rect = pygame.Rect(lan_button_x, y, lan_button_width, 40)

        # Draw LAN server button with status
        mouse_pos = pygame.mouse.get_pos()
        hover = self.lan_server_button_rect.collidepoint(mouse_pos)

        if self.lan_server_running:
            btn_text = "LAN Server: ON"
            bg_color = (30, 80, 30)  # Green tint
            border_color = (100, 200, 100) if hover else (80, 160, 80)
        else:
            btn_text = "LAN Server: OFF"
            bg_color = DARK_PANEL
            border_color = GOLD_BRIGHT if hover else GOLD_ACCENT

        pygame.draw.rect(
            surface, bg_color, self.lan_server_button_rect, border_radius=6
        )
        pygame.draw.rect(
            surface, border_color, self.lan_server_button_rect, 2, border_radius=6
        )

        btn_surf = self.small_font.render(btn_text, True, BONE_WHITE)
        btn_rect = btn_surf.get_rect(center=self.lan_server_button_rect.center)
        surface.blit(btn_surf, btn_rect)

        y += 45

        # Show IP address when server is running
        if self.lan_server_running:
            ip_text = f"ws://{self.local_ip}:8765"
            ip_surf = self.small_font.render(ip_text, True, (100, 200, 100))
            ip_rect = ip_surf.get_rect(centerx=self.menu_rect.centerx, top=y)
            surface.blit(ip_surf, ip_rect)
            y += 25
            
        y += 10
            
        # Music Toggle Button
        music_button_width = 150
        music_button_x = self.menu_rect.centerx - music_button_width // 2
        self.music_button_rect = pygame.Rect(music_button_x, y, music_button_width, 35)
        
        music_text = "Music: ON" if self.music_enabled else "Music: OFF"
        # Draw music button
        mouse_pos = pygame.mouse.get_pos()
        hover = self.music_button_rect.collidepoint(mouse_pos)
        
        bg_col = DARK_PANEL
        border_col = GOLD_BRIGHT if hover else (120, 110, 100)
        text_col = BONE_WHITE if self.music_enabled else (100, 100, 100)
        
        pygame.draw.rect(surface, bg_col, self.music_button_rect, border_radius=6)
        pygame.draw.rect(surface, border_col, self.music_button_rect, 2, border_radius=6)
        
        m_surf = self.small_font.render(music_text, True, text_col)
        m_rect = m_surf.get_rect(center=self.music_button_rect.center)
        surface.blit(m_surf, m_rect)
        
        y += 50

        # Instructions at bottom
        y = self.menu_rect.bottom - 70

        # Brief description
        desc_lines = [
            "Catch chickens (grass) & gold (granite) for money!",
            "Black chicken/shiny gold = 3g. SHIFT+click to upgrade buildings.",
        ]
        for line in desc_lines:
            desc_surf = self.small_font.render(line, True, (140, 135, 125))
            desc_rect = desc_surf.get_rect(centerx=self.menu_rect.centerx, top=y)
            surface.blit(desc_surf, desc_rect)
            y += 20

        y += 5
        hint_surf = self.small_font.render(
            "Press ESC or click outside to close", True, (100, 95, 90)
        )
        hint_rect = hint_surf.get_rect(centerx=self.menu_rect.centerx, top=y)
        surface.blit(hint_surf, hint_rect)

    def _draw_setup_screen(self, surface):
        """Draws the new game setup screen."""
        self._draw_ornate_panel(surface, self.menu_rect)

        x = self.menu_rect.x + self.panel_padding
        y = self.menu_rect.y + self.panel_padding

        # Title
        title_surf = self.heading_font.render("New Game Setup", True, GOLD_BRIGHT)
        title_rect = title_surf.get_rect(centerx=self.menu_rect.centerx, top=y)
        surface.blit(title_surf, title_rect)

        y += 50

        # Number of players
        label_surf = self.font.render("Players:", True, BONE_WHITE)
        surface.blit(label_surf, (x, y))

        self.player_count_buttons = []
        btn_x = x + 100
        btn_size = 40
        for i in range(3):  # 2, 3, 4 players
            rect = pygame.Rect(btn_x + i * (btn_size + 10), y - 5, btn_size, 35)
            self.player_count_buttons.append(rect)
            selected = self.game_settings.num_players == i + 2
            self._draw_button(
                surface, rect, str(i + 2), self.small_font, selected=selected
            )

        y += 45

        # Map size
        label_surf = self.font.render("Map Size:", True, BONE_WHITE)
        surface.blit(label_surf, (x, y))

        self.map_size_buttons = []
        btn_x = x + 100
        btn_width = 80
        for i, (key, data) in enumerate(MAP_SIZES.items()):
            rect = pygame.Rect(btn_x + i * (btn_width + 5), y - 5, btn_width, 35)
            self.map_size_buttons.append(rect)
            selected = self.game_settings.map_size_key == key
            self._draw_button(
                surface, rect, data["name"], self.small_font, selected=selected
            )

        y += 55

        # Separator
        pygame.draw.line(
            surface,
            GOLD_ACCENT,
            (x, y),
            (self.menu_rect.right - self.panel_padding, y),
            1,
        )
        y += 15

        # Player setup section
        self.color_buttons = {}
        self.name_input_rects = {}

        used_colors = {p.color_key for p in self.game_settings.players}

        for i, player in enumerate(self.game_settings.players):
            # Player label
            player_label = self.font.render(
                f"Player {i + 1}:", True, player.get_light_color()
            )
            surface.blit(player_label, (x, y))

            # Name input
            name_rect = pygame.Rect(x + 90, y - 2, 150, 28)
            self.name_input_rects[i] = name_rect

            # Draw name input box
            if self.active_input_player == i:
                pygame.draw.rect(surface, (40, 36, 30), name_rect, border_radius=4)
                pygame.draw.rect(surface, GOLD_BRIGHT, name_rect, 2, border_radius=4)
                display_text = self.input_text + "|"
            else:
                pygame.draw.rect(surface, DARK_PANEL, name_rect, border_radius=4)
                pygame.draw.rect(surface, DARK_BORDER, name_rect, 1, border_radius=4)
                display_text = player.name

            name_surf = self.small_font.render(display_text, True, BONE_WHITE)
            name_text_rect = name_surf.get_rect(
                midleft=(name_rect.x + 8, name_rect.centery)
            )
            # Clip to rect
            surface.set_clip(name_rect)
            surface.blit(name_surf, name_text_rect)
            surface.set_clip(None)

            # Color buttons
            color_x = x + 260
            self.color_buttons[i] = {}
            color_btn_size = 25

            for j, color_key in enumerate(PLAYER_COLORS.keys()):
                rect = pygame.Rect(
                    color_x + j * (color_btn_size + 5),
                    y,
                    color_btn_size,
                    color_btn_size,
                )
                self.color_buttons[i][color_key] = rect

                selected = player.color_key == color_key
                # Color is available if it's selected or not used by others
                enabled = (
                    selected
                    or color_key not in used_colors
                    or color_key == player.color_key
                )
                self._draw_color_button(surface, rect, color_key, selected, enabled)

            y += 40

        y += 20

        # Bottom buttons
        button_width = 120
        button_height = 45
        button_y = self.menu_rect.bottom - self.panel_padding - button_height

        # Back button
        self.back_button_rect = pygame.Rect(
            self.menu_rect.x + self.panel_padding, button_y, button_width, button_height
        )
        self._draw_button(surface, self.back_button_rect, "Back", self.font)

        # Start Game button
        self.start_game_button_rect = pygame.Rect(
            self.menu_rect.right - self.panel_padding - button_width,
            button_y,
            button_width,
            button_height,
        )
        self._draw_button(surface, self.start_game_button_rect, "Start Game", self.font)

    def get_game_settings(self):
        """Returns the current game settings."""
        return self.game_settings
