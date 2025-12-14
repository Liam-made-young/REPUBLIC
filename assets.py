import os

import pygame


class AssetManager:
    def __init__(self):
        """Initializes the AssetManager."""
        # Build a robust path to the assets directory relative to this file
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.asset_path = os.path.join(script_dir, "assets", "textures")

        self.original_textures = {}
        self.scaled_textures = {}
        self.sprites = {}

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

        # Load sprites
        try:
            path = os.path.join(self.asset_path, "char1.png")
            self.sprites["player"] = pygame.image.load(path).convert_alpha()
        except pygame.error as e:
            print(f"Unable to load player sprite: {path}\n{e}")
            placeholder = pygame.Surface((32, 32))
            placeholder.fill((0, 255, 0))  # Green placeholder
            self.sprites["player"] = placeholder

    def rescale_textures(self, tile_size):
        """
        Rescales all textures from original_textures to a new tile size
        and stores them in the scaled_textures dictionary.
        """
        for name, image in self.original_textures.items():
            self.scaled_textures[name] = pygame.transform.scale(
                image, (tile_size, tile_size)
            )
