import pygame

# UI Colors
BUTTON_COLOR = (80, 80, 100)
BUTTON_COLOR_ENEMY = (100, 60, 60)  # Reddish tint for enemy turn
BUTTON_TEXT_COLOR = (255, 255, 255)
INFO_TEXT_COLOR = (0, 0, 0)
PLAYER_TURN_COLOR = (50, 150, 50)  # Green for player turn
ENEMY_TURN_COLOR = (180, 50, 50)  # Red for enemy turn
INSTRUCTIONS_TEXT_COLOR = (220, 220, 220)  # Light gray
INSTRUCTIONS_BAR_COLOR = (0, 0, 0, 180)  # Black with ~70% opacity

# Health bar colors
HEALTH_BAR_BG = (60, 60, 60)  # Dark gray background
PLAYER_HEALTH_COLOR = (50, 200, 50)  # Green for player health
ENEMY_HEALTH_COLOR = (200, 50, 50)  # Red for enemy health
HEALTH_BAR_BORDER = (30, 30, 30)  # Darker border

# Game over colors
RIP_COLOR = (200, 0, 0)  # Red for RIP message
RIP_BG_COLOR = (0, 0, 0, 200)  # Semi-transparent black


class UIManager:
    """Manages the drawing and interaction of all UI elements."""

    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height

        # Ensure the font module is initialized
        if not pygame.font.get_init():
            pygame.font.init()

        try:
            self.font = pygame.font.SysFont("Arial", 24)
        except pygame.error:
            self.font = pygame.font.Font(None, 30)  # Fallback to default font

        # Smaller font for instructions
        try:
            self.instructions_font = pygame.font.SysFont("Arial", 18)
        except pygame.error:
            self.instructions_font = pygame.font.Font(None, 24)  # Fallback

        # Large font for RIP message
        try:
            self.rip_font = pygame.font.SysFont("Arial", 120, bold=True)
            self.rip_subtitle_font = pygame.font.SysFont("Arial", 36)
        except pygame.error:
            self.rip_font = pygame.font.Font(None, 120)
            self.rip_subtitle_font = pygame.font.Font(None, 40)

        # Health bar font
        try:
            self.health_font = pygame.font.SysFont("Arial", 16)
        except pygame.error:
            self.health_font = pygame.font.Font(None, 20)

        # Position the End Turn button at the top right
        self.end_turn_button_rect = pygame.Rect(screen_width - 130, 10, 120, 40)

        # Health bar dimensions
        self.health_bar_width = 100
        self.health_bar_height = 16

        # Pre-render the instructions text
        instructions_text = "WASD: Move Camera | Q/E: Zoom Out/In | Click: Move/Attack | Return: End Turn"
        self.instructions_surf = self.instructions_font.render(
            instructions_text, True, INSTRUCTIONS_TEXT_COLOR
        )
        self.instructions_rect = self.instructions_surf.get_rect()
        self.instructions_rect.centerx = screen_width // 2
        self.instructions_rect.bottom = screen_height - 10

        # Create the background bar surface (semi-transparent black)
        bar_padding_x = 20
        bar_padding_y = 8
        self.bar_rect = self.instructions_rect.inflate(
            bar_padding_x * 2, bar_padding_y * 2
        )
        self.bar_surf = pygame.Surface(self.bar_rect.size, pygame.SRCALPHA)
        self.bar_surf.fill(INSTRUCTIONS_BAR_COLOR)

    def draw(self, surface, game_state, player, enemy):
        """Draws all UI elements onto the given surface."""
        # Draw Turn Counter Text
        self._draw_turn_counter(surface, game_state.turn_count)

        # Draw Turn Phase Indicator
        self._draw_turn_phase(surface, game_state)

        # Draw Health Bars
        self._draw_health_bars(surface, player, enemy)

        # Draw End Turn Button
        self._draw_end_turn_button(surface, game_state)

        # Draw controls instructions with background bar
        self._draw_controls_instructions(surface)

        # Draw game over message if applicable
        if game_state.game_over:
            self._draw_game_over(surface, game_state)

    def _draw_turn_counter(self, surface, turn_count):
        text_surf = self.font.render(f"Turn: {turn_count}", True, INFO_TEXT_COLOR)
        surface.blit(text_surf, (10, 15))

    def _draw_turn_phase(self, surface, game_state):
        """Draws an indicator showing whose turn it is."""
        if game_state.is_player_turn():
            phase_text = "Your Turn"
            phase_color = PLAYER_TURN_COLOR
        else:
            phase_text = "Enemy Turn"
            phase_color = ENEMY_TURN_COLOR

        text_surf = self.font.render(phase_text, True, phase_color)
        # Position below the turn counter
        surface.blit(text_surf, (10, 45))

    def _draw_health_bars(self, surface, player, enemy):
        """Draws health bars for both player and enemy."""
        # Player health bar - positioned below turn phase indicator
        player_label = self.health_font.render("Hero:", True, PLAYER_TURN_COLOR)
        surface.blit(player_label, (10, 80))

        player_bar_x = 60
        player_bar_y = 82
        self._draw_single_health_bar(
            surface,
            player_bar_x,
            player_bar_y,
            player.health,
            player.MAX_HEALTH,
            PLAYER_HEALTH_COLOR,
        )

        # Enemy health bar - positioned below player health bar
        enemy_label = self.health_font.render("Enemy:", True, ENEMY_TURN_COLOR)
        surface.blit(enemy_label, (10, 105))

        enemy_bar_x = 60
        enemy_bar_y = 107
        self._draw_single_health_bar(
            surface,
            enemy_bar_x,
            enemy_bar_y,
            enemy.health,
            enemy.MAX_HEALTH,
            ENEMY_HEALTH_COLOR,
        )

    def _draw_single_health_bar(
        self, surface, x, y, current_health, max_health, fill_color
    ):
        """Draws a single health bar."""
        # Draw background
        bg_rect = pygame.Rect(x, y, self.health_bar_width, self.health_bar_height)
        pygame.draw.rect(surface, HEALTH_BAR_BG, bg_rect)

        # Draw health fill
        health_ratio = current_health / max_health
        fill_width = int(self.health_bar_width * health_ratio)
        if fill_width > 0:
            fill_rect = pygame.Rect(x, y, fill_width, self.health_bar_height)
            pygame.draw.rect(surface, fill_color, fill_rect)

        # Draw border
        pygame.draw.rect(surface, HEALTH_BAR_BORDER, bg_rect, 2)

        # Draw health text
        health_text = self.health_font.render(
            f"{current_health}/{max_health}", True, BUTTON_TEXT_COLOR
        )
        text_rect = health_text.get_rect(center=bg_rect.center)
        surface.blit(health_text, text_rect)

    def _draw_end_turn_button(self, surface, game_state):
        # Don't draw button if game is over
        if game_state.game_over:
            return

        # Use different color based on whose turn it is
        if game_state.is_player_turn():
            button_color = BUTTON_COLOR
            button_text = "End Turn"
        else:
            button_color = BUTTON_COLOR_ENEMY
            button_text = "End Turn"

        pygame.draw.rect(
            surface, button_color, self.end_turn_button_rect, border_radius=8
        )
        button_text_surf = self.font.render(button_text, True, BUTTON_TEXT_COLOR)
        text_rect = button_text_surf.get_rect(center=self.end_turn_button_rect.center)
        surface.blit(button_text_surf, text_rect)

    def _draw_controls_instructions(self, surface):
        """Draws the background bar and then the instructional text."""
        # Draw the semi-transparent black bar
        surface.blit(self.bar_surf, self.bar_rect.topleft)

        # Draw the text on top (centered as before)
        surface.blit(self.instructions_surf, self.instructions_rect)

    def _draw_game_over(self, surface, game_state):
        """Draws the big RIP game over message."""
        # Create semi-transparent overlay
        overlay = pygame.Surface(
            (self.screen_width, self.screen_height), pygame.SRCALPHA
        )
        overlay.fill(RIP_BG_COLOR)
        surface.blit(overlay, (0, 0))

        # Draw big RIP text
        rip_text = self.rip_font.render("RIP", True, RIP_COLOR)
        rip_rect = rip_text.get_rect(
            centerx=self.screen_width // 2, centery=self.screen_height // 2 - 40
        )
        surface.blit(rip_text, rip_rect)

        # Draw subtitle showing who died
        if game_state.player_wins():
            subtitle = "Enemy has been defeated!"
            subtitle_color = PLAYER_TURN_COLOR
        else:
            subtitle = "You have been defeated!"
            subtitle_color = ENEMY_TURN_COLOR

        subtitle_surf = self.rip_subtitle_font.render(subtitle, True, subtitle_color)
        subtitle_rect = subtitle_surf.get_rect(
            centerx=self.screen_width // 2, centery=self.screen_height // 2 + 60
        )
        surface.blit(subtitle_surf, subtitle_rect)

        # Draw restart hint
        hint_text = "Press ESC to quit"
        hint_surf = self.font.render(hint_text, True, INSTRUCTIONS_TEXT_COLOR)
        hint_rect = hint_surf.get_rect(
            centerx=self.screen_width // 2, centery=self.screen_height // 2 + 120
        )
        surface.blit(hint_surf, hint_rect)
