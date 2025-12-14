from enum import Enum, auto


class TeamSide(Enum):
    """Represents the two team sides in the game."""

    RED = auto()
    BLUE = auto()


class Team:
    """Manages a team's resources and state."""

    def __init__(self, side: TeamSide):
        """
        Initializes a team.

        Args:
            side: The team side (RED or BLUE)
        """
        self.side = side
        self.money = 0
        self.characters = []  # List of Character objects
        self.capitals = []  # List of Capital objects
        self.revealed_tiles = set()  # Set of (x, y) tuples for fog of war

    @property
    def name(self):
        """Returns the display name of the team."""
        return "Red" if self.side == TeamSide.RED else "Blue"

    @property
    def color(self):
        """Returns the RGB color tuple for the team."""
        if self.side == TeamSide.RED:
            return (200, 50, 50)  # Red
        else:
            return (50, 100, 200)  # Blue

    @property
    def light_color(self):
        """Returns a lighter version of the team color for glows."""
        if self.side == TeamSide.RED:
            return (255, 100, 100)  # Light red
        else:
            return (100, 150, 255)  # Light blue

    @property
    def dark_color(self):
        """Returns a darker version of the team color for UI elements."""
        if self.side == TeamSide.RED:
            return (120, 30, 30)  # Dark red
        else:
            return (30, 60, 120)  # Dark blue

    def add_money(self, amount):
        """Adds money to the team's treasury."""
        self.money += amount

    def spend_money(self, amount):
        """
        Attempts to spend money from the team's treasury.

        Args:
            amount: The amount to spend

        Returns:
            bool: True if successful, False if not enough money
        """
        if self.money >= amount:
            self.money -= amount
            return True
        return False

    def can_afford(self, amount):
        """Checks if the team can afford a purchase."""
        return self.money >= amount

    def add_character(self, character):
        """Adds a character to the team."""
        self.characters.append(character)

    def remove_character(self, character):
        """Removes a character from the team."""
        if character in self.characters:
            self.characters.remove(character)

    def add_capital(self, capital):
        """Adds a capital to the team."""
        self.capitals.append(capital)

    def remove_capital(self, capital):
        """Removes a capital from the team."""
        if capital in self.capitals:
            self.capitals.remove(capital)

    def reveal_area(self, center_x, center_y, radius):
        """
        Reveals tiles in a square area around a center point.

        Args:
            center_x: X coordinate of the center
            center_y: Y coordinate of the center
            radius: Half-width of the square area (e.g., 3 for 7x7)
        """
        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                self.revealed_tiles.add((center_x + dx, center_y + dy))

    def is_tile_revealed(self, x, y):
        """Checks if a tile is revealed for this team."""
        return (x, y) in self.revealed_tiles

    def get_living_characters(self):
        """Returns a list of characters that are still alive."""
        return [c for c in self.characters if not c.is_dead()]

    def has_living_characters(self):
        """Checks if the team has any living characters."""
        return len(self.get_living_characters()) > 0

    def has_capitals(self):
        """Checks if the team has any capitals."""
        return len(self.capitals) > 0

    def is_defeated(self):
        """Checks if the team has been defeated (no capitals and no characters)."""
        return not self.has_capitals() and not self.has_living_characters()
