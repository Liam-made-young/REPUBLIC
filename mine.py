"""
Mine building for REPUBLIC.

Mines can only be placed on granite tiles and generate gold per turn for the owning team.
Can be upgraded to double the gold income (from 1 to 2 gold per turn).
"""

import pygame


class Mine:
    """
    A building that generates gold each turn.
    Can only be placed on granite tiles.
    Can be upgraded for 10 gold to double income (1 -> 2 gold per turn).
    """

    # Mine constants
    BUILD_COST = 6  # Gold cost to build a mine
    INCOME_PER_TURN = 1  # Gold generated per turn (base)
    UPGRADED_INCOME_PER_TURN = 2  # Gold generated per turn when upgraded
    UPGRADE_COST = 10  # Gold cost to upgrade
    VALID_TERRAIN = "granite"  # Can only be placed on granite

    # Class variable to track unique IDs
    _next_id = 0

    def __init__(self, x, y, team):
        """
        Initializes a Mine.

        Args:
            x (int): The x-coordinate (tile) of the mine.
            y (int): The y-coordinate (tile) of the mine.
            team: The Team object this mine belongs to.
        """
        # Assign unique ID
        self.id = Mine._next_id
        Mine._next_id += 1

        self.x = x
        self.y = y
        self.team = team
        self.has_generated_this_turn = False

        # Upgrade state
        self.is_upgraded = False

    @property
    def current_income(self):
        """Returns the current income based on upgrade status."""
        return (
            self.UPGRADED_INCOME_PER_TURN if self.is_upgraded else self.INCOME_PER_TURN
        )

    def reset_turn(self):
        """Resets turn-specific state."""
        self.has_generated_this_turn = False

    def can_upgrade(self):
        """
        Checks if this mine can be upgraded.

        Returns:
            bool: True if not already upgraded and team can afford it.
        """
        return not self.is_upgraded and self.team.can_afford(self.UPGRADE_COST)

    def upgrade(self):
        """
        Upgrades this mine (doubles gold income).

        Returns:
            bool: True if upgrade was successful.
        """
        if not self.can_upgrade():
            return False

        self.team.spend_money(self.UPGRADE_COST)
        self.is_upgraded = True
        print(
            f"Mine at ({self.x}, {self.y}) upgraded! Income doubled to {self.current_income} gold/turn."
        )
        return True

    def generate_income(self):
        """
        Generates income for the owning team.

        Returns:
            int: Amount of gold generated (0 if already generated this turn).
        """
        if self.has_generated_this_turn:
            return 0

        self.has_generated_this_turn = True
        income = self.current_income
        self.team.add_money(income)
        return income

    @staticmethod
    def is_valid_position(x, y, world_map, all_entities):
        """
        Checks if a position is valid for placing a mine.
        Must be on granite and not occupied.

        Args:
            x (int): The x-coordinate to check.
            y (int): The y-coordinate to check.
            world_map: The 2D array of tile types.
            all_entities: Dict with lists of entities to check for occupation.
                         Expected keys: 'characters', 'capitals', 'hospitals', 'mines', 'seers'

        Returns:
            bool: True if the position is valid for a mine.
        """
        # Check if tile is granite
        try:
            tile_type = world_map[y][x]
            if tile_type != Mine.VALID_TERRAIN:
                return False
        except (IndexError, TypeError):
            return False

        # Check if position is occupied by any entity
        for entity_type, entities in all_entities.items():
            for entity in entities:
                if hasattr(entity, "x") and hasattr(entity, "y"):
                    if entity.x == x and entity.y == y:
                        # For characters, skip dead ones
                        if hasattr(entity, "is_dead") and entity.is_dead():
                            continue
                        return False

        return True

    def draw_placeholder(self, surface, screen_x, screen_y, tile_size, font=None):
        """
        Draws a placeholder 'M' for the mine.

        Args:
            surface: The pygame surface to draw on.
            screen_x: Screen x-coordinate.
            screen_y: Screen y-coordinate.
            tile_size: Size of a tile in pixels.
            font: Optional pygame font to use.
        """
        # Draw a background square in team color with brownish tint for mining
        center_x = screen_x + tile_size // 2
        center_y = screen_y + tile_size // 2

        # Create a rect for the mine (slightly smaller than tile)
        padding = 2
        mine_rect = pygame.Rect(
            screen_x + padding,
            screen_y + padding,
            tile_size - padding * 2,
            tile_size - padding * 2,
        )

        # Mix team color with brown for mining theme
        team_color = self.team.color
        mine_color = (
            min(255, (team_color[0] + 139) // 2),  # Mix with brown
            min(255, (team_color[1] + 90) // 2),
            min(255, (team_color[2] + 43) // 2),
        )

        # Draw filled rect with mine color
        pygame.draw.rect(surface, mine_color, mine_rect, border_radius=4)
        pygame.draw.rect(surface, self.team.color, mine_rect, 3, border_radius=4)

        # If upgraded, draw a golden border
        if self.is_upgraded:
            inner_rect = pygame.Rect(
                screen_x + padding + 2,
                screen_y + padding + 2,
                tile_size - padding * 2 - 4,
                tile_size - padding * 2 - 4,
            )
            pygame.draw.rect(surface, (255, 215, 0), inner_rect, 2, border_radius=3)

        # Draw the 'M' letter (or 'M+' if upgraded)
        if font is None:
            font = pygame.font.Font(None, tile_size)

        text_color = (255, 215, 0)  # Gold text to indicate income
        text = "M+" if self.is_upgraded else "M"
        text_surf = font.render(text, True, text_color)
        text_rect = text_surf.get_rect(center=(center_x, center_y))
        surface.blit(text_surf, text_rect)

    def __repr__(self):
        upgrade_str = " [UPGRADED x2]" if self.is_upgraded else ""
        return f"Mine(id={self.id}, team={self.team.name}, pos=({self.x},{self.y}), income={self.current_income}/turn{upgrade_str})"
