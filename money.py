import pygame


class Money:
    """Represents a collectible money tile on the map."""

    # Money constants
    VALUE = 1  # Amount of money each pickup gives
    SPAWN_RATIO = 10  # One money per this many tiles (1:10 ratio)

    # Class variable to track unique IDs
    _next_id = 0

    def __init__(self, x, y):
        """
        Initializes a money pickup.

        Args:
            x (int): The x-coordinate (tile) of the money.
            y (int): The y-coordinate (tile) of the money.
        """
        # Assign unique ID
        self.id = Money._next_id
        Money._next_id += 1

        self.x = x
        self.y = y
        self.collected = False
        self.glow_surface = None  # Cached glow surface

    def collect(self, team):
        """
        Collects this money for a team.

        Args:
            team: The Team object that collected the money.

        Returns:
            int: The value collected, or 0 if already collected.
        """
        if not self.collected:
            self.collected = True
            team.add_money(self.VALUE)
            return self.VALUE
        return 0

    def is_at(self, tile_x, tile_y):
        """
        Checks if this money is at the given tile position.

        Args:
            tile_x (int): The x-coordinate to check.
            tile_y (int): The y-coordinate to check.

        Returns:
            bool: True if the money is at this position.
        """
        return self.x == tile_x and self.y == tile_y and not self.collected

    @staticmethod
    def create_money_sprite(base_sand_texture, tile_size):
        """
        Creates a glowing yellow money sprite based on the sand texture.

        Args:
            base_sand_texture: The original sand texture surface.
            tile_size: Size to scale the sprite to.

        Returns:
            pygame.Surface: A yellow-tinted, high-contrast version of sand.
        """
        # Scale the texture first
        scaled = pygame.transform.scale(base_sand_texture, (tile_size, tile_size))

        # Create a copy to modify
        money_surf = scaled.copy()

        # Apply yellow tint and increase contrast
        money_surf.lock()

        width, height = money_surf.get_size()

        for x in range(width):
            for y in range(height):
                color = money_surf.get_at((x, y))

                # Calculate luminance
                luminance = (color.r * 0.299 + color.g * 0.587 + color.b * 0.114) / 255

                # Increase contrast
                contrast_factor = 1.5
                luminance = max(0, min(1, (luminance - 0.5) * contrast_factor + 0.5))

                # Apply golden yellow tint
                gold_r = 255
                gold_g = 215
                gold_b = 0

                new_r = int(gold_r * luminance + 50)
                new_g = int(gold_g * luminance + 30)
                new_b = int(gold_b * luminance * 0.3)

                # Clamp values
                new_r = max(0, min(255, new_r))
                new_g = max(0, min(255, new_g))
                new_b = max(0, min(255, new_b))

                money_surf.set_at((x, y), (new_r, new_g, new_b, color.a))

        money_surf.unlock()
        return money_surf

    @staticmethod
    def create_glow_surface(tile_size):
        """
        Creates a glowing effect surface for money tiles.

        Args:
            tile_size: Size of the tile.

        Returns:
            pygame.Surface: A circular glow surface.
        """
        radius = int(tile_size * 0.8)
        if radius <= 0:
            return None

        surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)

        # Golden glow color
        glow_color = (255, 215, 0)  # Gold

        # Draw gradient circles for glow effect
        for i in range(radius, 0, -2):
            alpha = 255 * (1 - (i / radius)) ** 1.5
            final_alpha = int(max(0, min(200, alpha)))
            pygame.draw.circle(surf, (*glow_color, final_alpha), (radius, radius), i)

        return surf

    @staticmethod
    def generate_money_positions(world_map, map_width, map_height, spawn_ratio=None):
        """
        Generates positions for money pickups across the map.

        Args:
            world_map: The 2D array of tile types.
            map_width: Width of the map.
            map_height: Height of the map.
            spawn_ratio: Optional override for spawn ratio.

        Returns:
            list: List of Money objects.
        """
        import random

        if spawn_ratio is None:
            spawn_ratio = Money.SPAWN_RATIO

        total_tiles = map_width * map_height
        num_money = total_tiles // spawn_ratio

        money_list = []
        attempts = 0
        max_attempts = num_money * 10  # Prevent infinite loop

        # Collect valid positions (not water, not already used)
        used_positions = set()

        while len(money_list) < num_money and attempts < max_attempts:
            attempts += 1

            x = random.randint(0, map_width - 1)
            y = random.randint(0, map_height - 1)

            # Skip if position already used
            if (x, y) in used_positions:
                continue

            # Skip water tiles
            tile_type = world_map[y][x]
            if tile_type == "water":
                continue

            # Create money at this position
            used_positions.add((x, y))
            money_list.append(Money(x, y))

        return money_list

    def __repr__(self):
        status = "collected" if self.collected else "available"
        return f"Money(id={self.id}, pos=({self.x},{self.y}), {status})"
