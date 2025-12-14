import pygame

# Greek-style fonts to try (in order of preference)
GREEK_FONTS = [
    "Cinzel",
    "Trajan Pro",
    "Palatino Linotype",
    "Book Antiqua",
    "Garamond",
    "Times New Roman",
    "Georgia",
]

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

# Health bar colors
HEALTH_BG = (40, 35, 30)
HEALTH_BORDER = (80, 70, 55)

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

        # Load fonts - Greek/Classical style
        greek_font = self._find_greek_font()

        try:
            self.title_font = pygame.font.SysFont(greek_font, 32, bold=True)
            self.font = pygame.font.SysFont(greek_font, 22)
            self.small_font = pygame.font.SysFont(greek_font, 16)
            self.tiny_font = pygame.font.SysFont(greek_font, 14)
        except pygame.error:
            self.title_font = pygame.font.Font(None, 36)
            self.font = pygame.font.Font(None, 26)
            self.small_font = pygame.font.Font(None, 20)
            self.tiny_font = pygame.font.Font(None, 16)

        # Large font for game over
        try:
            self.rip_font = pygame.font.SysFont(greek_font, 100, bold=True)
            self.rip_subtitle_font = pygame.font.SysFont(greek_font, 32)
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

        # End Turn button (top right, moved down to avoid menu button overlap)
        self.end_turn_button_rect = pygame.Rect(
            screen_width - 145, self.panel_margin + 55, 130, 45
        )

        # Creation menu button (below end turn)
        self.creation_menu_button_rect = pygame.Rect(
            screen_width - 145, self.panel_margin + 110, 130, 35
        )

        # Creation menu panel (appears when toggled) - made taller for seer option
        self.creation_menu_rect = pygame.Rect(
            screen_width - 250, self.panel_margin + 155, 235, 130
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

        # Corner radius for rounded UI elements
        self.corner_radius = 8

        # Seer spawn button rect (initialized in draw method)
        self.seer_button_rect = pygame.Rect(0, 0, 0, 0)

        # Bottom instruction bar
        self.instructions_height = 35
        self.instructions_rect = pygame.Rect(
            0,
            screen_height - self.instructions_height,
            screen_width,
            self.instructions_height,
        )

    def _find_greek_font(self):
        """Finds the best available Greek-style font on the system."""
        available_fonts = pygame.font.get_fonts()

        for font_name in GREEK_FONTS:
            # Check both exact match and lowercase
            if font_name.lower().replace(" ", "") in available_fonts:
                return font_name
            # Also try without spaces
            clean_name = font_name.lower().replace(" ", "")
            for avail in available_fonts:
                if clean_name in avail.lower():
                    return font_name

        # Fallback to Georgia which is widely available
        return "Georgia"

    def _setup_char_buttons(self):
        """Sets up the character creation buttons."""
        button_height = 35
        button_margin = 5
        start_y = self.char_menu_rect.y + 45

        char_types = [
            ("warrior", "Warrior", 2, "10 HP, 5 DMG, 3 MOV"),
            ("swordsman", "Swordsman", 5, "15 HP, 10 DMG, 3 MOV"),
            ("shieldman", "Shieldman", 3, "20 HP, 2 DMG, 2 MOV"),
            ("runner", "Runner", 5, "5 HP, 4 DMG, 10 MOV, 9x9 VIS"),
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

    def draw(self, surface, game_state, teams):
        """Draws all UI elements onto the given surface."""
        # Get current team
        current_team = game_state.get_current_team(teams)

        # Draw main info panel
        self._draw_info_panel(surface, game_state, teams)

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
            self._draw_game_over(surface, game_state, teams)

    def _draw_ornate_panel(
        self, surface, rect, border_color=DARK_BORDER, bg_color=DARK_PANEL
    ):
        """Draws an ornate Dark Souls-style panel with rounded corners."""
        # Draw shadow
        shadow_rect = rect.copy()
        shadow_rect.x += 4
        shadow_rect.y += 4
        shadow_surf = pygame.Surface(shadow_rect.size, pygame.SRCALPHA)
        pygame.draw.rect(
            shadow_surf,
            SHADOW_BLACK,
            shadow_surf.get_rect(),
            border_radius=self.corner_radius,
        )
        surface.blit(shadow_surf, shadow_rect.topleft)

        # Draw main panel background with rounded corners
        pygame.draw.rect(surface, bg_color, rect, border_radius=self.corner_radius)

        # Draw border with multiple layers for depth (rounded)
        pygame.draw.rect(surface, DARK_BG, rect, 3, border_radius=self.corner_radius)
        pygame.draw.rect(
            surface, border_color, rect, 2, border_radius=self.corner_radius
        )
        pygame.draw.rect(
            surface, GOLD_ACCENT, rect, 1, border_radius=self.corner_radius
        )

        # Draw corner accents (small decorative marks)
        corner_size = 6
        accent_offset = 4

        # Top-left corner accent
        pygame.draw.line(
            surface,
            GOLD_BRIGHT,
            (rect.left + accent_offset, rect.top + accent_offset),
            (rect.left + accent_offset + corner_size, rect.top + accent_offset),
            2,
        )
        pygame.draw.line(
            surface,
            GOLD_BRIGHT,
            (rect.left + accent_offset, rect.top + accent_offset),
            (rect.left + accent_offset, rect.top + accent_offset + corner_size),
            2,
        )

        # Top-right corner accent
        pygame.draw.line(
            surface,
            GOLD_BRIGHT,
            (rect.right - accent_offset, rect.top + accent_offset),
            (rect.right - accent_offset - corner_size, rect.top + accent_offset),
            2,
        )
        pygame.draw.line(
            surface,
            GOLD_BRIGHT,
            (rect.right - accent_offset, rect.top + accent_offset),
            (rect.right - accent_offset, rect.top + accent_offset + corner_size),
            2,
        )

        # Bottom-left corner accent
        pygame.draw.line(
            surface,
            GOLD_BRIGHT,
            (rect.left + accent_offset, rect.bottom - accent_offset),
            (rect.left + accent_offset + corner_size, rect.bottom - accent_offset),
            2,
        )
        pygame.draw.line(
            surface,
            GOLD_BRIGHT,
            (rect.left + accent_offset, rect.bottom - accent_offset),
            (rect.left + accent_offset, rect.bottom - accent_offset - corner_size),
            2,
        )

        # Bottom-right corner accent
        pygame.draw.line(
            surface,
            GOLD_BRIGHT,
            (rect.right - accent_offset, rect.bottom - accent_offset),
            (rect.right - accent_offset - corner_size, rect.bottom - accent_offset),
            2,
        )
        pygame.draw.line(
            surface,
            GOLD_BRIGHT,
            (rect.right - accent_offset, rect.bottom - accent_offset),
            (rect.right - accent_offset, rect.bottom - accent_offset - corner_size),
            2,
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
        """Draws a Dark Souls-style button with rounded corners."""
        # Adjust colors for hover state
        if hover:
            bg_color = tuple(min(255, c + 20) for c in bg_color)
            border_color = GOLD_BRIGHT

        # Draw shadow with rounded corners
        shadow_rect = rect.copy()
        shadow_rect.x += 2
        shadow_rect.y += 2
        shadow_surf = pygame.Surface(shadow_rect.size, pygame.SRCALPHA)
        pygame.draw.rect(
            shadow_surf,
            (0, 0, 0, 150),
            shadow_surf.get_rect(),
            border_radius=self.corner_radius - 2,
        )
        surface.blit(shadow_surf, shadow_rect.topleft)

        # Draw button background with rounded corners
        pygame.draw.rect(surface, bg_color, rect, border_radius=self.corner_radius - 2)

        # Draw border with rounded corners
        pygame.draw.rect(
            surface, DARK_BG, rect, 2, border_radius=self.corner_radius - 2
        )
        pygame.draw.rect(
            surface, border_color, rect, 1, border_radius=self.corner_radius - 2
        )

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
        """Draws a stylized health bar with rounded corners."""
        bar_radius = height // 2  # Pill-shaped

        # Background
        bg_rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect(surface, HEALTH_BG, bg_rect, border_radius=bar_radius)

        # Health fill
        if maximum > 0:
            health_ratio = current / maximum
            fill_width = int(width * health_ratio)
            if fill_width > bar_radius * 2:  # Only draw if wide enough for rounded
                fill_rect = pygame.Rect(x, y, fill_width, height)
                pygame.draw.rect(
                    surface, fill_color, fill_rect, border_radius=bar_radius
                )

                # Gradient highlight on top half
                highlight_rect = pygame.Rect(
                    x + 2, y + 1, fill_width - 4, height // 2 - 1
                )
                if highlight_rect.width > 0:
                    highlight_surf = pygame.Surface(
                        highlight_rect.size, pygame.SRCALPHA
                    )
                    highlight_surf.fill((*bright_color, 80))
                    surface.blit(highlight_surf, highlight_rect.topleft)
            elif fill_width > 0:
                # For small fills, just draw rectangle
                fill_rect = pygame.Rect(x, y, fill_width, height)
                pygame.draw.rect(
                    surface, fill_color, fill_rect, border_radius=bar_radius
                )

        # Border
        pygame.draw.rect(surface, HEALTH_BORDER, bg_rect, 1, border_radius=bar_radius)

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

    def _draw_info_panel(self, surface, game_state, teams):
        """Draws the main info panel with turn info and team money."""
        # Adjust panel height based on number of teams
        panel_height = 100 + len(teams) * 28
        adjusted_rect = pygame.Rect(
            self.info_panel_rect.x,
            self.info_panel_rect.y,
            self.info_panel_rect.width,
            panel_height,
        )

        # Draw ornate panel
        self._draw_ornate_panel(surface, adjusted_rect)

        x = adjusted_rect.x + self.panel_padding
        y = adjusted_rect.y + self.panel_padding

        # Turn counter
        turn_text = f"Turn {game_state.turn_count}"
        turn_surf = self.font.render(turn_text, True, GOLD_ACCENT)
        surface.blit(turn_surf, (x, y))

        # Current phase indicator
        y += 25
        current_team = game_state.get_current_team(teams)
        if current_team:
            phase_text = f"{current_team.name}'s Turn"
            phase_color = current_team.light_color
        else:
            phase_text = "Unknown Turn"
            phase_color = BONE_WHITE

        phase_surf = self.font.render(phase_text, True, phase_color)
        surface.blit(phase_surf, (x, y))

        # Separator line
        y += 28
        pygame.draw.line(
            surface,
            GOLD_ACCENT,
            (x, y),
            (adjusted_rect.right - self.panel_padding, y),
            1,
        )

        # Draw money for each team
        y += 8
        for team in teams:
            self._draw_money_display(surface, x, y, team.money, team.color)

            # Team label
            team_label = self.tiny_font.render(team.name, True, team.light_color)
            surface.blit(team_label, (x + 60, y - 2))

            y += 28

    def _draw_end_turn_button(self, surface, game_state, current_team):
        """Draws the End Turn button."""
        # Check if mouse is hovering
        mouse_pos = pygame.mouse.get_pos()
        hover = self.end_turn_button_rect.collidepoint(mouse_pos)

        # Use current team's color for button
        if current_team:
            bg_color = current_team.dark_color
            border_color = current_team.light_color if hover else current_team.color
        else:
            bg_color = DARK_PANEL
            border_color = GOLD_BRIGHT if hover else GOLD_ACCENT

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

        # Title - Capital
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

        # Separator
        y += 22
        pygame.draw.line(
            surface,
            DARK_BORDER,
            (x, y),
            (self.creation_menu_rect.right - self.panel_padding, y),
            1,
        )
        y += 8

        # Title - Seer
        from seer import Seer

        seer_title = self.small_font.render("Spawn Seer (Scout)", True, GOLD_ACCENT)
        surface.blit(seer_title, (x, y))

        y += 20

        seer_cost_text = f"Cost: {Seer.COST} gold"
        can_afford_seer = current_team.can_afford(Seer.COST)
        seer_cost_color = MONEY_GOLD if can_afford_seer else (100, 100, 100)
        seer_cost_surf = self.tiny_font.render(seer_cost_text, True, seer_cost_color)
        surface.blit(seer_cost_surf, (x, y))

        # Store seer button rect for click detection
        self.seer_button_rect = pygame.Rect(x + 100, y - 3, 80, 22)

        # Draw spawn seer button
        mouse_pos = pygame.mouse.get_pos()
        hover = self.seer_button_rect.collidepoint(mouse_pos) and can_afford_seer

        btn_bg = (40, 36, 30) if hover else DARK_PANEL
        btn_border = (
            GOLD_BRIGHT if hover else (DARK_BORDER if can_afford_seer else (50, 45, 40))
        )
        btn_text_color = BONE_WHITE if can_afford_seer else (80, 75, 70)

        pygame.draw.rect(surface, btn_bg, self.seer_button_rect, border_radius=4)
        pygame.draw.rect(surface, btn_border, self.seer_button_rect, 1, border_radius=4)

        spawn_text = self.tiny_font.render("Spawn", True, btn_text_color)
        spawn_rect = spawn_text.get_rect(center=self.seer_button_rect.center)
        surface.blit(spawn_text, spawn_rect)

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

            # Draw button background with rounded corners
            pygame.draw.rect(surface, bg_color, rect, border_radius=4)
            pygame.draw.rect(surface, border_color, rect, 1, border_radius=4)

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
        """Draws the bottom instruction bar with rounded top corners."""
        # Draw dark background bar with rounded top corners
        # Create a rect that extends below screen to hide bottom rounding
        extended_rect = self.instructions_rect.copy()
        extended_rect.height += 10
        pygame.draw.rect(
            surface, DARK_BG, extended_rect, border_radius=self.corner_radius
        )

        # Draw top border line with slight curve effect
        pygame.draw.line(
            surface,
            GOLD_ACCENT,
            (self.corner_radius, self.instructions_rect.y),
            (self.screen_width - self.corner_radius, self.instructions_rect.y),
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

    def _draw_game_over(self, surface, game_state, teams=None):
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

        # Find the winning team for display
        winner_team = None
        winner_name = "Unknown"
        if teams and game_state.winner:
            for team in teams:
                if team.side == game_state.winner:
                    winner_team = team
                    winner_name = team.name
                    break

        # Main text - "VICTORY"
        main_text = "VICTORY"
        main_color = GOLD_BRIGHT

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

        # Subtitle with winner's name and color
        subtitle = f"{winner_name} Wins!"
        if winner_team:
            sub_color = winner_team.light_color
        else:
            sub_color = BONE_WHITE

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
