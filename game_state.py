from enum import Enum, auto


class TurnPhase(Enum):
    """Represents whose turn it currently is."""

    PLAYER_TURN = auto()
    ENEMY_TURN = auto()


class GameState:
    """Holds the current state of the game, such as turn count and turn phase."""

    def __init__(self):
        self.turn_count = 1
        self.player_has_moved = False
        self.enemy_has_moved = False
        self.current_phase = TurnPhase.PLAYER_TURN

    def end_turn(self):
        """
        Advances the turn based on the current phase.
        Player turn -> Enemy turn -> Next round (increment turn count) -> Player turn
        """
        if self.current_phase == TurnPhase.PLAYER_TURN:
            # Player's turn ends, enemy's turn begins
            self.current_phase = TurnPhase.ENEMY_TURN
            self.enemy_has_moved = False
        else:
            # Enemy's turn ends, new round begins with player's turn
            self.current_phase = TurnPhase.PLAYER_TURN
            self.turn_count += 1
            self.player_has_moved = False

    def is_player_turn(self):
        """Returns True if it's currently the player's turn."""
        return self.current_phase == TurnPhase.PLAYER_TURN

    def is_enemy_turn(self):
        """Returns True if it's currently the enemy's turn."""
        return self.current_phase == TurnPhase.ENEMY_TURN
