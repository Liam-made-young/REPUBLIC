import math

import pygame
from assets import AssetManager
from camera import Camera
from enemy import Enemy
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
MOVEMENT_RANGE = 3  # Player can move 3 tiles in any direction
SPAWN_DISTANCE = 20  # Distance between player and enemy spawn points


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

        # Spawn player and enemy equidistant from center, ~20 tiles apart
        center_x = MAP_WIDTH // 2
        center_y = MAP_HEIGHT // 2
        half_distance = SPAWN_DISTANCE // 2

        # Player spawns to the left of center
        self.player = Player(center_x - half_distance, center_y)
        # Enemy spawns to the right of center
        self.enemy = Enemy(center_x + half_distance, center_y)

        self.ui_manager = UIManager(SCREEN_WIDTH, SCREEN_HEIGHT)

        self.world = None
        self.hovered_tile = None
        self.animation_timer = 0

        # Track if we need to center camera on turn change
        self.last_phase = self.game_state.current_phase

    def run(self):
        """Starts and runs the main game loop."""
        print("Loading assets...")
        self.asset_manager.load_assets()
        # Create initial scaled textures and glow surfaces
        self.asset_manager.rescale_textures(self.camera.tile_size)
        self.renderer.create_glow_surfaces(self.camera.tile_size)

        # Set up sprites
        self.player.sprite = self.asset_manager.sprites.get("player")
        # Enemy uses the same sprite but will invert it
        self.enemy.set_sprite(self.asset_manager.sprites.get("player"))

        print("Generating world...")
        self.world = self.world_generator.generate()
        print("World generation complete. Game starting.")

        # Center camera on player at start (it's player's turn)
        self.camera.center_on_entity(self.player)

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
                elif event.key == pygame.K_RETURN:
                    if not self.game_state.game_over:
                        self._handle_end_turn()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if not self.game_state.game_over:
                    self.handle_mouse_click(event.pos)

    def _handle_end_turn(self):
        """Handles the end turn action and camera refocus."""
        self.game_state.end_turn()
        self._center_camera_on_active_entity()

    def _center_camera_on_active_entity(self):
        """Centers the camera on whoever's turn it is."""
        if self.game_state.is_player_turn():
            self.camera.center_on_entity(self.player)
        else:
            self.camera.center_on_entity(self.enemy)

    def _get_focus_entity(self):
        """Returns the entity that should be the focus for camera operations."""
        if self.game_state.is_player_turn():
            return self.player
        else:
            return self.enemy

    def _check_game_over(self):
        """Checks if the game is over due to death."""
        if self.enemy.is_dead():
            self.game_state.set_game_over("player")
        elif self.player.is_dead():
            self.game_state.set_game_over("enemy")

    def handle_mouse_click(self, mouse_pos):
        """Handles all logic for mouse clicks, including UI, movement, and attacks."""
        # Check for UI interaction first
        if self.ui_manager.end_turn_button_rect.collidepoint(mouse_pos):
            self._handle_end_turn()
            return

        # Calculate clicked tile from mouse position
        tile_x = math.floor(
            (mouse_pos[0] + self.camera.offset_x) / self.camera.tile_size
        )
        tile_y = math.floor(
            (mouse_pos[1] + self.camera.offset_y) / self.camera.tile_size
        )

        if self.game_state.is_player_turn() and not self.game_state.player_has_moved:
            # Check if clicking on enemy (attack)
            if (
                tile_x == self.enemy.x
                and tile_y == self.enemy.y
                and not self.enemy.is_dead()
            ):
                # Check if enemy is in range
                if self.player.is_valid_move(tile_x, tile_y, MOVEMENT_RANGE):
                    # Attack the enemy
                    self.enemy.take_damage(Player.ATTACK_DAMAGE)
                    self.game_state.player_has_moved = True
                    self._check_game_over()
            else:
                # Normal movement
                if self.player.is_valid_move(tile_x, tile_y, MOVEMENT_RANGE):
                    # Don't move onto enemy position
                    if not (tile_x == self.enemy.x and tile_y == self.enemy.y):
                        self.player.move(tile_x, tile_y)
                        self.game_state.player_has_moved = True

        elif self.game_state.is_enemy_turn() and not self.game_state.enemy_has_moved:
            # Check if clicking on player (attack)
            if (
                tile_x == self.player.x
                and tile_y == self.player.y
                and not self.player.is_dead()
            ):
                # Check if player is in range
                if self.enemy.is_valid_move(tile_x, tile_y, MOVEMENT_RANGE):
                    # Attack the player
                    self.player.take_damage(Enemy.ATTACK_DAMAGE)
                    self.game_state.enemy_has_moved = True
                    self._check_game_over()
            else:
                # Normal movement
                if self.enemy.is_valid_move(tile_x, tile_y, MOVEMENT_RANGE):
                    # Don't move onto player position
                    if not (tile_x == self.player.x and tile_y == self.player.y):
                        self.enemy.move(tile_x, tile_y)
                        self.game_state.enemy_has_moved = True

    def update(self):
        """Updates the state of all game components."""
        self.animation_timer += 1

        # Check if phase changed and center camera accordingly
        if self.game_state.current_phase != self.last_phase:
            self._center_camera_on_active_entity()
            self.last_phase = self.game_state.current_phase

        keys = pygame.key.get_pressed()
        focus_entity = self._get_focus_entity()
        needs_rescale = self.camera.update(keys, ZOOM_SPEED, SCROLL_SPEED, focus_entity)
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
                self.enemy,
                self.ui_manager,
                self.game_state,
                self.hovered_tile,
                MOVEMENT_RANGE,
                self.animation_timer,
            )


if __name__ == "__main__":
    game = Game()
    game.run()
