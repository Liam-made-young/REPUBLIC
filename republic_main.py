import math

import pygame
from assets import AssetManager
from camera import Camera
from game_state import GameState
from player import Player
from renderer import MapRenderer
from ui import UIManager
from world import WorldGenerator

# --- Main Game Constants ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 800
MAP_WIDTH = 125
MAP_HEIGHT = 125
INITIAL_TILE_SIZE = 32
ZOOM_SPEED = 1
SCROLL_SPEED = 10
MOVEMENT_RANGE = 3  # Player can move 2 tiles in any direction


class Game:
    """Manages the main game loop and coordinates all game components."""

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("REPUBLIC")
        self.clock = pygame.time.Clock()
        self.running = True

        # Initialize components
        self.asset_manager = AssetManager()
        self.world_generator = WorldGenerator(MAP_WIDTH, MAP_HEIGHT)
        self.camera = Camera(
            SCREEN_WIDTH, SCREEN_HEIGHT, MAP_WIDTH, MAP_HEIGHT, INITIAL_TILE_SIZE
        )
        self.renderer = MapRenderer(self.screen)

        # Initialize game logic components
        self.game_state = GameState()
        # Start player in the center of the map
        self.player = Player(MAP_WIDTH // 2, MAP_HEIGHT // 2)
        self.ui_manager = UIManager(SCREEN_WIDTH, SCREEN_HEIGHT)

        self.world = None
        self.hovered_tile = None
        self.animation_timer = 0

    def run(self):
        """Starts and runs the main game loop."""
        print("Loading assets...")
        self.asset_manager.load_assets()
        # Create initial scaled textures and glow surfaces
        self.asset_manager.rescale_textures(self.camera.tile_size)
        self.renderer.create_glow_surfaces(self.camera.tile_size)
        self.player.sprite = self.asset_manager.sprites.get("player")

        print("Generating world...")
        self.world = self.world_generator.generate()
        print("World generation complete. Game starting.")

        while self.running:
            self.events()
            self.update()
            self.draw()
            self.clock.tick(60)

        pygame.quit()

    def events(self):
        """Handles user input and events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_RETURN:  # NEW: End Turn on Return/Enter
                    self.game_state.end_turn()
            if event.type == pygame.MOUSEBUTTONDOWN:
                self.handle_mouse_click(event.pos)

    def handle_mouse_click(self, mouse_pos):
        """Handles all logic for mouse clicks, including UI and player movement."""
        # Check for UI interaction first
        if self.ui_manager.end_turn_button_rect.collidepoint(mouse_pos):
            self.game_state.end_turn()
            return

        # If not UI, check for map interaction (player movement)
        if not self.game_state.player_has_moved:
            # hovered_tile is already calculated in the update loop
            if self.hovered_tile:
                tile_x, tile_y = self.hovered_tile
                # Use the player's new validation method
                if self.player.is_valid_move(tile_x, tile_y, MOVEMENT_RANGE):
                    self.player.move(tile_x, tile_y)
                    self.game_state.player_has_moved = True

    def update(self):
        """Updates the state of all game components."""
        self.animation_timer += 1
        keys = pygame.key.get_pressed()
        needs_rescale = self.camera.update(keys, ZOOM_SPEED, SCROLL_SPEED, self.player)
        if needs_rescale:
            self.asset_manager.rescale_textures(self.camera.tile_size)
            self.renderer.create_glow_surfaces(self.camera.tile_size)

        # Update hovered tile for visual feedback
        mouse_pos = pygame.mouse.get_pos()
        self.hovered_tile = (
            math.floor((mouse_pos[0] + self.camera.offset_x) / self.camera.tile_size),
            math.floor((mouse_pos[1] + self.camera.offset_y) / self.camera.tile_size),
        )

    def draw(self):
        """Draws the game world to the screen."""
        if self.world:
            self.renderer.draw(
                self.world,
                self.camera,
                self.asset_manager.scaled_textures,
                self.player,
                self.ui_manager,
                self.game_state,
                self.hovered_tile,
                MOVEMENT_RANGE,
                self.animation_timer,
            )


if __name__ == "__main__":
    game = Game()
    game.run()
