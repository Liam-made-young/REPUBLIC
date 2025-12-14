from enum import Enum, auto

from team import TeamSide


class TurnPhase(Enum):
    """Represents whose turn it currently is."""

    RED_TURN = auto()
    BLUE_TURN = auto()


class GameState:
    """Holds the current state of the game, including teams, turns, and win conditions."""

    def __init__(self):
        self.turn_count = 1
        self.current_phase = TurnPhase.RED_TURN
        self.game_over = False
        self.winner = None  # TeamSide.RED or TeamSide.BLUE

        # Track selected character for multi-character control
        self.selected_character = None

        # UI state
        self.show_creation_menu = False
        self.show_character_menu = False
        self.selected_capital = None  # Capital being interacted with

    def get_current_team_side(self):
        """Returns the TeamSide of the team whose turn it is."""
        if self.current_phase == TurnPhase.RED_TURN:
            return TeamSide.RED
        else:
            return TeamSide.BLUE

    def get_opposing_team_side(self):
        """Returns the TeamSide of the opposing team."""
        if self.current_phase == TurnPhase.RED_TURN:
            return TeamSide.BLUE
        else:
            return TeamSide.RED

    def is_red_turn(self):
        """Returns True if it's currently the red team's turn."""
        return self.current_phase == TurnPhase.RED_TURN

    def is_blue_turn(self):
        """Returns True if it's currently the blue team's turn."""
        return self.current_phase == TurnPhase.BLUE_TURN

    def end_turn(self, red_team, blue_team):
        """
        Advances the turn to the next team.

        Args:
            red_team: The red Team object
            blue_team: The blue Team object
        """
        if self.game_over:
            return

        # Reset selected character
        self.selected_character = None

        # Close any open menus
        self.show_creation_menu = False
        self.show_character_menu = False
        self.selected_capital = None

        if self.current_phase == TurnPhase.RED_TURN:
            # Red's turn ends, blue's turn begins
            self.current_phase = TurnPhase.BLUE_TURN
            # Reset blue team's characters and capitals for their turn
            self._reset_team_for_turn(blue_team)
        else:
            # Blue's turn ends, new round begins with red's turn
            self.current_phase = TurnPhase.RED_TURN
            self.turn_count += 1
            # Reset red team's characters and capitals for their turn
            self._reset_team_for_turn(red_team)

    def _reset_team_for_turn(self, team):
        """Resets all turn-specific state for a team at the start of their turn."""
        # Reset all characters
        for character in team.characters:
            character.reset_turn()

        # Reset all capitals
        for capital in team.capitals:
            capital.reset_turn()

    def select_character(self, character):
        """
        Selects a character for the current player to control.

        Args:
            character: The Character to select, or None to deselect.
        """
        self.selected_character = character

    def deselect_character(self):
        """Deselects the currently selected character."""
        self.selected_character = None

    def has_selected_character(self):
        """Returns True if a character is currently selected."""
        return self.selected_character is not None

    def toggle_creation_menu(self):
        """Toggles the capital creation menu visibility."""
        self.show_creation_menu = not self.show_creation_menu
        if self.show_creation_menu:
            self.show_character_menu = False
            self.selected_capital = None

    def open_character_menu(self, capital):
        """
        Opens the character creation menu for a specific capital.

        Args:
            capital: The Capital to spawn characters from.
        """
        self.show_character_menu = True
        self.selected_capital = capital
        self.show_creation_menu = False

    def close_character_menu(self):
        """Closes the character creation menu."""
        self.show_character_menu = False
        self.selected_capital = None

    def close_all_menus(self):
        """Closes all open menus."""
        self.show_creation_menu = False
        self.show_character_menu = False
        self.selected_capital = None

    def set_game_over(self, winner_side):
        """
        Sets the game as over with the specified winner.

        Args:
            winner_side: TeamSide.RED or TeamSide.BLUE
        """
        self.game_over = True
        self.winner = winner_side

    def red_wins(self):
        """Returns True if the red team won the game."""
        return self.game_over and self.winner == TeamSide.RED

    def blue_wins(self):
        """Returns True if the blue team won the game."""
        return self.game_over and self.winner == TeamSide.BLUE

    def check_victory_conditions(self, red_team, blue_team):
        """
        Checks if either team has won the game.
        A team wins when the opposing team has no capitals and no characters.

        Args:
            red_team: The red Team object
            blue_team: The blue Team object
        """
        if self.game_over:
            return

        if red_team.is_defeated():
            self.set_game_over(TeamSide.BLUE)
        elif blue_team.is_defeated():
            self.set_game_over(TeamSide.RED)

    def get_winner_name(self):
        """Returns the display name of the winner, or None if no winner."""
        if self.winner == TeamSide.RED:
            return "Red"
        elif self.winner == TeamSide.BLUE:
            return "Blue"
        return None

    def get_current_phase_name(self):
        """Returns a display-friendly name for the current phase."""
        if self.current_phase == TurnPhase.RED_TURN:
            return "Red Team's Turn"
        else:
            return "Blue Team's Turn"

    def __repr__(self):
        phase = "RED" if self.is_red_turn() else "BLUE"
        return f"GameState(turn={self.turn_count}, phase={phase}, game_over={self.game_over})"
