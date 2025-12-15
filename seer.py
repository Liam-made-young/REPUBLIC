import random

import pygame


class Seer:
    """
    An automated scout unit that explores fog of war.
    Seers move automatically towards unexplored areas.
    """

    # Seer constants
    VISIBILITY_RANGE = 11  # 23x23 visibility (11 tiles in each direction, ~1.5x of 7)
    MOVEMENT_RANGE = 0  # Seers don't move - they're stationary watchtowers
    MOVES_PER_TURN = 0  # No moves per turn
    COST = 8  # Money cost to spawn a seer

    # Class variable to track unique IDs
    _next_id = 0

    def __init__(self, x, y, team):
        """
        Initializes a Seer.

        Args:
            x (int): The initial x-coordinate (tile) of the seer.
            y (int): The initial y-coordinate (tile) of the seer.
            team: The Team object this seer belongs to.
        """
        # Assign unique ID
        self.id = Seer._next_id
        Seer._next_id += 1

        self.x = x
        self.y = y
        self.team = team

        # Sprite
        self.sprite = None

        # Movement tracking
        self.moves_remaining = 0  # Moves left this turn
        self.has_acted_this_turn = False

    def set_sprite(self, sprite):
        """
        Sets the seer's sprite.

        Args:
            sprite: The pygame surface to use as the seer's sprite.
        """
        self.sprite = sprite

    def get_display_sprite(self):
        """Returns the sprite for display."""
        return self.sprite

    def reset_turn(self):
        """Resets the seer for a new turn."""
        # Seers are stationary - they don't move
        self.moves_remaining = 0
        self.has_acted_this_turn = True  # Already "acted" by providing visibility

    def can_act(self):
        """Returns True if the seer can still move this turn. Seers are stationary."""
        return False  # Seers don't move

    def perform_auto_move(
        self,
        world,
        team,
        all_characters,
        all_capitals,
        all_seers,
        all_hospitals,
        map_width,
        map_height,
    ):
        """
        Seers are stationary watchtowers - they don't move.
        Their value comes from their large 15x15 visibility range.

        Returns:
            bool: Always False - seers don't move.
        """
        # Seers are stationary - they provide visibility but don't move
        return False

    def _find_best_fog_move(
        self,
        world,
        team,
        all_characters,
        all_capitals,
        all_seers,
        all_hospitals,
        map_width,
        map_height,
    ):
        """
        Finds the best move that leads towards unexplored fog.

        Returns:
            tuple or None: (x, y) of best move, or None if no good move found.
        """
        valid_moves = self._get_valid_moves(
            world,
            all_characters,
            all_capitals,
            all_seers,
            all_hospitals,
            map_width,
            map_height,
        )

        if not valid_moves:
            return None

        # Score each move by how much fog it would reveal
        best_score = -1
        best_moves = []

        for move_x, move_y in valid_moves:
            fog_score = self._count_fog_tiles_in_range(
                move_x, move_y, team, map_width, map_height
            )

            if fog_score > best_score:
                best_score = fog_score
                best_moves = [(move_x, move_y)]
            elif fog_score == best_score:
                best_moves.append((move_x, move_y))

        # If we found moves that reveal fog, pick one randomly
        if best_score > 0 and best_moves:
            return random.choice(best_moves)

        return None

    def _find_random_move(
        self,
        world,
        all_characters,
        all_capitals,
        all_seers,
        all_hospitals,
        map_width,
        map_height,
    ):
        """
        Finds a random valid move.

        Returns:
            tuple or None: (x, y) of a random valid move, or None if none available.
        """
        valid_moves = self._get_valid_moves(
            world,
            all_characters,
            all_capitals,
            all_seers,
            all_hospitals,
            map_width,
            map_height,
        )

        if valid_moves:
            return random.choice(valid_moves)

        return None

    def _get_valid_moves(
        self,
        world,
        all_characters,
        all_capitals,
        all_seers,
        all_hospitals,
        map_width,
        map_height,
    ):
        """
        Gets all valid moves within movement range.

        Returns:
            list: List of (x, y) tuples for valid move positions.
        """
        valid_moves = []

        for dx in range(-self.MOVEMENT_RANGE, self.MOVEMENT_RANGE + 1):
            for dy in range(-self.MOVEMENT_RANGE, self.MOVEMENT_RANGE + 1):
                if dx == 0 and dy == 0:
                    continue

                # Check Chebyshev distance
                if max(abs(dx), abs(dy)) > self.MOVEMENT_RANGE:
                    continue

                new_x = self.x + dx
                new_y = self.y + dy

                if self._is_valid_position(
                    new_x,
                    new_y,
                    world,
                    all_characters,
                    all_capitals,
                    all_seers,
                    all_hospitals,
                    map_width,
                    map_height,
                ):
                    valid_moves.append((new_x, new_y))

        return valid_moves

    def _is_valid_position(
        self,
        x,
        y,
        world,
        all_characters,
        all_capitals,
        all_seers,
        all_hospitals,
        map_width,
        map_height,
    ):
        """
        Checks if a position is valid for the seer to move to.

        Returns:
            bool: True if valid, False otherwise.
        """
        # Check bounds
        if not (0 <= x < map_width and 0 <= y < map_height):
            return False

        # Check terrain (no water)
        tile = world.world_map[y][x]
        if tile == "water":
            return False

        # Check for character collision
        for char in all_characters:
            if hasattr(char, "is_dead") and char.is_dead():
                continue
            if char.x == x and char.y == y:
                return False

        # Check for capital collision
        for capital in all_capitals:
            if capital.x == x and capital.y == y:
                return False

        # Check for other seers collision
        for seer in all_seers:
            if seer.id != self.id and seer.x == x and seer.y == y:
                return False

        # Check for hospital collision
        for hospital in all_hospitals:
            if hospital.x == x and hospital.y == y:
                return False

        return True

    def _count_fog_tiles_in_range(self, x, y, team, map_width, map_height):
        """
        Counts how many fog (unrevealed) tiles would be visible from a position.

        Returns:
            int: Number of fog tiles that would be revealed.
        """
        fog_count = 0

        for dx in range(-self.VISIBILITY_RANGE, self.VISIBILITY_RANGE + 1):
            for dy in range(-self.VISIBILITY_RANGE, self.VISIBILITY_RANGE + 1):
                check_x = x + dx
                check_y = y + dy

                # Check bounds
                if not (0 <= check_x < map_width and 0 <= check_y < map_height):
                    continue

                # Check if this tile is currently fog (not revealed)
                if not team.is_tile_revealed(check_x, check_y):
                    fog_count += 1

        return fog_count

    def get_team_color(self):
        """Returns the team's RGB color for glow effects."""
        return self.team.color

    def get_team_light_color(self):
        """Returns the team's light color for highlights."""
        return self.team.light_color

    def __repr__(self):
        return f"Seer(id={self.id}, team={self.team.name}, pos=({self.x},{self.y}), moves_left={self.moves_remaining})"
