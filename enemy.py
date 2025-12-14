import pygame


class Enemy:
    """Represents an enemy character in the game."""

    def __init__(self, start_x, start_y):
        """
        Initializes the Enemy.

        Args:
            start_x (int): The initial x-coordinate (tile) of the enemy.
            start_y (int): The initial y-coordinate (tile) of the enemy.
        """
        self.x = start_x
        self.y = start_y
        self.sprite = None  # The enemy's visual sprite, to be loaded separately.
        self.inverted_sprite = None  # Cached inverted version of the sprite

    def set_sprite(self, sprite):
        """
        Sets the enemy sprite and creates an inverted version.

        Args:
            sprite: The pygame surface to use as the enemy's sprite.
        """
        self.sprite = sprite
        if sprite:
            self.inverted_sprite = self._create_inverted_sprite(sprite)

    def _create_inverted_sprite(self, sprite):
        """
        Creates an inverted (negative) version of the sprite.

        Args:
            sprite: The original pygame surface.

        Returns:
            pygame.Surface: A new surface with inverted colors.
        """
        # Create a copy of the sprite to avoid modifying the original
        inverted = sprite.copy()

        # Lock the surface for pixel access
        inverted.lock()

        # Get the size of the surface
        width, height = inverted.get_size()

        # Invert each pixel
        for x in range(width):
            for y in range(height):
                # Get the color at this pixel (including alpha)
                color = inverted.get_at((x, y))
                # Invert RGB values but keep alpha unchanged
                inverted_color = (
                    255 - color.r,
                    255 - color.g,
                    255 - color.b,
                    color.a,
                )
                inverted.set_at((x, y), inverted_color)

        inverted.unlock()
        return inverted

    def move(self, new_x, new_y):
        """
        Moves the enemy to a new tile coordinate.

        Args:
            new_x (int): The new x-coordinate.
            new_y (int): The new y-coordinate.
        """
        self.x = new_x
        self.y = new_y

    def is_valid_move(self, tile_x, tile_y, movement_range):
        """
        Checks if a move to the given tile is valid.

        Args:
            tile_x (int): The target x-coordinate.
            tile_y (int): The target y-coordinate.
            movement_range (int): The maximum allowed distance for a move.

        Returns:
            bool: True if the move is valid, False otherwise.
        """
        dist_x = abs(tile_x - self.x)
        dist_y = abs(tile_y - self.y)

        # A move is valid if it's not to the same spot (distance > 0)
        # and is within the allowed range.
        return 0 < max(dist_x, dist_y) <= movement_range

    def get_display_sprite(self):
        """
        Returns the inverted sprite for display.

        Returns:
            pygame.Surface: The inverted sprite, or the original if inversion failed.
        """
        return self.inverted_sprite if self.inverted_sprite else self.sprite
