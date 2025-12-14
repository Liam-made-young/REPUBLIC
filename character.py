import pygame


class CharacterType:
    """Defines the different character types and their stats."""

    WARRIOR = "warrior"
    SWORDSMAN = "swordsman"
    SHIELDMAN = "shieldman"
    RUNNER = "runner"

    # Stats: (max_health, damage, movement_range, cost, sprite_file)
    STATS = {
        WARRIOR: {
            "max_health": 10,
            "damage": 5,
            "movement_range": 3,
            "cost": 2,
            "sprite_file": "char1.png",
        },
        SWORDSMAN: {
            "max_health": 15,
            "damage": 10,
            "movement_range": 3,
            "cost": 5,
            "sprite_file": "swordsman.png",
        },
        SHIELDMAN: {
            "max_health": 20,
            "damage": 2,
            "movement_range": 2,
            "cost": 3,
            "sprite_file": "shield.png",
        },
        RUNNER: {
            "max_health": 5,
            "damage": 5,
            "movement_range": 10,
            "cost": 5,
            "sprite_file": "runner.png",
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
        self.sprite_file = stats["sprite_file"]

        # Sprite surfaces
        self.original_sprite = None  # Original loaded sprite
        self.tinted_sprite = None  # Team-colored version
        self.has_moved = False  # Track if character moved this turn

    def set_sprite(self, sprite):
        """
        Sets the character's sprite and creates a team-tinted version.

        Args:
            sprite: The pygame surface to use as the character's sprite.
        """
        self.original_sprite = sprite
        if sprite:
            self.tinted_sprite = self._create_tinted_sprite(sprite)

    def _create_tinted_sprite(self, sprite):
        """
        Creates a hue-shifted version of the sprite based on team color.

        Args:
            sprite: The original pygame surface.

        Returns:
            pygame.Surface: A new surface with team-colored tint.
        """
        # Create a copy of the sprite
        tinted = sprite.copy()

        # Get team color for tinting
        team_color = self.team.color

        # Lock the surface for pixel access
        tinted.lock()

        width, height = tinted.get_size()

        for x in range(width):
            for y in range(height):
                color = tinted.get_at((x, y))

                # Skip fully transparent pixels
                if color.a == 0:
                    continue

                # Calculate luminance (grayscale value)
                luminance = (color.r * 0.299 + color.g * 0.587 + color.b * 0.114) / 255

                # Blend with team color based on luminance
                # Darker areas get more team color, lighter areas stay lighter
                blend_factor = 0.6  # How much team color to apply

                new_r = int(
                    color.r * (1 - blend_factor)
                    + team_color[0] * blend_factor * luminance
                    + (255 - team_color[0]) * blend_factor * (1 - luminance) * 0.3
                )
                new_g = int(
                    color.g * (1 - blend_factor)
                    + team_color[1] * blend_factor * luminance
                    + (255 - team_color[1]) * blend_factor * (1 - luminance) * 0.3
                )
                new_b = int(
                    color.b * (1 - blend_factor)
                    + team_color[2] * blend_factor * luminance
                    + (255 - team_color[2]) * blend_factor * (1 - luminance) * 0.3
                )

                # Clamp values
                new_r = max(0, min(255, new_r))
                new_g = max(0, min(255, new_g))
                new_b = max(0, min(255, new_b))

                tinted.set_at((x, y), (new_r, new_g, new_b, color.a))

        tinted.unlock()
        return tinted

    def get_display_sprite(self):
        """
        Returns the tinted sprite for display.

        Returns:
            pygame.Surface: The team-tinted sprite.
        """
        return self.tinted_sprite if self.tinted_sprite else self.original_sprite

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

    def __repr__(self):
        return f"Character(id={self.id}, type={self.char_type}, team={self.team.name}, pos=({self.x},{self.y}), hp={self.health}/{self.max_health})"
