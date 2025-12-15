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

        # Creation menu panel (appears when toggled) - made taller for all building options
        self.creation_menu_rect = pygame.Rect(
            screen_width - 250, self.panel_margin + 155, 235, 260
        )

        # Character creation menu (appears when clicking capital)
        self.char_menu_width = 280
        self.char_menu_height = 400
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

        # Building button rects (initialized in draw method)
        self.capital_button_rect = pygame.Rect(0, 0, 0, 0)
        self.seer_button_rect = pygame.Rect(0, 0, 0, 0)
        self.hospital_button_rect = pygame.Rect(0, 0, 0, 0)
        self.mine_button_rect = pygame.Rect(0, 0, 0, 0)
        self.upgrade_cap_button_rect = pygame.Rect(0, 0, 0, 0)

        # Placement mode tracking
        self.placement_mode = None  # None, "capital", "hospital", or "mine"

        # Bottom instruction bar
        self.instructions_height = 35
        self.instructions_rect = pygame.Rect(
            0,
            screen_height - self.instructions_height,
            screen_width,
            self.instructions_height,
        )

    def _update_rects(self):
        """Updates all rect positions after a resize."""
        # Top left info panel
        self.info_panel_rect = pygame.Rect(
            self.panel_margin, self.panel_margin, 200, 140
        )

        # End Turn button (top right, moved down to avoid menu button overlap)
        self.end_turn_button_rect = pygame.Rect(
            self.screen_width - 145, self.panel_margin + 55, 130, 45
        )

        # Creation menu button (below end turn)
        self.creation_menu_button_rect = pygame.Rect(
            self.screen_width - 145, self.panel_margin + 110, 130, 35
        )

        # Creation menu panel (appears when toggled)
        self.creation_menu_rect = pygame.Rect(
            self.screen_width - 250, self.panel_margin + 155, 235, 260
        )

        # Character creation menu (appears when clicking capital)
        self.char_menu_rect = pygame.Rect(
            (self.screen_width - self.char_menu_width) // 2,
            (self.screen_height - self.char_menu_height) // 2,
            self.char_menu_width,
            self.char_menu_height,
        )

        # Update char buttons positions
        self._setup_char_buttons()

        # Bottom instruction bar
        self.instructions_rect = pygame.Rect(
            0,
            self.screen_height - self.instructions_height,
            self.screen_width,
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
            ("tank", "Tank", 12, "30 HP, 20 DMG, 10 MOV, Chain x4"),
            ("king", "King", 20, "1 HP, 0 DMG - REVEALS FOG"),
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

        # Upgrade button setup
        # Upgrade button setup (positioned after characters)
        last_button_bottom = self.char_buttons[-1]["rect"].bottom if self.char_buttons else start_y
        self.upgrade_cap_button_rect = pygame.Rect(
            self.char_menu_rect.centerx - 100,
            last_button_bottom + 15,
            200,
            30
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
        """Draws the creation menu dropdown with clickable buttons."""
        self._draw_ornate_panel(surface, self.creation_menu_rect)

        x = self.creation_menu_rect.x + self.panel_padding
        y = self.creation_menu_rect.y + self.panel_padding
        mouse_pos = pygame.mouse.get_pos()

        # === CAPITAL SECTION ===
        from capital import Capital

        title_surf = self.small_font.render("Create Capital", True, GOLD_ACCENT)
        surface.blit(title_surf, (x, y))
        y += 20

        can_afford_cap = current_team.can_afford(Capital.COST)
        cost_text = f"Cost: {Capital.COST} gold"
        cost_color = MONEY_GOLD if can_afford_cap else (100, 100, 100)
        cost_surf = self.tiny_font.render(cost_text, True, cost_color)
        surface.blit(cost_surf, (x, y))

        # Capital button
        self.capital_button_rect = pygame.Rect(x + 100, y - 3, 80, 22)
        cap_hover = self.capital_button_rect.collidepoint(mouse_pos) and can_afford_cap
        cap_selected = self.placement_mode == "capital"

        cap_bg = (
            (60, 50, 40)
            if cap_selected
            else ((40, 36, 30) if cap_hover else DARK_PANEL)
        )
        cap_border = (
            GOLD_BRIGHT
            if (cap_hover or cap_selected)
            else (DARK_BORDER if can_afford_cap else (50, 45, 40))
        )
        cap_text_color = (
            GOLD_BRIGHT
            if cap_selected
            else (BONE_WHITE if can_afford_cap else (80, 75, 70))
        )

        pygame.draw.rect(surface, cap_bg, self.capital_button_rect, border_radius=4)
        pygame.draw.rect(
            surface, cap_border, self.capital_button_rect, 1, border_radius=4
        )

        cap_btn_text = "Placing..." if cap_selected else "Place"
        cap_text_surf = self.tiny_font.render(cap_btn_text, True, cap_text_color)
        cap_text_rect = cap_text_surf.get_rect(center=self.capital_button_rect.center)
        surface.blit(cap_text_surf, cap_text_rect)

        # Separator
        y += 26
        pygame.draw.line(
            surface,
            DARK_BORDER,
            (x, y),
            (self.creation_menu_rect.right - self.panel_padding, y),
            1,
        )
        y += 8

        # === SEER SECTION ===
        from seer import Seer

        seer_title = self.small_font.render("Spawn Seer (Scout)", True, GOLD_ACCENT)
        surface.blit(seer_title, (x, y))
        y += 20

        can_afford_seer = current_team.can_afford(Seer.COST)
        seer_cost_text = f"Cost: {Seer.COST} gold"
        seer_cost_color = MONEY_GOLD if can_afford_seer else (100, 100, 100)
        seer_cost_surf = self.tiny_font.render(seer_cost_text, True, seer_cost_color)
        surface.blit(seer_cost_surf, (x, y))

        # Seer button
        self.seer_button_rect = pygame.Rect(x + 100, y - 3, 80, 22)
        seer_hover = self.seer_button_rect.collidepoint(mouse_pos) and can_afford_seer

        seer_bg = (40, 36, 30) if seer_hover else DARK_PANEL
        seer_border = (
            GOLD_BRIGHT
            if seer_hover
            else (DARK_BORDER if can_afford_seer else (50, 45, 40))
        )
        seer_text_color = BONE_WHITE if can_afford_seer else (80, 75, 70)

        pygame.draw.rect(surface, seer_bg, self.seer_button_rect, border_radius=4)
        pygame.draw.rect(
            surface, seer_border, self.seer_button_rect, 1, border_radius=4
        )

        seer_text_surf = self.tiny_font.render("Spawn", True, seer_text_color)
        seer_text_rect = seer_text_surf.get_rect(center=self.seer_button_rect.center)
        surface.blit(seer_text_surf, seer_text_rect)

        # Separator
        y += 26
        pygame.draw.line(
            surface,
            DARK_BORDER,
            (x, y),
            (self.creation_menu_rect.right - self.panel_padding, y),
            1,
        )
        y += 8

        # === HOSPITAL SECTION ===
        from hospital import Hospital

        hosp_title = self.small_font.render("Build Hospital", True, GOLD_ACCENT)
        surface.blit(hosp_title, (x, y))
        y += 20

        can_afford_hosp = current_team.can_afford(Hospital.BUILD_COST)
        hosp_cost_text = f"Cost: {Hospital.BUILD_COST} gold"
        hosp_cost_color = MONEY_GOLD if can_afford_hosp else (100, 100, 100)
        hosp_cost_surf = self.tiny_font.render(hosp_cost_text, True, hosp_cost_color)
        surface.blit(hosp_cost_surf, (x, y))

        # Hospital button
        self.hospital_button_rect = pygame.Rect(x + 100, y - 3, 80, 22)
        hosp_hover = (
            self.hospital_button_rect.collidepoint(mouse_pos) and can_afford_hosp
        )
        hosp_selected = self.placement_mode == "hospital"

        hosp_bg = (
            (60, 50, 40)
            if hosp_selected
            else ((40, 36, 30) if hosp_hover else DARK_PANEL)
        )
        hosp_border = (
            GOLD_BRIGHT
            if (hosp_hover or hosp_selected)
            else (DARK_BORDER if can_afford_hosp else (50, 45, 40))
        )
        hosp_text_color = (
            GOLD_BRIGHT
            if hosp_selected
            else (BONE_WHITE if can_afford_hosp else (80, 75, 70))
        )

        pygame.draw.rect(surface, hosp_bg, self.hospital_button_rect, border_radius=4)
        pygame.draw.rect(
            surface, hosp_border, self.hospital_button_rect, 1, border_radius=4
        )

        hosp_btn_text = "Placing..." if hosp_selected else "Place"
        hosp_text_surf = self.tiny_font.render(hosp_btn_text, True, hosp_text_color)
        hosp_text_rect = hosp_text_surf.get_rect(
            center=self.hospital_button_rect.center
        )
        surface.blit(hosp_text_surf, hosp_text_rect)

        # Separator
        y += 26
        pygame.draw.line(
            surface,
            DARK_BORDER,
            (x, y),
            (self.creation_menu_rect.right - self.panel_padding, y),
            1,
        )
        y += 8

        # === MINE SECTION ===
        from mine import Mine

        mine_title = self.small_font.render("Build Mine", True, GOLD_ACCENT)
        surface.blit(mine_title, (x, y))
        y += 20

        can_afford_mine = current_team.can_afford(Mine.BUILD_COST)
        mine_cost_text = f"Cost: {Mine.BUILD_COST}g (+1g/turn)"
        mine_cost_color = MONEY_GOLD if can_afford_mine else (100, 100, 100)
        mine_cost_surf = self.tiny_font.render(mine_cost_text, True, mine_cost_color)
        surface.blit(mine_cost_surf, (x, y))

        # Mine button
        self.mine_button_rect = pygame.Rect(x + 120, y - 3, 80, 22)
        mine_hover = self.mine_button_rect.collidepoint(mouse_pos) and can_afford_mine
        mine_selected = self.placement_mode == "mine"

        mine_bg = (
            (60, 50, 40)
            if mine_selected
            else ((40, 36, 30) if mine_hover else DARK_PANEL)
        )
        mine_border = (
            GOLD_BRIGHT
            if (mine_hover or mine_selected)
            else (DARK_BORDER if can_afford_mine else (50, 45, 40))
        )
        mine_text_color = (
            GOLD_BRIGHT
            if mine_selected
            else (BONE_WHITE if can_afford_mine else (80, 75, 70))
        )

        pygame.draw.rect(surface, mine_bg, self.mine_button_rect, border_radius=4)
        pygame.draw.rect(
            surface, mine_border, self.mine_button_rect, 1, border_radius=4
        )

        mine_btn_text = "Placing..." if mine_selected else "Place"
        mine_text_surf = self.tiny_font.render(mine_btn_text, True, mine_text_color)
        mine_text_rect = mine_text_surf.get_rect(center=self.mine_button_rect.center)
        surface.blit(mine_text_surf, mine_text_rect)

        # Granite only note
        y += 22
        granite_note = self.tiny_font.render(
            "(Granite tiles only)", True, (120, 115, 110)
        )
        surface.blit(granite_note, (x, y))

        # Show placement instructions at bottom
        y += 20
        if self.placement_mode:
            if self.placement_mode == "mine":
                inst_text = "Click on GRANITE to place mine. Right-click to cancel."
            else:
                inst_text = f"Click on map to place {self.placement_mode}. Right-click to cancel."
            inst_surf = self.tiny_font.render(inst_text, True, GOLD_BRIGHT)
            surface.blit(inst_surf, (x, y))

    def _draw_character_menu(self, surface, game_state, current_team):
        """Draws the character creation menu when clicking a capital."""
        self._draw_ornate_panel(surface, self.char_menu_rect, GOLD_ACCENT, DARK_BG)

        x = self.char_menu_rect.x + self.panel_padding
        y = self.char_menu_rect.y + self.panel_padding

        # Get selected capital to check for upgrade discount
        selected_capital = game_state.selected_capital
        is_upgraded = selected_capital and selected_capital.is_upgraded

        # Title
        title_text = "Recruit Unit"
        if is_upgraded:
            title_text = "Recruit Unit (50% OFF!)"
        title_surf = self.font.render(title_text, True, GOLD_BRIGHT)
        title_rect = title_surf.get_rect(centerx=self.char_menu_rect.centerx, top=y)
        surface.blit(title_surf, title_rect)

        # Draw character type buttons
        mouse_pos = pygame.mouse.get_pos()

        for button in self.char_buttons:
            rect = button["rect"]
            hover = rect.collidepoint(mouse_pos)

            # Calculate adjusted cost if capital is upgraded
            base_cost = button["cost"]
            if is_upgraded:
                adjusted_cost = max(1, (base_cost + 1) // 2)  # Half price, rounded up
            else:
                adjusted_cost = base_cost

            can_afford = current_team.can_afford(adjusted_cost)

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

            # Draw button content with adjusted cost display
            if is_upgraded and adjusted_cost < base_cost:
                name_text = f"{button['name']} (${adjusted_cost})"
                # Show strikethrough original price
                old_price_surf = self.tiny_font.render(
                    f"${base_cost}", True, (100, 90, 80)
                )
                name_surf = self.small_font.render(
                    name_text, True, (100, 255, 100) if can_afford else text_color
                )
            else:
                name_text = f"{button['name']} (${base_cost})"
                name_surf = self.small_font.render(name_text, True, text_color)
            name_rect = name_surf.get_rect(midleft=(rect.x + 8, rect.centery - 6))
            surface.blit(name_surf, name_rect)

            stats_surf = self.tiny_font.render(
                button["stats"], True, text_color if can_afford else (80, 75, 70)
            )
            stats_rect = stats_surf.get_rect(midleft=(rect.x + 8, rect.centery + 8))
            surface.blit(stats_surf, stats_rect)

        # Upgrade button if not upgraded
        if selected_capital and not is_upgraded:
            from capital import Capital
            
            # Recalculate rect based on current menu position
            # Recalculate rect based on current menu position and last button
            # Note: We duplicate the logic from _setup_char_buttons so it follows dynamic positioning
            button_height = 35
            button_margin = 5
            start_y = self.char_menu_rect.y + 45
            last_button_y = start_y + (len(self.char_buttons)-1) * (button_height + button_margin)
            last_button_bottom = last_button_y + button_height
            
            self.upgrade_cap_button_rect = pygame.Rect(
                self.char_menu_rect.centerx - 100,
                last_button_bottom + 15,
                200,
                30
            )
            
            cost = Capital.UPGRADE_COST
            can_afford = current_team.can_afford(cost)
            mouse_pos = pygame.mouse.get_pos()
            hover = self.upgrade_cap_button_rect.collidepoint(mouse_pos) and can_afford
            
            bg_color = (40, 36, 30) if hover else DARK_PANEL
            border_color = GOLD_BRIGHT if hover else (GOLD_ACCENT if can_afford else (80, 75, 70))
            text_color = GOLD_BRIGHT if can_afford else (100, 95, 90)
            
            pygame.draw.rect(surface, bg_color, self.upgrade_cap_button_rect, border_radius=4)
            pygame.draw.rect(surface, border_color, self.upgrade_cap_button_rect, 1, border_radius=4)
            
            text = f"Upgrade Capital ({cost}g)"
            text_surf = self.small_font.render(text, True, text_color)
            text_rect = text_surf.get_rect(center=self.upgrade_cap_button_rect.center)
            surface.blit(text_surf, text_rect)
            
            # Effect text
            effect_surf = self.tiny_font.render("Double Income + Stronger Units", True, (150, 140, 100))
            effect_rect = effect_surf.get_rect(centerx=self.char_menu_rect.centerx, top=self.upgrade_cap_button_rect.bottom + 2)
            surface.blit(effect_surf, effect_rect)

        # Close button hint
        close_text = "Click outside to close"
        close_surf = self.tiny_font.render(close_text, True, (120, 115, 105))
        close_rect = close_surf.get_rect(
            centerx=self.char_menu_rect.centerx, bottom=self.char_menu_rect.bottom - 10
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
            text = "Select a unit to recruit  |  Click outside to cancel  |  SHIFT+Click capital = Upgrade"
        elif game_state.show_creation_menu:
            text = "Click to place building  |  Mines: granite only  |  Right-click to cancel"
        elif game_state.selected_character:
            text = "Click to move/attack  |  Click again to deselect  |  SHIFT+Click building = Upgrade"
        else:
            text = "Click unit to select  |  Click capital to recruit  |  SHIFT+Click building = Upgrade"

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

    def handle_creation_menu_click(self, pos, current_team):
        """
        Handles clicks within the creation menu.

        Returns:
            str or None: "seer" if seer should spawn, "capital"/"hospital"/"mine" if entering placement mode, None otherwise
        """
        from capital import Capital
        from hospital import Hospital
        from mine import Mine
        from seer import Seer

        print(f"DEBUG UI: handle_creation_menu_click at {pos}")
        print(f"DEBUG UI: capital_button_rect = {self.capital_button_rect}")
        print(
            f"DEBUG UI: current money = {current_team.money}, capital cost = {Capital.COST}"
        )

        # Check capital button
        if self.capital_button_rect.collidepoint(pos):
            print("DEBUG UI: Capital button clicked!")
            if current_team.can_afford(Capital.COST):
                if self.placement_mode == "capital":
                    self.placement_mode = None  # Toggle off
                    print("DEBUG UI: Toggled capital placement OFF")
                else:
                    self.placement_mode = "capital"
                    print("DEBUG UI: Toggled capital placement ON")
                return "capital_mode"
            else:
                print("DEBUG UI: Cannot afford capital")

        # Check seer button - immediate spawn
        if self.seer_button_rect.collidepoint(pos):
            if current_team.can_afford(Seer.COST):
                return "seer"

        # Check hospital button
        if self.hospital_button_rect.collidepoint(pos):
            if current_team.can_afford(Hospital.BUILD_COST):
                if self.placement_mode == "hospital":
                    self.placement_mode = None  # Toggle off
                else:
                    self.placement_mode = "hospital"
                return "hospital_mode"

        # Check mine button
        if self.mine_button_rect.collidepoint(pos):
            if current_team.can_afford(Mine.BUILD_COST):
                if self.placement_mode == "mine":
                    self.placement_mode = None  # Toggle off
                else:
                    self.placement_mode = "mine"
                return "mine_mode"

        return None

    def clear_placement_mode(self):
        """Clears any active placement mode."""
        self.placement_mode = None
