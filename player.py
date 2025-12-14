class Player:
    """Represents the player character in the game."""

    def __init__(self, start_x, start_y):
        """
        Initializes the Player.

        Args:
            start_x (int): The initial x-coordinate (tile) of the player.
            start_y (int): The initial y-coordinate (tile) of the player.
        """
        self.x = start_x
        self.y = start_y
        self.sprite = None  # The player's visual sprite, to be loaded separately.

    def move(self, new_x, new_y):
        """
        Moves the player to a new tile coordinate.

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
