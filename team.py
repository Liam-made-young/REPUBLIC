from enum import Enum, auto


class TeamSide(Enum):
    """Represents the team sides in the game (supports 2-4 players)."""

    PLAYER_1 = auto()
    PLAYER_2 = auto()
    PLAYER_3 = auto()
    PLAYER_4 = auto()


# Default color data for backwards compatibility
DEFAULT_COLORS = {
    TeamSide.PLAYER_1: {
        "name": "Red",
        "color_key": "red",
        "rgb": (200, 50, 50),
        "light": (255, 100, 100),
        "dark": (120, 30, 30),
    },
    TeamSide.PLAYER_2: {
        "name": "Blue",
        "color_key": "blue",
        "rgb": (50, 100, 200),
        "light": (100, 150, 255),
        "dark": (30, 60, 120),
    },
    TeamSide.PLAYER_3: {
        "name": "Green",
        "color_key": "green",
        "rgb": (50, 180, 50),
        "light": (100, 220, 100),
        "dark": (30, 100, 30),
    },
    TeamSide.PLAYER_4: {
        "name": "Purple",
        "color_key": "purple",
        "rgb": (150, 50, 180),
        "light": (200, 100, 220),
        "dark": (90, 30, 110),
    },
}


class Team:
    """Manages a team's resources and state."""

    def __init__(
        self, side: TeamSide, player_name=None, color_key=None, color_data=None
    ):
        """
        Initializes a team.

        Args:
            side: The team side (PLAYER_1, PLAYER_2, etc.)
            player_name: Optional custom player name (e.g., "Samuel")
            color_key: The color key (e.g., "red", "blue", "green", "purple")
            color_data: Optional dict with "rgb", "light", "dark" color tuples
        """
        self.side = side
        self.money = 0
        self.characters = []  # List of Character objects
        self.capitals = []  # List of Capital objects
        self.seers = []  # List of Seer objects
        self.hospitals = []  # List of Hospital objects
        self.mines = []  # List of Mine objects
        self.revealed_tiles = set()  # Set of (x, y) tuples for fog of war

        # Set up player name
        if player_name:
            self._player_name = player_name
        else:
            self._player_name = DEFAULT_COLORS.get(
                side, DEFAULT_COLORS[TeamSide.PLAYER_1]
            )["name"]

        # Set up colors
        if color_key:
            self._color_key = color_key
        else:
            self._color_key = DEFAULT_COLORS.get(
                side, DEFAULT_COLORS[TeamSide.PLAYER_1]
            )["color_key"]

        if color_data:
            self._color = color_data.get("rgb", (200, 50, 50))
            self._light_color = color_data.get("light", (255, 100, 100))
            self._dark_color = color_data.get("dark", (120, 30, 30))
        else:
            default = DEFAULT_COLORS.get(side, DEFAULT_COLORS[TeamSide.PLAYER_1])
            self._color = default["rgb"]
            self._light_color = default["light"]
            self._dark_color = default["dark"]

    @property
    def name(self):
        """Returns the display name of the team (player name)."""
        return self._player_name

    @property
    def color_key(self):
        """Returns the color key (e.g., 'red', 'blue')."""
        return self._color_key

    @property
    def color(self):
        """Returns the RGB color tuple for the team."""
        return self._color

    @property
    def light_color(self):
        """Returns a lighter version of the team color for glows."""
        return self._light_color

    @property
    def dark_color(self):
        """Returns a darker version of the team color for UI elements."""
        return self._dark_color

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

    def add_seer(self, seer):
        """Adds a seer to the team."""
        self.seers.append(seer)

    def remove_seer(self, seer):
        """Removes a seer from the team."""
        if seer in self.seers:
            self.seers.remove(seer)

    def add_hospital(self, hospital):
        """Adds a hospital to the team."""
        self.hospitals.append(hospital)

    def remove_hospital(self, hospital):
        """Removes a hospital from the team."""
        if hospital in self.hospitals:
            self.hospitals.remove(hospital)

    def add_mine(self, mine):
        """Adds a mine to the team."""
        self.mines.append(mine)

    def remove_mine(self, mine):
        """Removes a mine from the team."""
        if mine in self.mines:
            self.mines.remove(mine)

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

    def reset_seers_for_turn(self):
        """Resets all seers for a new turn."""
        for seer in self.seers:
            seer.reset_turn()

    def reset_hospitals_for_turn(self):
        """Resets all hospitals for a new turn."""
        for hospital in self.hospitals:
            hospital.reset_turn()

    def reset_mines_for_turn(self):
        """Resets all mines for a new turn."""
        for mine in self.mines:
            mine.reset_turn()

    def generate_mine_income(self):
        """
        Generates income from all mines.

        Returns:
            int: Total gold generated from mines.
        """
        total = 0
        for mine in self.mines:
            total += mine.generate_income()
        return total

    def __repr__(self):
        return f"Team({self.name}, color={self._color_key}, money={self.money}, chars={len(self.characters)}, capitals={len(self.capitals)}, seers={len(self.seers)}, hospitals={len(self.hospitals)}, mines={len(self.mines)})"
