from enum import Enum, auto

from team import TeamSide


class TurnPhase(Enum):
    """Represents whose turn it currently is (supports 2-4 players)."""

    PLAYER_1_TURN = auto()
    PLAYER_2_TURN = auto()
    PLAYER_3_TURN = auto()
    PLAYER_4_TURN = auto()


# Mapping from turn phase to team side
PHASE_TO_SIDE = {
    TurnPhase.PLAYER_1_TURN: TeamSide.PLAYER_1,
    TurnPhase.PLAYER_2_TURN: TeamSide.PLAYER_2,
    TurnPhase.PLAYER_3_TURN: TeamSide.PLAYER_3,
    TurnPhase.PLAYER_4_TURN: TeamSide.PLAYER_4,
}

# Ordered list of turn phases
TURN_ORDER = [
    TurnPhase.PLAYER_1_TURN,
    TurnPhase.PLAYER_2_TURN,
    TurnPhase.PLAYER_3_TURN,
    TurnPhase.PLAYER_4_TURN,
]


class GameState:
    """Holds the current state of the game, including teams, turns, and win conditions."""

    def __init__(self, num_players=2):
        """
        Initializes the game state.

        Args:
            num_players: Number of players (2-4)
        """
        self.num_players = max(2, min(4, num_players))
        self.turn_count = 1
        self.current_phase = TurnPhase.PLAYER_1_TURN
        self.game_over = False
        self.winner = None  # TeamSide of winner

        # Track selected character for multi-character control
        self.selected_character = None

        # UI state
        self.show_creation_menu = False
        self.show_character_menu = False
        self.selected_capital = None  # Capital being interacted with

    def get_current_team_side(self):
        """Returns the TeamSide of the team whose turn it is."""
        return PHASE_TO_SIDE.get(self.current_phase, TeamSide.PLAYER_1)

    def get_current_player_index(self):
        """Returns the index (0-based) of the current player."""
        for i, phase in enumerate(TURN_ORDER):
            if phase == self.current_phase:
                return i
        return 0

    def is_player_turn(self, player_index):
        """Returns True if it's the specified player's turn (0-based index)."""
        if player_index < 0 or player_index >= self.num_players:
            return False
        return self.current_phase == TURN_ORDER[player_index]

    def end_turn(self, teams):
        """
        Advances the turn to the next player, skipping defeated players.

        Args:
            teams: List of Team objects
        """
        if self.game_over:
            return

        # Reset selected character
        self.selected_character = None

        # Close any open menus
        self.show_creation_menu = False
        self.show_character_menu = False
        self.selected_capital = None

        # Find current player index
        current_index = self.get_current_player_index()

        # Find next alive player (skip defeated players)
        next_index = self._find_next_alive_player(current_index, teams)

        if next_index is None:
            # No alive players left (shouldn't happen if victory check works)
            return

        # Check if we wrapped around (new turn)
        if next_index <= current_index:
            self.turn_count += 1

        # Set the new phase
        self.current_phase = TURN_ORDER[next_index]

        # Reset the new current team's characters and capitals
        if next_index < len(teams):
            self._reset_team_for_turn(teams[next_index])
            # Generate mine income at the start of turn
            self._generate_turn_income(teams[next_index])

    def _find_next_alive_player(self, current_index, teams):
        """
        Finds the next player who is still alive (not defeated).

        Args:
            current_index: Current player index.
            teams: List of Team objects.

        Returns:
            int or None: Index of next alive player, or None if none found.
        """
        checked = 0
        next_index = (current_index + 1) % self.num_players

        while checked < self.num_players:
            if next_index < len(teams) and not teams[next_index].is_defeated():
                return next_index
            next_index = (next_index + 1) % self.num_players
            checked += 1

        return None

    def _generate_turn_income(self, team):
        """
        Generates income from mines at the start of a team's turn.

        Args:
            team: The Team object to generate income for.
        """
        if hasattr(team, "mines") and team.mines:
            income = team.generate_mine_income()
            if income > 0:
                print(f"{team.name} earned {income} gold from mines")

        if hasattr(team, "capitals") and team.capitals:
            cap_income = 0
            for capital in team.capitals:
                cap_income += capital.generate_income()
            
            if cap_income > 0:
                print(f"{team.name} earned {cap_income} gold from capitals")

    def _reset_team_for_turn(self, team):
        """Resets all turn-specific state for a team at the start of their turn."""
        # Reset all characters
        for character in team.characters:
            character.reset_turn()

        # Reset all capitals
        for capital in team.capitals:
            capital.reset_turn()

        # Reset all seers
        if hasattr(team, "seers"):
            team.reset_seers_for_turn()

        # Reset all hospitals
        if hasattr(team, "hospitals"):
            team.reset_hospitals_for_turn()

        # Reset all mines
        if hasattr(team, "mines"):
            team.reset_mines_for_turn()

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
            winner_side: TeamSide of the winning team
        """
        self.game_over = True
        self.winner = winner_side

    def check_victory_conditions(self, teams):
        """
        Checks if any team has won the game.
        A team wins when all other teams have been defeated.
        A team is defeated when they have no capitals and no characters.

        Args:
            teams: List of Team objects
        """
        if self.game_over:
            return

        # Count surviving teams
        surviving_teams = [team for team in teams if not team.is_defeated()]

        # If only one team remains, they win
        if len(surviving_teams) == 1:
            self.set_game_over(surviving_teams[0].side)
        elif len(surviving_teams) == 0:
            # Edge case: everyone defeated (shouldn't happen normally)
            # Last team to act "wins"
            self.game_over = True

    def get_winner_name(self, teams):
        """
        Returns the display name of the winner, or None if no winner.

        Args:
            teams: List of Team objects to look up winner name
        """
        if not self.winner:
            return None

        for team in teams:
            if team.side == self.winner:
                return team.name
        return None

    def get_current_phase_name(self, teams):
        """
        Returns a display-friendly name for the current phase.

        Args:
            teams: List of Team objects to get team name
        """
        current_index = self.get_current_player_index()
        if current_index < len(teams):
            return f"{teams[current_index].name}'s Turn"
        return "Unknown Turn"

    def get_current_team(self, teams):
        """
        Returns the Team object for the current player.

        Args:
            teams: List of Team objects

        Returns:
            Team: The current team, or None if index out of range
        """
        current_index = self.get_current_player_index()
        if current_index < len(teams):
            return teams[current_index]
        return None

    def __repr__(self):
        phase_name = self.current_phase.name if self.current_phase else "UNKNOWN"
        return f"GameState(turn={self.turn_count}, phase={phase_name}, players={self.num_players}, game_over={self.game_over})"
