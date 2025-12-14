import pygame

# Dark Souls inspired color palette
DARK_BG = (15, 12, 10)  # Near black with warm tint
DARK_PANEL = (25, 22, 18)  # Slightly lighter panel
DARK_BORDER = (60, 50, 40)  # Bronze-ish border
GOLD_ACCENT = (180, 150, 80)  # Gold for accents
GOLD_BRIGHT = (220, 190, 100)  # Brighter gold for highlights
BLOOD_RED = (120, 20, 20)  # Dark blood red
EMBER_ORANGE = (200, 100, 40)  # Ember glow
BONE_WHITE = (200, 195, 180)  # Off-white for text
SHADOW_BLACK = (5, 5, 5, 200)  # Semi-transparent shadow

# Team colors
RED_TEAM_COLOR = (180, 50, 50)
RED_TEAM_LIGHT = (220, 80, 80)
RED_TEAM_DARK = (100, 30, 30)
BLUE_TEAM_COLOR = (50, 100, 180)
BLUE_TEAM_LIGHT = (80, 130, 220)
BLUE_TEAM_DARK = (30, 60, 100)

# Health bar colors
HEALTH_BG = (40, 35, 30)
HEALTH_BORDER = (80, 70, 55)
HEALTH_RED = (160, 40, 40)
HEALTH_RED_BRIGHT = (200, 60, 60)
HEALTH_BLUE = (40, 80, 160)
HEALTH_BLUE_BRIGHT = (60, 100, 200)

# Money colors
MONEY_GOLD = (255, 215, 0)
MONEY_DARK = (180, 140, 20)


class UIManager:
    """Manages the drawing and interaction of all UI elements with Dark Souls aesthetic."""

    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height

        # Ensure the font module is initialized
        if not pygame.font.get_init():
            pygame.font.init()

        # Load fonts - trying to get a gothic/medieval feel
        try:
            self.title_font = pygame.font.SysFont("Georgia", 32, bold=True)
            self.font = pygame.font.SysFont("Georgia", 22)
            self.small_font = pygame.font.SysFont("Georgia", 16)
            self.tiny_font = pygame.font.SysFont("Georgia", 14)
        except pygame.error:
            self.title_font = pygame.font.Font(None, 36)
            self.font = pygame.font.Font(None, 26)
            self.small_font = pygame.font.Font(None, 20)
            self.tiny_font = pygame.font.Font(None, 16)

        # Large font for game over
        try:
            self.rip_font = pygame.font.SysFont("Georgia", 100, bold=True)
            self.rip_subtitle_font = pygame.font.SysFont("Georgia", 32)
        except pygame.error:
            self.rip_font = pygame.font.Font(None, 100)
            self.rip_subtitle_font = pygame.font.Font(None, 36)

        # UI Element positions and sizes
        self.panel_padding = 10
        self.panel_margin = 15

        # Top left info panel
        self.info_panel_rect = pygame.Rect(
            self.panel_margin, self.panel_margin, 200, 140
        )

        # End Turn button (top right)
        self.end_turn_button_rect = pygame.Rect(
            screen_width - 145, self.panel_margin, 130, 45
        )

        # Creation menu button (below end turn)
        self.creation_menu_button_rect = pygame.Rect(
            screen_width - 145, self.panel_margin + 55, 130, 35
        )

        # Creation menu panel (appears when toggled)
        self.creation_menu_rect = pygame.Rect(
            screen_width - 250, self.panel_margin + 100, 235, 80
        )

        # Character creation menu (appears when clicking capital)
        self.char_menu_width = 280
        self.char_menu_height = 220
        self.char_menu_rect = pygame.Rect(
            (screen_width - self.char_menu_width) // 2,
            (screen_height - self.char_menu_height) // 2,
            self.char_menu_width,
            self.char_menu_height,
        )

        # Character type buttons within the menu
        self.char_buttons = []
        self._setup_char_buttons()

        # Bottom instruction bar
        self.instructions_height = 35
        self.instructions_rect = pygame.Rect(
            0,
            screen_height - self.instructions_height,
            screen_width,
            self.instructions_height,
        )

    def _setup_char_buttons(self):
        """Sets up the character creation buttons."""
        button_height = 35
        button_margin = 5
        start_y = self.char_menu_rect.y + 45

        char_types = [
            ("warrior", "Warrior", 2, "10 HP, 5 DMG, 3 MOV"),
            ("swordsman", "Swordsman", 5, "15 HP, 10 DMG, 3 MOV"),
            ("shieldman", "Shieldman", 3, "20 HP, 2 DMG, 2 MOV"),
            ("runner", "Runner", 5, "5 HP, 5 DMG, 10 MOV"),
        ]

        self.char_buttons = []
        for i, (char_type, display_name, cost, stats) in enumerate(char_types):
            button_rect = pygame.Rect(
                self.char_menu_rect.x + 10,
                start_y + i * (button_height + button_margin),
                self.char_menu_width - 20,
                button_height,
            )
            self.char_buttons.append(
                {
                    "rect": button_rect,
                    "type": char_type,
                    "name": display_name,
                    "cost": cost,
                    "stats": stats,
                }
            )

    def draw(self, surface, game_state, red_team, blue_team):
        """Draws all UI elements onto the given surface."""
        # Get current team
        current_team = red_team if game_state.is_red_turn() else blue_team

        # Draw main info panel
        self._draw_info_panel(surface, game_state, red_team, blue_team)

        # Draw End Turn button
        if not game_state.game_over:
            self._draw_end_turn_button(surface, game_state, current_team)

            # Draw Creation Menu button
            self._draw_creation_menu_button(surface, game_state, current_team)

            # Draw creation menu if open
            if game_state.show_creation_menu:
                self._draw_creation_menu(surface, current_team)

            # Draw character menu if open
            if game_state.show_character_menu and game_state.selected_capital:
                self._draw_character_menu(surface, game_state, current_team)

        # Draw bottom instruction bar
        self._draw_instructions(surface, game_state)

        # Draw game over overlay if applicable
        if game_state.game_over:
            self._draw_game_over(surface, game_state)

    def _draw_ornate_panel(
        self, surface, rect, border_color=DARK_BORDER, bg_color=DARK_PANEL
    ):
        """Draws an ornate Dark Souls-style panel with decorative corners."""
        # Draw shadow
        shadow_rect = rect.copy()
        shadow_rect.x += 4
        shadow_rect.y += 4
        shadow_surf = pygame.Surface(shadow_rect.size, pygame.SRCALPHA)
        shadow_surf.fill(SHADOW_BLACK)
        surface.blit(shadow_surf, shadow_rect.topleft)

        # Draw main panel background
        pygame.draw.rect(surface, bg_color, rect)

        # Draw border with multiple layers for depth
        pygame.draw.rect(surface, DARK_BG, rect, 3)
        pygame.draw.rect(surface, border_color, rect, 2)
        pygame.draw.rect(surface, GOLD_ACCENT, rect, 1)

        # Draw corner accents
        corner_size = 8
        corners = [
            (rect.left, rect.top),
            (rect.right - corner_size, rect.top),
            (rect.left, rect.bottom - corner_size),
            (rect.right - corner_size, rect.bottom - corner_size),
        ]

        for cx, cy in corners:
            pygame.draw.rect(
                surface, GOLD_BRIGHT, (cx, cy, corner_size, corner_size), 1
            )

    def _draw_ornate_button(
        self,
        surface,
        rect,
        text,
        font,
        text_color=BONE_WHITE,
        bg_color=DARK_PANEL,
        border_color=GOLD_ACCENT,
        hover=False,
    ):
        """Draws a Dark Souls-style button."""
        # Adjust colors for hover state
        if hover:
            bg_color = tuple(min(255, c + 20) for c in bg_color)
            border_color = GOLD_BRIGHT

        # Draw shadow
        shadow_rect = rect.copy()
        shadow_rect.x += 2
        shadow_rect.y += 2
        shadow_surf = pygame.Surface(shadow_rect.size, pygame.SRCALPHA)
        shadow_surf.fill((0, 0, 0, 150))
        surface.blit(shadow_surf, shadow_rect.topleft)

        # Draw button background
        pygame.draw.rect(surface, bg_color, rect)

        # Draw border
        pygame.draw.rect(surface, DARK_BG, rect, 2)
        pygame.draw.rect(surface, border_color, rect, 1)

        # Draw text
        text_surf = font.render(text, True, text_color)
        text_rect = text_surf.get_rect(center=rect.center)
        surface.blit(text_surf, text_rect)

    def _draw_health_bar(
        self,
        surface,
        x,
        y,
        width,
        height,
        current,
        maximum,
        fill_color,
        bright_color,
        label="",
    ):
        """Draws a stylized health bar."""
        # Background
        bg_rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect(surface, HEALTH_BG, bg_rect)

        # Health fill
        if maximum > 0:
            health_ratio = current / maximum
            fill_width = int(width * health_ratio)
            if fill_width > 0:
                fill_rect = pygame.Rect(x, y, fill_width, height)
                pygame.draw.rect(surface, fill_color, fill_rect)

                # Gradient highlight on top half
                highlight_rect = pygame.Rect(x, y, fill_width, height // 2)
                highlight_surf = pygame.Surface(highlight_rect.size, pygame.SRCALPHA)
                highlight_surf.fill((*bright_color, 80))
                surface.blit(highlight_surf, highlight_rect.topleft)

        # Border
        pygame.draw.rect(surface, HEALTH_BORDER, bg_rect, 1)

        # Text
        if label:
            text_surf = self.tiny_font.render(label, True, BONE_WHITE)
            text_rect = text_surf.get_rect(midleft=(x + 5, y + height // 2))
            surface.blit(text_surf, text_rect)

        # Health numbers
        hp_text = f"{current}/{maximum}"
        hp_surf = self.tiny_font.render(hp_text, True, BONE_WHITE)
        hp_rect = hp_surf.get_rect(midright=(x + width - 5, y + height // 2))
        surface.blit(hp_surf, hp_rect)

    def _draw_money_display(self, surface, x, y, amount, team_color):
        """Draws a money counter with a coin icon."""
        # Draw coin icon (simple circle with detail)
        coin_radius = 10
        coin_center = (x + coin_radius, y + coin_radius)

        # Outer ring
        pygame.draw.circle(surface, MONEY_DARK, coin_center, coin_radius)
        pygame.draw.circle(surface, MONEY_GOLD, coin_center, coin_radius - 2)
        pygame.draw.circle(surface, MONEY_DARK, coin_center, coin_radius - 4, 1)

        # Draw $ symbol
        dollar_surf = self.tiny_font.render("$", True, MONEY_DARK)
        dollar_rect = dollar_surf.get_rect(center=coin_center)
        surface.blit(dollar_surf, dollar_rect)

        # Draw amount
        amount_surf = self.font.render(str(amount), True, MONEY_GOLD)
        amount_rect = amount_surf.get_rect(
            midleft=(x + coin_radius * 2 + 8, y + coin_radius)
        )
        surface.blit(amount_surf, amount_rect)

    def _draw_info_panel(self, surface, game_state, red_team, blue_team):
        """Draws the main info panel with turn info and health bars."""
        # Draw ornate panel
        self._draw_ornate_panel(surface, self.info_panel_rect)

        x = self.info_panel_rect.x + self.panel_padding
        y = self.info_panel_rect.y + self.panel_padding

        # Turn counter
        turn_text = f"Turn {game_state.turn_count}"
        turn_surf = self.font.render(turn_text, True, GOLD_ACCENT)
        surface.blit(turn_surf, (x, y))

        # Current phase indicator
        y += 25
        if game_state.is_red_turn():
            phase_text = "Red Team"
            phase_color = RED_TEAM_LIGHT
        else:
            phase_text = "Blue Team"
            phase_color = BLUE_TEAM_LIGHT

        phase_surf = self.font.render(phase_text, True, phase_color)
        surface.blit(phase_surf, (x, y))

        # Separator line
        y += 28
        pygame.draw.line(
            surface,
            GOLD_ACCENT,
            (x, y),
            (self.info_panel_rect.right - self.panel_padding, y),
            1,
        )

        # Red team money
        y += 8
        self._draw_money_display(surface, x, y, red_team.money, RED_TEAM_COLOR)

        # Red team label
        red_label = self.tiny_font.render("Red", True, RED_TEAM_LIGHT)
        surface.blit(red_label, (x + 60, y - 2))

        # Blue team money
        y += 28
        self._draw_money_display(surface, x, y, blue_team.money, BLUE_TEAM_COLOR)

        # Blue team label
        blue_label = self.tiny_font.render("Blue", True, BLUE_TEAM_LIGHT)
        surface.blit(blue_label, (x + 60, y - 2))

    def _draw_end_turn_button(self, surface, game_state, current_team):
        """Draws the End Turn button."""
        # Check if mouse is hovering
        mouse_pos = pygame.mouse.get_pos()
        hover = self.end_turn_button_rect.collidepoint(mouse_pos)

        # Use team color for button
        if game_state.is_red_turn():
            bg_color = RED_TEAM_DARK
            border_color = RED_TEAM_LIGHT if hover else RED_TEAM_COLOR
        else:
            bg_color = BLUE_TEAM_DARK
            border_color = BLUE_TEAM_LIGHT if hover else BLUE_TEAM_COLOR

        self._draw_ornate_button(
            surface,
            self.end_turn_button_rect,
            "End Turn",
            self.font,
            BONE_WHITE,
            bg_color,
            border_color,
            hover,
        )

    def _draw_creation_menu_button(self, surface, game_state, current_team):
        """Draws the creation menu toggle button."""
        mouse_pos = pygame.mouse.get_pos()
        hover = self.creation_menu_button_rect.collidepoint(mouse_pos)

        text = "Create ▼" if not game_state.show_creation_menu else "Create ▲"

        self._draw_ornate_button(
            surface,
            self.creation_menu_button_rect,
            text,
            self.small_font,
            BONE_WHITE,
            DARK_PANEL,
            GOLD_BRIGHT if hover else GOLD_ACCENT,
            hover,
        )

    def _draw_creation_menu(self, surface, current_team):
        """Draws the creation menu dropdown."""
        self._draw_ornate_panel(surface, self.creation_menu_rect)

        x = self.creation_menu_rect.x + self.panel_padding
        y = self.creation_menu_rect.y + self.panel_padding

        # Title
        title_surf = self.small_font.render("Create Capital", True, GOLD_ACCENT)
        surface.blit(title_surf, (x, y))

        y += 22

        # Cost info
        from capital import Capital

        cost_text = f"Cost: {Capital.COST} gold"
        can_afford = current_team.can_afford(Capital.COST)
        cost_color = MONEY_GOLD if can_afford else (100, 100, 100)
        cost_surf = self.tiny_font.render(cost_text, True, cost_color)
        surface.blit(cost_surf, (x, y))

        y += 18

        # Instructions
        if can_afford:
            inst_text = "Click on map to place"
        else:
            inst_text = "Not enough gold!"

        inst_color = BONE_WHITE if can_afford else (150, 80, 80)
        inst_surf = self.tiny_font.render(inst_text, True, inst_color)
        surface.blit(inst_surf, (x, y))

    def _draw_character_menu(self, surface, game_state, current_team):
        """Draws the character creation menu when clicking a capital."""
        self._draw_ornate_panel(surface, self.char_menu_rect, GOLD_ACCENT, DARK_BG)

        x = self.char_menu_rect.x + self.panel_padding
        y = self.char_menu_rect.y + self.panel_padding

        # Title
        title_text = "Recruit Unit"
        title_surf = self.font.render(title_text, True, GOLD_BRIGHT)
        title_rect = title_surf.get_rect(centerx=self.char_menu_rect.centerx, top=y)
        surface.blit(title_surf, title_rect)

        # Draw character type buttons
        mouse_pos = pygame.mouse.get_pos()

        for button in self.char_buttons:
            rect = button["rect"]
            hover = rect.collidepoint(mouse_pos)
            can_afford = current_team.can_afford(button["cost"])

            # Button colors based on affordability
            if can_afford:
                bg_color = DARK_PANEL if not hover else (45, 40, 35)
                border_color = GOLD_BRIGHT if hover else GOLD_ACCENT
                text_color = BONE_WHITE
            else:
                bg_color = (30, 28, 25)
                border_color = (60, 55, 50)
                text_color = (100, 95, 90)

            # Draw button background
            pygame.draw.rect(surface, bg_color, rect)
            pygame.draw.rect(surface, border_color, rect, 1)

            # Draw button content
            name_text = f"{button['name']} (${button['cost']})"
            name_surf = self.small_font.render(name_text, True, text_color)
            name_rect = name_surf.get_rect(midleft=(rect.x + 8, rect.centery - 6))
            surface.blit(name_surf, name_rect)

            stats_surf = self.tiny_font.render(
                button["stats"], True, text_color if can_afford else (80, 75, 70)
            )
            stats_rect = stats_surf.get_rect(midleft=(rect.x + 8, rect.centery + 8))
            surface.blit(stats_surf, stats_rect)

        # Close button hint
        close_text = "Click outside to close"
        close_surf = self.tiny_font.render(close_text, True, (120, 115, 105))
        close_rect = close_surf.get_rect(
            centerx=self.char_menu_rect.centerx, bottom=self.char_menu_rect.bottom - 5
        )
        surface.blit(close_surf, close_rect)

    def _draw_instructions(self, surface, game_state):
        """Draws the bottom instruction bar."""
        # Draw dark background bar
        pygame.draw.rect(surface, DARK_BG, self.instructions_rect)
        pygame.draw.line(
            surface,
            GOLD_ACCENT,
            (0, self.instructions_rect.y),
            (self.screen_width, self.instructions_rect.y),
            1,
        )

        # Instruction text
        if game_state.game_over:
            text = "Press ESC to quit"
        elif game_state.show_character_menu:
            text = "Select a unit to recruit  |  Click outside to cancel"
        elif game_state.show_creation_menu:
            text = "Click on valid location to create capital  |  Must be 14+ tiles from other capitals"
        elif game_state.selected_character:
            text = "Click to move/attack  |  Click character again to deselect  |  WASD: Camera  |  Q/E: Zoom"
        else:
            text = "Click character to select  |  Click capital to recruit  |  WASD: Camera  |  Q/E: Zoom"

        text_surf = self.small_font.render(text, True, BONE_WHITE)
        text_rect = text_surf.get_rect(center=self.instructions_rect.center)
        surface.blit(text_surf, text_rect)

    def _draw_game_over(self, surface, game_state):
        """Draws the Dark Souls-style game over screen."""
        # Semi-transparent dark overlay
        overlay = pygame.Surface(
            (self.screen_width, self.screen_height), pygame.SRCALPHA
        )
        overlay.fill((0, 0, 0, 220))
        surface.blit(overlay, (0, 0))

        # Draw decorative border
        border_rect = pygame.Rect(
            self.screen_width // 4,
            self.screen_height // 4,
            self.screen_width // 2,
            self.screen_height // 2,
        )

        # Multiple border layers
        for i in range(3):
            offset = i * 3
            r = border_rect.inflate(offset * 2, offset * 2)
            pygame.draw.rect(surface, (*GOLD_ACCENT[:3],), r, 2)

        # Main text - "VICTORY" or "DEFEAT"
        winner_name = game_state.get_winner_name()

        if game_state.is_red_turn():
            # Current player is red
            if game_state.red_wins():
                main_text = "VICTORY"
                main_color = GOLD_BRIGHT
            else:
                main_text = "DEFEAT"
                main_color = BLOOD_RED
        else:
            # Current player is blue
            if game_state.blue_wins():
                main_text = "VICTORY"
                main_color = GOLD_BRIGHT
            else:
                main_text = "DEFEAT"
                main_color = BLOOD_RED

        main_surf = self.rip_font.render(main_text, True, main_color)
        main_rect = main_surf.get_rect(
            centerx=self.screen_width // 2, centery=self.screen_height // 2 - 30
        )

        # Draw text shadow
        shadow_surf = self.rip_font.render(main_text, True, DARK_BG)
        shadow_rect = shadow_surf.get_rect(
            centerx=main_rect.centerx + 3, centery=main_rect.centery + 3
        )
        surface.blit(shadow_surf, shadow_rect)
        surface.blit(main_surf, main_rect)

        # Subtitle
        subtitle = f"{winner_name} Team Wins!"
        if winner_name == "Red":
            sub_color = RED_TEAM_LIGHT
        else:
            sub_color = BLUE_TEAM_LIGHT

        sub_surf = self.rip_subtitle_font.render(subtitle, True, sub_color)
        sub_rect = sub_surf.get_rect(
            centerx=self.screen_width // 2, centery=self.screen_height // 2 + 50
        )
        surface.blit(sub_surf, sub_rect)

        # Hint text
        hint_surf = self.font.render("Press ESC to quit", True, BONE_WHITE)
        hint_rect = hint_surf.get_rect(
            centerx=self.screen_width // 2, centery=self.screen_height // 2 + 100
        )
        surface.blit(hint_surf, hint_rect)

    def get_char_button_at(self, pos):
        """
        Returns the character type if a character button was clicked.

        Args:
            pos: Mouse position tuple (x, y)

        Returns:
            str or None: Character type string or None if no button clicked.
        """
        for button in self.char_buttons:
            if button["rect"].collidepoint(pos):
                return button["type"]
        return None

    def is_click_in_char_menu(self, pos):
        """Checks if a click is within the character menu area."""
        return self.char_menu_rect.collidepoint(pos)

    def is_click_in_creation_menu(self, pos):
        """Checks if a click is within the creation menu area."""
        return self.creation_menu_rect.collidepoint(pos)
