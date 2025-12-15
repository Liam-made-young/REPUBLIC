import os
import sys

import pygame


class AssetManager:
    """Manages loading and scaling of all game assets including textures and sprites."""

    # Character types and their sprite file prefixes
    CHARACTER_SPRITE_PREFIXES = {
        "warrior": "char",
        "swordsman": "sword",
        "shieldman": "shield",
        "runner": "runner",
        "seer": "seer",
        "tank": "tank",
        "king": "king",
    }

    # Available colors
    COLORS = ["red", "blue", "green", "purple"]

    def get_resource_path(self, relative_path):
        """ Get absolute path to resource, works for dev and for PyInstaller """
        if hasattr(sys, '_MEIPASS'):
            return os.path.join(sys._MEIPASS, relative_path)
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), relative_path)

    def __init__(self):
        """Initializes the AssetManager."""
        # Build a robust path to the assets directory relative to this file
        script_dir = self.get_resource_path("")
        self.asset_path = os.path.join(script_dir, "assets", "textures")
        self.sprite_path = os.path.join(
            script_dir, "assets", "textures", "character sprites"
        )

        self.original_textures = {}
        self.scaled_textures = {}

        # Sprites organized by {char_type: {color: surface}}
        self.character_sprites = {}

        # Chicken sprites
        self.chicken_sprite = None  # Original chicken
        self.black_chicken_sprite = None  # Inverted chicken

        # Gold sprites (created from textures)
        self.gold_sprite = None
        self.shiny_gold_sprite = None

        # Fog tile
        self.fog_tile = None

        # Current tile size
        self.current_tile_size = 0

    def load_assets(self):
        """
        Loads all game textures and sprites from the disk.
        """
        # Load tile textures
        texture_files = {
            "grass": "grass.jpg",
            "water": "water.jpg",
            "sand": "sand.jpg",
            "granite": "granite.jpg",
            "ice": "ice.jpg",
            "lava": "lava.jpg",
        }
        for name, filename in texture_files.items():
            path = os.path.join(self.asset_path, filename)
            try:
                self.original_textures[name] = pygame.image.load(path).convert()
            except pygame.error as e:
                print(f"Unable to load texture: {path}\n{e}")
                placeholder = pygame.Surface((100, 100))
                placeholder.fill((255, 0, 255))
                self.original_textures[name] = placeholder

        # Load gold texture for gold pickups
        try:
            path = os.path.join(self.sprite_path, "gold.png")
            self.original_textures["gold"] = pygame.image.load(path).convert_alpha()
        except pygame.error as e:
            print(f"Unable to load gold texture: {path}\n{e}")
            # Create golden placeholder
            placeholder = pygame.Surface((100, 100))
            placeholder.fill((255, 215, 0))
            self.original_textures["gold"] = placeholder

        # Load chicken sprite
        self._load_chicken_sprite()

        # Load character sprites by type and color
        self._load_character_sprites()

    def _load_chicken_sprite(self):
        """Loads the chicken sprite."""
        chicken_path = os.path.join(self.sprite_path, "chicken.png")
        try:
            self.chicken_sprite = pygame.image.load(chicken_path).convert_alpha()
            print("Loaded chicken sprite")
        except pygame.error as e:
            print(f"Unable to load chicken sprite: {chicken_path}\n{e}")
            # Create placeholder
            placeholder = pygame.Surface((32, 32), pygame.SRCALPHA)
            placeholder.fill((255, 200, 100))
            self.chicken_sprite = placeholder

    def _load_character_sprites(self):
        """Loads all character sprites organized by type and color."""
        for char_type, prefix in self.CHARACTER_SPRITE_PREFIXES.items():
            self.character_sprites[char_type] = {}

            for color in self.COLORS:
                filename = f"{prefix}_{color}.png"
                path = os.path.join(self.sprite_path, filename)

                try:
                    sprite = pygame.image.load(path).convert_alpha()
                    self.character_sprites[char_type][color] = sprite
                except pygame.error as e:
                    print(f"Unable to load sprite: {path}\n{e}")
                    # Create colored placeholder
                    placeholder = pygame.Surface((32, 32), pygame.SRCALPHA)
                    color_rgb = self._get_placeholder_color(color)
                    placeholder.fill(color_rgb)
                    self.character_sprites[char_type][color] = placeholder

    def _get_placeholder_color(self, color_key):
        """Returns an RGB tuple for placeholder sprites."""
        colors = {
            "red": (200, 50, 50),
            "blue": (50, 100, 200),
            "green": (50, 180, 50),
            "purple": (150, 50, 180),
        }
        return colors.get(color_key, (150, 150, 150))

    def get_seer_sprite(self, color_key):
        """
        Returns the sprite for a seer of the given color.

        Args:
            color_key: The color key (red, blue, green, purple).

        Returns:
            pygame.Surface: The seer sprite surface.
        """
        return self.get_character_sprite("seer", color_key)

    def rescale_textures(self, tile_size):
        """
        Rescales all textures from original_textures to a new tile size
        and stores them in the scaled_textures dictionary.
        """
        self.current_tile_size = tile_size

        for name, image in self.original_textures.items():
            self.scaled_textures[name] = pygame.transform.scale(
                image, (tile_size, tile_size)
            )

        # Scale chicken sprites
        self._scale_chicken_sprites(tile_size)

        # Create gold sprites from granite texture
        self._create_gold_sprites(tile_size)

        # Create fog tile from grass texture
        self._create_fog_tile(tile_size)

    def _scale_chicken_sprites(self, tile_size):
        """Scales chicken sprites and creates black chicken variant."""
        if self.chicken_sprite is None:
            return

        from money import Money

        # Regular chicken
        self.chicken_sprite_scaled = Money.create_chicken_sprite(
            self.chicken_sprite, tile_size, inverted=False
        )

        # Black chicken (inverted)
        self.black_chicken_sprite = Money.create_chicken_sprite(
            self.chicken_sprite, tile_size, inverted=True
        )

    def _create_gold_sprites(self, tile_size):
        """Creates gold sprites from the gold texture or granite."""
        from money import Money

        # Use granite texture as base for gold
        if "gold" in self.original_textures and not isinstance(self.original_textures["gold"], pygame.Surface) == False: # Ensure it's a valid surface
             base = self.original_textures["gold"]
        elif "granite" in self.original_textures:
             base = self.original_textures["granite"]
        else:
            return

        # Regular gold
        self.gold_sprite = Money.create_gold_sprite(base, tile_size, shiny=False)

        # Shiny gold
        self.shiny_gold_sprite = Money.create_gold_sprite(base, tile_size, shiny=True)

    def _create_fog_tile(self, tile_size):
        """Creates a fog tile based on a whitened version of the grass texture."""
        if "grass" not in self.original_textures:
            return

        # Scale the texture first
        scaled = pygame.transform.scale(
            self.original_textures["grass"], (tile_size, tile_size)
        )

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
        self.fog_tile = fog_surf

    def get_character_sprite(self, char_type, color_key):
        """
        Returns the sprite for a character type and color.

        Args:
            char_type: The character type (warrior, swordsman, shieldman, runner).
            color_key: The color key (red, blue, green, purple).

        Returns:
            pygame.Surface: The sprite surface.
        """
        # Default to warrior if type not found
        if char_type not in self.character_sprites:
            char_type = "warrior"

        # Default to red if color not found
        if color_key not in self.character_sprites.get(char_type, {}):
            color_key = "red"

        return self.character_sprites.get(char_type, {}).get(color_key)

    def get_chicken_sprite(self, is_black=False):
        """
        Returns the chicken sprite.

        Args:
            is_black: If True, returns the black (inverted) chicken.

        Returns:
            pygame.Surface: The chicken sprite.
        """
        if is_black:
            return self.black_chicken_sprite
        return getattr(self, "chicken_sprite_scaled", self.chicken_sprite)

    def get_gold_sprite(self, is_shiny=False):
        """
        Returns the gold sprite.

        Args:
            is_shiny: If True, returns the shiny gold variant.

        Returns:
            pygame.Surface: The gold sprite.
        """
        if is_shiny:
            return self.shiny_gold_sprite
        return self.gold_sprite

    def get_fog_tile(self):
        """Returns the fog of war tile."""
        return self.fog_tile

    def get_available_colors(self):
        """Returns list of available color keys."""
        return self.COLORS.copy()

    def get_available_char_types(self):
        """Returns list of available character types."""
        return list(self.CHARACTER_SPRITE_PREFIXES.keys())
