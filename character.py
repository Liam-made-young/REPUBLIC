import pygame


class CharacterType:
    """Defines the different character types and their stats."""

    WARRIOR = "warrior"
    SWORDSMAN = "swordsman"
    SHIELDMAN = "shieldman"
    RUNNER = "runner"

    # Stats: (max_health, damage, movement_range, visibility_range, cost, sprite_prefix)
    STATS = {
        WARRIOR: {
            "max_health": 10,
            "damage": 5,
            "movement_range": 3,
            "visibility_range": 2,  # 5x5 visibility
            "cost": 2,
            "sprite_prefix": "char",
        },
        SWORDSMAN: {
            "max_health": 15,
            "damage": 10,
            "movement_range": 3,
            "visibility_range": 2,  # 5x5 visibility
            "cost": 5,
            "sprite_prefix": "sword",
        },
        SHIELDMAN: {
            "max_health": 20,
            "damage": 2,
            "movement_range": 2,
            "visibility_range": 2,  # 5x5 visibility
            "cost": 3,
            "sprite_prefix": "shield",
        },
        RUNNER: {
            "max_health": 5,
            "damage": 4,  # One less damage than others
            "movement_range": 10,
            "visibility_range": 4,  # 9x9 visibility (4 tiles in each direction)
            "cost": 5,
            "sprite_prefix": "runner",
        },
    }

    @classmethod
    def get_stats(cls, char_type):
        """Returns the stats dictionary for a character type."""
        return cls.STATS.get(char_type, cls.STATS[cls.WARRIOR])

    @classmethod
    def get_cost(cls, char_type):
        """Returns the cost to create a character of this type."""
        return cls.STATS.get(char_type, cls.STATS[cls.WARRIOR])["cost"]

    @classmethod
    def get_all_types(cls):
        """Returns a list of all character types."""
        return [cls.WARRIOR, cls.SWORDSMAN, cls.SHIELDMAN, cls.RUNNER]


class Character:
    """Represents a character unit in the game."""

    # Class variable to track unique IDs
    _next_id = 0

    def __init__(self, x, y, team, char_type=CharacterType.WARRIOR):
        """
        Initializes a character.

        Args:
            x (int): The initial x-coordinate (tile) of the character.
            y (int): The initial y-coordinate (tile) of the character.
            team: The Team object this character belongs to.
            char_type (str): The type of character (from CharacterType).
        """
        # Assign unique ID
        self.id = Character._next_id
        Character._next_id += 1

        self.x = x
        self.y = y
        self.team = team
        self.char_type = char_type

        # Get stats from character type
        stats = CharacterType.get_stats(char_type)
        self.max_health = stats["max_health"]
        self.health = self.max_health
        self.damage = stats["damage"]
        self.movement_range = stats["movement_range"]
        self.visibility_range = stats.get("visibility_range", 2)  # Default 5x5
        self.sprite_prefix = stats["sprite_prefix"]

        # Sprite surface (pre-colored, no tinting needed)
        self.sprite = None
        self.has_moved = False  # Track if character moved this turn

    def set_sprite(self, sprite):
        """
        Sets the character's sprite.
        Sprites are now pre-colored based on team color, no tinting needed.

        Args:
            sprite: The pygame surface to use as the character's sprite.
        """
        self.sprite = sprite

    def get_display_sprite(self):
        """
        Returns the sprite for display.

        Returns:
            pygame.Surface: The character's sprite.
        """
        return self.sprite

    def move(self, new_x, new_y):
        """
        Moves the character to a new tile coordinate.

        Args:
            new_x (int): The new x-coordinate.
            new_y (int): The new y-coordinate.
        """
        self.x = new_x
        self.y = new_y
        self.has_moved = True

    def is_valid_move(self, tile_x, tile_y):
        """
        Checks if a move to the given tile is valid.

        Args:
            tile_x (int): The target x-coordinate.
            tile_y (int): The target y-coordinate.

        Returns:
            bool: True if the move is valid, False otherwise.
        """
        dist_x = abs(tile_x - self.x)
        dist_y = abs(tile_y - self.y)

        # A move is valid if it's not to the same spot (distance > 0)
        # and is within the allowed range.
        return 0 < max(dist_x, dist_y) <= self.movement_range

    def is_in_range(self, tile_x, tile_y):
        """
        Checks if a tile is within attack/interaction range.

        Args:
            tile_x (int): The target x-coordinate.
            tile_y (int): The target y-coordinate.

        Returns:
            bool: True if in range, False otherwise.
        """
        dist_x = abs(tile_x - self.x)
        dist_y = abs(tile_y - self.y)
        return max(dist_x, dist_y) <= self.movement_range

    def take_damage(self, amount):
        """
        Reduces the character's health by the given amount.

        Args:
            amount (int): The amount of damage to take.
        """
        self.health = max(0, self.health - amount)

    def heal(self, amount):
        """
        Heals the character by the given amount.

        Args:
            amount (int): The amount to heal.
        """
        self.health = min(self.max_health, self.health + amount)

    def is_dead(self):
        """
        Checks if the character is dead.

        Returns:
            bool: True if the character's health is 0 or below.
        """
        return self.health <= 0

    def reset_turn(self):
        """Resets turn-specific state (called at the start of the team's turn)."""
        self.has_moved = False

    def can_act(self):
        """
        Checks if the character can still take actions this turn.

        Returns:
            bool: True if the character hasn't moved and isn't dead.
        """
        return not self.has_moved and not self.is_dead()

    def get_type_display_name(self):
        """Returns a display-friendly name for the character type."""
        return self.char_type.capitalize()

    def get_team_color(self):
        """Returns the team's RGB color for glow effects."""
        return self.team.color

    def get_team_light_color(self):
        """Returns the team's light color for highlights."""
        return self.team.light_color

    def __repr__(self):
        return f"Character(id={self.id}, type={self.char_type}, team={self.team.name}, pos=({self.x},{self.y}), hp={self.health}/{self.max_health})"
