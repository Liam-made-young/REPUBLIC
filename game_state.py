class GameState:
    """Holds the current state of the game, such as turn count."""

    def __init__(self):
        self.turn_count = 1
        self.player_has_moved = False

    def end_turn(self):
        """Advances the turn counter and resets turn-specific flags."""
        self.turn_count += 1
        self.player_has_moved = False
