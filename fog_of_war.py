import pygame


class FogOfWar:
    """Manages fog of war visibility for teams."""

    # Visibility constants
    CAPITAL_VISIBILITY_RADIUS = 3  # 7x7 area around capitals
    CHARACTER_VISIBILITY_RADIUS = 2  # 5x5 area around characters

    def __init__(self, map_width, map_height):
        """
        Initializes the fog of war system.

        Args:
            map_width (int): Width of the map in tiles.
            map_height (int): Height of the map in tiles.
        """
        self.map_width = map_width
        self.map_height = map_height
        self.fog_tile_surface = None  # Cached fog tile

    def create_fog_tile(self, grass_texture, tile_size):
        """
        Creates a fog tile based on a whitened version of the grass texture.

        Args:
            grass_texture: The original grass texture surface.
            tile_size: Size to scale the tile to.

        Returns:
            pygame.Surface: A white-filtered version of grass.
        """
        # Scale the texture first
        scaled = pygame.transform.scale(grass_texture, (tile_size, tile_size))

        # Create a copy to modify
        fog_surf = scaled.copy()

        # Apply white filter
        fog_surf.lock()

        width, height = fog_surf.get_size()

        for x in range(width):
            for y in range(height):
                color = fog_surf.get_at((x, y))

                # Calculate luminance
                luminance = color.r * 0.299 + color.g * 0.587 + color.b * 0.114

                # Blend towards white/gray
                white_blend = 0.7  # How much to blend towards white
                gray_value = int(luminance * 0.3 + 180)  # Light gray base

                new_r = int(color.r * (1 - white_blend) + gray_value * white_blend)
                new_g = int(color.g * (1 - white_blend) + gray_value * white_blend)
                new_b = int(color.b * (1 - white_blend) + gray_value * white_blend)

                # Clamp values
                new_r = max(0, min(255, new_r))
                new_g = max(0, min(255, new_g))
                new_b = max(0, min(255, new_b))

                fog_surf.set_at(
                    (x, y),
                    (new_r, new_g, new_b, color.a if hasattr(color, "a") else 255),
                )

        fog_surf.unlock()
        self.fog_tile_surface = fog_surf
        return fog_surf

    def update_team_visibility(self, team):
        """
        Updates the revealed tiles for a team based on their capitals and characters.

        Args:
            team: The Team object to update visibility for.
        """
        # Reveal around capitals
        for capital in team.capitals:
            team.reveal_area(capital.x, capital.y, self.CAPITAL_VISIBILITY_RADIUS)

        # Reveal around living characters
        for character in team.get_living_characters():
            team.reveal_area(character.x, character.y, self.CHARACTER_VISIBILITY_RADIUS)

    def is_visible_to_team(self, tile_x, tile_y, team):
        """
        Checks if a tile is visible to a team.

        Args:
            tile_x (int): X coordinate of the tile.
            tile_y (int): Y coordinate of the tile.
            team: The Team to check visibility for.

        Returns:
            bool: True if the tile is visible to the team.
        """
        return team.is_tile_revealed(tile_x, tile_y)

    def get_fog_surface(self):
        """
        Returns the cached fog tile surface.

        Returns:
            pygame.Surface: The fog tile, or None if not created.
        """
        return self.fog_tile_surface

    @staticmethod
    def calculate_revealed_tiles(center_x, center_y, radius):
        """
        Calculates all tiles that would be revealed from a center point.

        Args:
            center_x (int): X coordinate of the center.
            center_y (int): Y coordinate of the center.
            radius (int): Radius of visibility.

        Returns:
            set: Set of (x, y) tuples for revealed tiles.
        """
        tiles = set()
        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                tiles.add((center_x + dx, center_y + dy))
        return tiles

    def __repr__(self):
        return f"FogOfWar(map_size={self.map_width}x{self.map_height})"
