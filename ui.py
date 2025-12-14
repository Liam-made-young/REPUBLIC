import pygame

# UI Colors
BUTTON_COLOR = (80, 80, 100)
BUTTON_TEXT_COLOR = (255, 255, 255)
INFO_TEXT_COLOR = (0, 0, 0)
INSTRUCTIONS_TEXT_COLOR = (220, 220, 220)  # Light gray
INSTRUCTIONS_BAR_COLOR = (0, 0, 0, 180)  # Black with ~70% opacity


class UIManager:
    """Manages the drawing and interaction of all UI elements."""

    def __init__(self, screen_width, screen_height):
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

        # Position the End Turn button at the top right
        self.end_turn_button_rect = pygame.Rect(screen_width - 130, 10, 120, 40)

        # Pre-render the instructions text
        instructions_text = "WASD: Move Camera | Q/E: Zoom Out/In | Click: Move Character | Return: End Turn"
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

    def draw(self, surface, game_state):
        """Draws all UI elements onto the given surface."""
        # Draw Turn Counter Text
        self._draw_turn_counter(surface, game_state.turn_count)

        # Draw End Turn Button
        self._draw_end_turn_button(surface)

        # Draw controls instructions with background bar
        self._draw_controls_instructions(surface)

    def _draw_turn_counter(self, surface, turn_count):
        text_surf = self.font.render(f"Turn: {turn_count}", True, INFO_TEXT_COLOR)
        surface.blit(text_surf, (10, 15))

    def _draw_end_turn_button(self, surface):
        pygame.draw.rect(
            surface, BUTTON_COLOR, self.end_turn_button_rect, border_radius=8
        )
        button_text = self.font.render("End Turn", True, BUTTON_TEXT_COLOR)
        text_rect = button_text.get_rect(center=self.end_turn_button_rect.center)
        surface.blit(button_text, text_rect)

    def _draw_controls_instructions(self, surface):
        """Draws the background bar and then the instructional text."""
        # Draw the semi-transparent black bar
        surface.blit(self.bar_surf, self.bar_rect.topleft)

        # Draw the text on top (centered as before)
        surface.blit(self.instructions_surf, self.instructions_rect)
