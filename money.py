"""
Money/Resource pickup system for REPUBLIC.

Chickens spawn on grass tiles (1 gold, or 3 gold for black chickens).
Gold spawns on granite/rock tiles (1 gold, or 3 gold for shiny gold).
"""

import random

import pygame


class MoneyType:
    """Types of money pickups."""

    CHICKEN = "chicken"  # Regular chicken on grass, gives 1 gold
    BLACK_CHICKEN = "black_chicken"  # Rare black chicken on grass, gives 3 gold
    GOLD = "gold"  # Regular gold on granite, gives 1 gold
    SHINY_GOLD = "shiny_gold"  # Rare shiny gold on granite, gives 3 gold


class Money:
    """Represents a collectible resource tile on the map."""

    # Money constants
    REGULAR_VALUE = 1  # Amount regular pickups give
    RARE_VALUE = 3  # Amount rare pickups give (black chicken / shiny gold)
    SPAWN_RATIO = 10  # One pickup per this many tiles (1:10 ratio)
    RARE_CHANCE = 0.15  # 15% chance for rare variant

    # Valid terrain for each type
    GRASS_TERRAIN = ["grass", "sand"]  # Chickens spawn here
    GRANITE_TERRAIN = ["granite", "rock"]  # Gold spawns here

    # Class variable to track unique IDs
    _next_id = 0

    def __init__(self, x, y, money_type=MoneyType.CHICKEN):
        """
        Initializes a money pickup.

        Args:
            x (int): The x-coordinate (tile) of the pickup.
            y (int): The y-coordinate (tile) of the pickup.
            money_type: Type of money (CHICKEN, BLACK_CHICKEN, GOLD, SHINY_GOLD).
        """
        # Assign unique ID
        self.id = Money._next_id
        Money._next_id += 1

        self.x = x
        self.y = y
        self.money_type = money_type
        self.collected = False

    @property
    def value(self):
        """Returns the value of this money pickup."""
        if self.money_type in (MoneyType.BLACK_CHICKEN, MoneyType.SHINY_GOLD):
            return self.RARE_VALUE
        return self.REGULAR_VALUE

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
            amount = self.value
            team.add_money(amount)
            return amount
        return 0

    def is_at(self, tile_x, tile_y):
        """
        Checks if this money is at the given tile position.

        Args:
            tile_x (int): The x-coordinate to check.
            tile_y (int): The y-coordinate to check.

        Returns:
            bool: True if the money is at this position and not collected.
        """
        return self.x == tile_x and self.y == tile_y and not self.collected

    def is_chicken(self):
        """Returns True if this is a chicken (regular or black)."""
        return self.money_type in (MoneyType.CHICKEN, MoneyType.BLACK_CHICKEN)

    def is_gold(self):
        """Returns True if this is gold (regular or shiny)."""
        return self.money_type in (MoneyType.GOLD, MoneyType.SHINY_GOLD)

    def is_rare(self):
        """Returns True if this is a rare variant (black chicken or shiny gold)."""
        return self.money_type in (MoneyType.BLACK_CHICKEN, MoneyType.SHINY_GOLD)

    @staticmethod
    def create_chicken_sprite(original_sprite, tile_size, inverted=False):
        """
        Creates a chicken sprite, optionally inverted (black chicken).

        Args:
            original_sprite: The original chicken sprite surface.
            tile_size: Size to scale the sprite to.
            inverted: If True, creates a black/inverted chicken.

        Returns:
            pygame.Surface: The processed chicken sprite.
        """
        # Scale the sprite
        scaled = pygame.transform.scale(original_sprite, (tile_size, tile_size))

        if not inverted:
            return scaled

        # Create inverted (black) chicken
        inverted_surf = scaled.copy()
        inverted_surf.lock()

        width, height = inverted_surf.get_size()

        for x in range(width):
            for y in range(height):
                color = inverted_surf.get_at((x, y))

                # Skip transparent pixels
                if color.a < 10:
                    continue

                # Invert the colors
                new_r = 255 - color.r
                new_g = 255 - color.g
                new_b = 255 - color.b

                # Darken slightly for more dramatic effect
                new_r = int(new_r * 0.7)
                new_g = int(new_g * 0.7)
                new_b = int(new_b * 0.7)

                # Add slight purple tint for mystical black chicken
                new_r = min(255, new_r + 20)
                new_b = min(255, new_b + 30)

                inverted_surf.set_at((x, y), (new_r, new_g, new_b, color.a))

        inverted_surf.unlock()
        return inverted_surf

    @staticmethod
    def create_gold_sprite(base_texture, tile_size, shiny=False):
        """
        Creates a gold sprite from a base texture.

        Args:
            base_texture: The original texture surface (e.g., granite).
            tile_size: Size to scale the sprite to.
            shiny: If True, creates a brighter/shiny version.

        Returns:
            pygame.Surface: A gold-tinted sprite.
        """
        # Scale the texture first
        scaled = pygame.transform.scale(base_texture, (tile_size, tile_size))

        # Create a copy to modify
        gold_surf = scaled.copy()

        # Apply gold tint
        gold_surf.lock()

        width, height = gold_surf.get_size()

        for x in range(width):
            for y in range(height):
                color = gold_surf.get_at((x, y))

                # Calculate luminance
                luminance = (color.r * 0.299 + color.g * 0.587 + color.b * 0.114) / 255

                if shiny:
                    # Inverted/shiny effect - brighter, more white-gold
                    inv_luminance = 1.0 - luminance

                    # Increase contrast significantly
                    contrast_factor = 2.0
                    inv_luminance = max(
                        0, min(1, (inv_luminance - 0.5) * contrast_factor + 0.5)
                    )

                    # Apply bright white-gold tint
                    gold_r = 255
                    gold_g = 250
                    gold_b = 200

                    new_r = int(gold_r * (0.5 + inv_luminance * 0.5))
                    new_g = int(gold_g * (0.5 + inv_luminance * 0.5))
                    new_b = int(gold_b * (0.3 + inv_luminance * 0.5))

                    # Add sparkle effect
                    if (x + y) % 4 == 0:
                        new_r = min(255, new_r + 50)
                        new_g = min(255, new_g + 50)
                        new_b = min(255, new_b + 40)
                else:
                    # Regular gold effect
                    contrast_factor = 1.5
                    luminance = max(
                        0, min(1, (luminance - 0.5) * contrast_factor + 0.5)
                    )

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

                gold_surf.set_at(
                    (x, y),
                    (new_r, new_g, new_b, color.a if hasattr(color, "a") else 255),
                )

        gold_surf.unlock()
        return gold_surf

    @staticmethod
    def create_glow_surface(tile_size, is_rare=False, is_chicken=True):
        """
        Creates a glowing effect surface for pickups.

        Args:
            tile_size: Size of the tile.
            is_rare: If True, creates a brighter glow.
            is_chicken: If True, uses chicken glow color, else gold glow.

        Returns:
            pygame.Surface: A circular glow surface.
        """
        radius = int(tile_size * 0.8)
        if is_rare:
            radius = int(tile_size * 1.0)  # Larger glow for rare

        if radius <= 0:
            return None

        surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)

        if is_chicken:
            if is_rare:
                # Dark purple glow for black chicken
                glow_color = (100, 50, 150)
            else:
                # Warm orange glow for regular chicken
                glow_color = (255, 200, 100)
        else:
            if is_rare:
                # Bright white-gold glow for shiny gold
                glow_color = (255, 250, 200)
            else:
                # Regular golden glow
                glow_color = (255, 215, 0)

        # Draw gradient circles for glow effect
        for i in range(radius, 0, -2):
            alpha = 255 * (1 - (i / radius)) ** 1.5
            if is_rare:
                alpha *= 1.3  # More intense for rare
            final_alpha = int(max(0, min(220, alpha)))
            pygame.draw.circle(surf, (*glow_color, final_alpha), (radius, radius), i)

        return surf

    @staticmethod
    def generate_money_positions(world_map, map_width, map_height, spawn_ratio=None):
        """
        Generates positions for money pickups across the map.
        Chickens spawn on grass, gold spawns on granite/rock.

        Args:
            world_map: The 2D array of tile types.
            map_width: Width of the map.
            map_height: Height of the map.
            spawn_ratio: Optional override for spawn ratio.

        Returns:
            list: List of Money objects.
        """
        if spawn_ratio is None:
            spawn_ratio = Money.SPAWN_RATIO

        total_tiles = map_width * map_height
        num_money = total_tiles // spawn_ratio

        money_list = []
        attempts = 0
        max_attempts = num_money * 10  # Prevent infinite loop

        # Collect valid positions (not already used)
        used_positions = set()

        # Separate counts for chickens and gold
        target_each = num_money // 2
        chicken_count = 0
        gold_count = 0

        while (chicken_count + gold_count) < num_money and attempts < max_attempts:
            attempts += 1

            x = random.randint(0, map_width - 1)
            y = random.randint(0, map_height - 1)

            # Skip if position already used
            if (x, y) in used_positions:
                continue

            # Get tile type
            tile_type = world_map[y][x]

            # Skip water, ice, lava
            if tile_type in ("water", "ice", "lava"):
                continue

            # Determine what can spawn here
            is_grass = tile_type in Money.GRASS_TERRAIN
            is_granite = tile_type in Money.GRANITE_TERRAIN

            # Decide type based on terrain
            money_type = None

            if is_grass and chicken_count < target_each:
                # Spawn chicken on grass
                if random.random() < Money.RARE_CHANCE:
                    money_type = MoneyType.BLACK_CHICKEN
                else:
                    money_type = MoneyType.CHICKEN
                chicken_count += 1

            elif is_granite and gold_count < target_each:
                # Spawn gold on granite
                if random.random() < Money.RARE_CHANCE:
                    money_type = MoneyType.SHINY_GOLD
                else:
                    money_type = MoneyType.GOLD
                gold_count += 1

            elif is_grass and gold_count >= target_each:
                # If we have enough gold, put more chickens
                if random.random() < Money.RARE_CHANCE:
                    money_type = MoneyType.BLACK_CHICKEN
                else:
                    money_type = MoneyType.CHICKEN
                chicken_count += 1

            elif is_granite and chicken_count >= target_each:
                # If we have enough chickens, put more gold
                if random.random() < Money.RARE_CHANCE:
                    money_type = MoneyType.SHINY_GOLD
                else:
                    money_type = MoneyType.GOLD
                gold_count += 1

            if money_type:
                used_positions.add((x, y))
                money_list.append(Money(x, y, money_type))

        return money_list

    def __repr__(self):
        status = "collected" if self.collected else "available"
        return f"Money(id={self.id}, pos=({self.x},{self.y}), type={self.money_type}, value={self.value}, {status})"
