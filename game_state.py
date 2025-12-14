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
        self.game_over = False
        self.winner = None  # "player" or "enemy"

    def end_turn(self):
        """
        Advances the turn based on the current phase.
        Player turn -> Enemy turn -> Next round (increment turn count) -> Player turn
        """
        if self.game_over:
            return

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

    def set_game_over(self, winner):
        """
        Sets the game as over with the specified winner.

        Args:
            winner (str): Either "player" or "enemy"
        """
        self.game_over = True
        self.winner = winner

    def player_wins(self):
        """Returns True if the player won the game."""
        return self.game_over and self.winner == "player"

    def enemy_wins(self):
        """Returns True if the enemy won the game."""
        return self.game_over and self.winner == "enemy"
