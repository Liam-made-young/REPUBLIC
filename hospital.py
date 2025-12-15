"""
Hospital building for REPUBLIC.

Hospitals heal all friendly characters within their radius.
Can be upgraded to expand the heal radius from 5x5 to 9x9.
"""

import pygame


class Hospital:
    """
    A building that heals all friendly characters in a radius.
    Costs 8 gold to build, 1 gold to activate healing.
    Can be upgraded for 20 gold to expand heal radius from 5x5 to 9x9.
    """

    # Hospital constants
    BUILD_COST = 8  # Gold cost to build
    HEAL_COST = 1  # Gold cost to heal
    HEAL_RADIUS = 2  # 5x5 area (2 tiles in each direction from center)
    UPGRADED_HEAL_RADIUS = 4  # 9x9 area (4 tiles in each direction)
    UPGRADE_COST = 20  # Gold cost to upgrade

    # Class variable to track unique IDs
    _next_id = 0

    def __init__(self, x, y, team):
        """
        Initializes a Hospital.

        Args:
            x (int): The x-coordinate (tile) of the hospital.
            y (int): The y-coordinate (tile) of the hospital.
            team: The Team object this hospital belongs to.
        """
        # Assign unique ID
        self.id = Hospital._next_id
        Hospital._next_id += 1

        self.x = x
        self.y = y
        self.team = team
        self.has_healed_this_turn = False

        # Upgrade state
        self.is_upgraded = False

    @property
    def current_heal_radius(self):
        """Returns the current heal radius based on upgrade status."""
        return self.UPGRADED_HEAL_RADIUS if self.is_upgraded else self.HEAL_RADIUS

    def reset_turn(self):
        """Resets turn-specific state."""
        self.has_healed_this_turn = False

    def can_heal(self, team):
        """
        Checks if the hospital can perform healing.

        Args:
            team: The team attempting to heal.

        Returns:
            bool: True if healing is possible.
        """
        return (
            team == self.team
            and not self.has_healed_this_turn
            and team.can_afford(self.HEAL_COST)
        )

    def can_upgrade(self):
        """
        Checks if this hospital can be upgraded.

        Returns:
            bool: True if not already upgraded and team can afford it.
        """
        return not self.is_upgraded and self.team.can_afford(self.UPGRADE_COST)

    def upgrade(self):
        """
        Upgrades this hospital (expands heal radius to 9x9).

        Returns:
            bool: True if upgrade was successful.
        """
        if not self.can_upgrade():
            return False

        self.team.spend_money(self.UPGRADE_COST)
        self.is_upgraded = True
        print(
            f"Hospital at ({self.x}, {self.y}) upgraded! Heal radius expanded to 9x9."
        )
        return True

    def heal_characters(self, characters):
        """
        Heals all friendly characters within the heal radius to full health.

        Args:
            characters: List of all characters to check.

        Returns:
            int: Number of characters healed.
        """
        if not self.team.can_afford(self.HEAL_COST):
            return 0

        healed_count = 0

        for char in characters:
            # Only heal friendly, living characters
            if char.team != self.team:
                continue
            if char.is_dead():
                continue

            # Check if character is within heal radius
            if self.is_in_heal_range(char.x, char.y):
                # Only count if actually damaged
                if char.health < char.max_health:
                    char.health = char.max_health
                    healed_count += 1

        # Only charge if we actually healed someone
        if healed_count > 0:
            self.team.spend_money(self.HEAL_COST)
            self.has_healed_this_turn = True

        return healed_count

    def is_in_heal_range(self, tile_x, tile_y):
        """
        Checks if a tile is within the hospital's heal radius.

        Args:
            tile_x (int): The x-coordinate to check.
            tile_y (int): The y-coordinate to check.

        Returns:
            bool: True if the tile is within the heal radius.
        """
        dist_x = abs(tile_x - self.x)
        dist_y = abs(tile_y - self.y)
        return max(dist_x, dist_y) <= self.current_heal_radius

    def get_heal_tiles(self):
        """
        Returns a list of all tiles within the hospital's heal radius.

        Returns:
            list: List of (x, y) tuples for tiles in the heal area.
        """
        tiles = []
        radius = self.current_heal_radius
        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                tiles.append((self.x + dx, self.y + dy))
        return tiles

    def draw_placeholder(self, surface, screen_x, screen_y, tile_size, font=None):
        """
        Draws a placeholder 'H' for the hospital.

        Args:
            surface: The pygame surface to draw on.
            screen_x: Screen x-coordinate.
            screen_y: Screen y-coordinate.
            tile_size: Size of a tile in pixels.
            font: Optional pygame font to use.
        """
        # Draw a background circle in team color with green tint for healing
        center_x = screen_x + tile_size // 2
        center_y = screen_y + tile_size // 2
        radius = tile_size // 2 - 2

        # Mix team color with green for healing theme
        team_color = self.team.color
        heal_color = (
            min(255, team_color[0] // 2),
            min(255, (team_color[1] + 150) // 2),
            min(255, team_color[2] // 2),
        )

        # Draw filled circle with heal color
        pygame.draw.circle(surface, heal_color, (center_x, center_y), radius)
        pygame.draw.circle(surface, self.team.color, (center_x, center_y), radius, 3)

        # If upgraded, draw a golden ring
        if self.is_upgraded:
            pygame.draw.circle(
                surface, (255, 215, 0), (center_x, center_y), radius + 2, 2
            )

        # Draw the 'H' letter (or 'H+' if upgraded)
        if font is None:
            font = pygame.font.Font(None, tile_size)

        text_color = (255, 255, 255)  # White text
        text = "H+" if self.is_upgraded else "H"
        text_surf = font.render(text, True, text_color)
        text_rect = text_surf.get_rect(center=(center_x, center_y))
        surface.blit(text_surf, text_rect)

    def __repr__(self):
        upgrade_str = " [UPGRADED 9x9]" if self.is_upgraded else ""
        return f"Hospital(id={self.id}, team={self.team.name}, pos=({self.x},{self.y}), healed_this_turn={self.has_healed_this_turn}{upgrade_str})"
