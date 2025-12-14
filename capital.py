import pygame


class Capital:
    """Represents a team's capital/headquarters on the map."""

    # Capital constants
    GLOW_RADIUS = 3  # 7x7 area (3 tiles in each direction from center)
    VISIBILITY_RADIUS = 3  # Initial fog of war reveal radius
    MIN_DISTANCE_FROM_OTHER_CAPITALS = 14  # Minimum tiles between capitals
    COST = 10  # Money cost to create a new capital
    MAX_CHARACTERS_PER_CAPITAL = (
        3  # Maximum characters that can be spawned from this capital
    )

    # Class variable to track unique IDs
    _next_id = 0

    def __init__(self, x, y, team):
        """
        Initializes a capital.

        Args:
            x (int): The x-coordinate (tile) of the capital.
            y (int): The y-coordinate (tile) of the capital.
            team: The Team object this capital belongs to.
        """
        # Assign unique ID
        self.id = Capital._next_id
        Capital._next_id += 1

        self.x = x
        self.y = y
        self.team = team
        self.spawned_characters = 0  # Total characters spawned from this capital
        self.spawned_this_turn = False  # Whether a character was spawned this turn

    def can_spawn_character(self):
        """
        Checks if this capital can spawn another character.

        Returns:
            bool: True if under the spawn limit and hasn't spawned this turn.
        """
        return (
            self.spawned_characters < self.MAX_CHARACTERS_PER_CAPITAL
            and not self.spawned_this_turn
        )

    def spawn_character(self):
        """
        Marks that a character has been spawned from this capital.
        Should be called after successfully creating a character.
        """
        self.spawned_characters += 1
        self.spawned_this_turn = True

    def reset_turn(self):
        """Resets turn-specific state (called at the start of the team's turn)."""
        self.spawned_this_turn = False

    def get_spawn_positions(self):
        """
        Returns a list of valid spawn positions around the capital.
        Characters spawn adjacent to the capital.

        Returns:
            list: List of (x, y) tuples for valid spawn positions.
        """
        positions = []
        # Check all 8 adjacent tiles
        for dx in range(-1, 2):
            for dy in range(-1, 2):
                if dx == 0 and dy == 0:
                    continue  # Skip the capital's own position
                positions.append((self.x + dx, self.y + dy))
        return positions

    def get_glow_tiles(self):
        """
        Returns a list of all tiles within the capital's glow radius.

        Returns:
            list: List of (x, y) tuples for tiles in the glow area.
        """
        tiles = []
        for dx in range(-self.GLOW_RADIUS, self.GLOW_RADIUS + 1):
            for dy in range(-self.GLOW_RADIUS, self.GLOW_RADIUS + 1):
                tiles.append((self.x + dx, self.y + dy))
        return tiles

    def is_tile_in_glow(self, tile_x, tile_y):
        """
        Checks if a tile is within the capital's glow radius.

        Args:
            tile_x (int): The x-coordinate to check.
            tile_y (int): The y-coordinate to check.

        Returns:
            bool: True if the tile is within the glow radius.
        """
        dist_x = abs(tile_x - self.x)
        dist_y = abs(tile_y - self.y)
        return max(dist_x, dist_y) <= self.GLOW_RADIUS

    def is_protected(self, characters):
        """
        Checks if the capital is protected by friendly characters.

        Args:
            characters: List of all characters to check.

        Returns:
            bool: True if at least one friendly character is adjacent.
        """
        for char in characters:
            if char.is_dead():
                continue
            if char.team == self.team:
                # Check if character is adjacent (within 1 tile)
                dist_x = abs(char.x - self.x)
                dist_y = abs(char.y - self.y)
                if max(dist_x, dist_y) <= 1:
                    return True
        return False

    def get_remaining_spawns(self):
        """
        Returns the number of characters that can still be spawned from this capital.

        Returns:
            int: Number of remaining spawns.
        """
        return self.MAX_CHARACTERS_PER_CAPITAL - self.spawned_characters

    @staticmethod
    def is_valid_capital_position(x, y, all_capitals):
        """
        Checks if a position is valid for placing a new capital.
        Must be at least MIN_DISTANCE_FROM_OTHER_CAPITALS away from all existing capitals.

        Args:
            x (int): The x-coordinate to check.
            y (int): The y-coordinate to check.
            all_capitals: List of all existing capitals.

        Returns:
            bool: True if the position is valid.
        """
        for capital in all_capitals:
            dist_x = abs(x - capital.x)
            dist_y = abs(y - capital.y)
            if max(dist_x, dist_y) < Capital.MIN_DISTANCE_FROM_OTHER_CAPITALS:
                return False
        return True

    def draw_placeholder(self, surface, screen_x, screen_y, tile_size, font=None):
        """
        Draws a placeholder 'C' for the capital.

        Args:
            surface: The pygame surface to draw on.
            screen_x: Screen x-coordinate.
            screen_y: Screen y-coordinate.
            tile_size: Size of a tile in pixels.
            font: Optional pygame font to use.
        """
        # Draw a background circle in team color
        center_x = screen_x + tile_size // 2
        center_y = screen_y + tile_size // 2
        radius = tile_size // 2 - 2

        # Draw filled circle with team color
        pygame.draw.circle(surface, self.team.dark_color, (center_x, center_y), radius)
        pygame.draw.circle(surface, self.team.color, (center_x, center_y), radius, 3)

        # Draw the 'C' letter
        if font is None:
            font = pygame.font.Font(None, tile_size)

        text_color = (255, 255, 255)  # White text
        text_surf = font.render("C", True, text_color)
        text_rect = text_surf.get_rect(center=(center_x, center_y))
        surface.blit(text_surf, text_rect)

    def __repr__(self):
        return f"Capital(id={self.id}, team={self.team.name}, pos=({self.x},{self.y}), spawns={self.spawned_characters}/{self.MAX_CHARACTERS_PER_CAPITAL})"
