import os

import pygame


class AssetManager:
    """Manages loading and scaling of all game assets including textures and sprites."""

    def __init__(self):
        """Initializes the AssetManager."""
        # Build a robust path to the assets directory relative to this file
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.asset_path = os.path.join(script_dir, "assets", "textures")

        self.original_textures = {}
        self.scaled_textures = {}
        self.sprites = {}  # Character sprites by type
        self.money_sprite = None
        self.fog_tile = None

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

        # Load character sprites
        sprite_files = {
            "warrior": "char1.png",
            "swordsman": "swordsman.png",
            "shieldman": "shield.png",
            "runner": "runner.png",
        }
        for name, filename in sprite_files.items():
            path = os.path.join(self.asset_path, filename)
            try:
                self.sprites[name] = pygame.image.load(path).convert_alpha()
            except pygame.error as e:
                print(f"Unable to load sprite: {path}\n{e}")
                # Create colored placeholder based on type
                placeholder = pygame.Surface((32, 32), pygame.SRCALPHA)
                colors = {
                    "warrior": (100, 200, 100),
                    "swordsman": (200, 100, 100),
                    "shieldman": (100, 100, 200),
                    "runner": (200, 200, 100),
                }
                placeholder.fill(colors.get(name, (150, 150, 150)))
                self.sprites[name] = placeholder

        # Keep legacy "player" reference for compatibility
        self.sprites["player"] = self.sprites.get("warrior")

    def rescale_textures(self, tile_size):
        """
        Rescales all textures from original_textures to a new tile size
        and stores them in the scaled_textures dictionary.
        """
        for name, image in self.original_textures.items():
            self.scaled_textures[name] = pygame.transform.scale(
                image, (tile_size, tile_size)
            )

        # Create money sprite from sand texture
        self._create_money_sprite(tile_size)

        # Create fog tile from grass texture
        self._create_fog_tile(tile_size)

    def _create_money_sprite(self, tile_size):
        """Creates a glowing yellow money sprite based on the sand texture."""
        if "sand" not in self.original_textures:
            return

        # Scale the texture first
        scaled = pygame.transform.scale(
            self.original_textures["sand"], (tile_size, tile_size)
        )

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

                money_surf.set_at((x, y), (new_r, new_g, new_b, 255))

        money_surf.unlock()
        self.money_sprite = money_surf

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

                fog_surf.set_at((x, y), (new_r, new_g, new_b, 255))

        fog_surf.unlock()
        self.fog_tile = fog_surf

    def get_sprite(self, sprite_name):
        """
        Returns a sprite by name.

        Args:
            sprite_name: The name of the sprite to get.

        Returns:
            pygame.Surface or None: The sprite surface if found.
        """
        return self.sprites.get(sprite_name)

    def get_character_sprite(self, char_type):
        """
        Returns the sprite for a character type.

        Args:
            char_type: The character type (warrior, swordsman, shieldman, runner).

        Returns:
            pygame.Surface: The sprite surface.
        """
        return self.sprites.get(char_type, self.sprites.get("warrior"))

    def get_money_sprite(self):
        """Returns the money pickup sprite."""
        return self.money_sprite

    def get_fog_tile(self):
        """Returns the fog of war tile."""
        return self.fog_tile
