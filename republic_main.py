import math
import random

import pygame
from assets import AssetManager
from camera import Camera
from capital import Capital
from character import Character, CharacterType
from fog_of_war import FogOfWar
from game_state import GameState
from money import Money
from renderer import MapRenderer
from team import Team, TeamSide
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

# Capital spawn margins
CAPITAL_MARGIN = 15  # Distance from map edge for starting capitals


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

        # Initialize teams
        self.red_team = Team(TeamSide.RED)
        self.blue_team = Team(TeamSide.BLUE)

        # Fog of war
        self.fog_of_war = FogOfWar(MAP_WIDTH, MAP_HEIGHT)

        # UI Manager
        self.ui_manager = UIManager(SCREEN_WIDTH, SCREEN_HEIGHT)

        # World and money
        self.world = None
        self.money_pickups = []

        # UI state
        self.hovered_tile = None
        self.animation_timer = 0

    def run(self):
        """Starts and runs the main game loop."""
        print("Loading assets...")
        self.asset_manager.load_assets()

        # Create initial scaled textures and glow surfaces
        self.asset_manager.rescale_textures(self.camera.tile_size)
        self.renderer.create_glow_surfaces(self.camera.tile_size)

        # Set up renderer with money sprite and fog tile
        self.renderer.set_money_sprite(self.asset_manager.get_money_sprite())
        self.renderer.set_fog_tile(self.asset_manager.get_fog_tile())

        print("Generating world...")
        self.world = self.world_generator.generate()
        print("World generation complete.")

        # Generate money pickups
        self._generate_money()

        # Set up starting capitals and characters
        self._setup_starting_positions()

        # Update fog of war for both teams
        self.fog_of_war.update_team_visibility(self.red_team)
        self.fog_of_war.update_team_visibility(self.blue_team)

        # Center camera on red team's starting capital (red starts first)
        if self.red_team.capitals:
            self.camera.center_on_entity(self.red_team.capitals[0])

        print("Game starting.")

        while self.running:
            self.events()
            self.update()
            self.draw()
            self.clock.tick(60)

        pygame.quit()

    def _generate_money(self):
        """Generates money pickups across the map."""
        self.money_pickups = Money.generate_money_positions(
            self.world.world_map, MAP_WIDTH, MAP_HEIGHT
        )
        print(f"Generated {len(self.money_pickups)} money pickups.")

    def _setup_starting_positions(self):
        """Sets up starting capitals and characters for both teams."""
        # Find suitable positions for capitals (avoiding water)
        red_capital_x = CAPITAL_MARGIN
        blue_capital_x = MAP_WIDTH - CAPITAL_MARGIN - 1

        # Find y positions (with some randomness)
        red_capital_y = self._find_valid_capital_y(red_capital_x)
        blue_capital_y = self._find_valid_capital_y(blue_capital_x)

        # Create starting capitals
        red_capital = Capital(red_capital_x, red_capital_y, self.red_team)
        blue_capital = Capital(blue_capital_x, blue_capital_y, self.blue_team)

        self.red_team.add_capital(red_capital)
        self.blue_team.add_capital(blue_capital)

        # Create starting warriors for each team
        red_char = self._create_starting_character(
            self.red_team, red_capital, CharacterType.WARRIOR
        )
        blue_char = self._create_starting_character(
            self.blue_team, blue_capital, CharacterType.WARRIOR
        )

        if red_char:
            self.red_team.add_character(red_char)
        if blue_char:
            self.blue_team.add_character(blue_char)

        print(f"Red capital at ({red_capital_x}, {red_capital_y})")
        print(f"Blue capital at ({blue_capital_x}, {blue_capital_y})")

    def _find_valid_capital_y(self, x):
        """Finds a valid y position for a capital at the given x coordinate."""
        center_y = MAP_HEIGHT // 2
        # Try center first, then expand outward
        for offset in range(0, MAP_HEIGHT // 2):
            for y in [center_y + offset, center_y - offset]:
                if 0 <= y < MAP_HEIGHT:
                    tile = self.world.world_map[y][x]
                    if tile != "water":
                        return y
        return center_y  # Fallback

    def _create_starting_character(self, team, capital, char_type):
        """Creates a starting character next to a capital."""
        spawn_positions = capital.get_spawn_positions()

        for pos in spawn_positions:
            x, y = pos
            if 0 <= x < MAP_WIDTH and 0 <= y < MAP_HEIGHT:
                tile = self.world.world_map[y][x]
                if tile != "water":
                    char = Character(x, y, team, char_type)
                    # Set the sprite
                    sprite = self.asset_manager.get_character_sprite(char_type)
                    char.set_sprite(sprite)
                    return char
        return None

    def events(self):
        """Handles user input and events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.game_state.show_character_menu:
                        self.game_state.close_character_menu()
                    elif self.game_state.show_creation_menu:
                        self.game_state.close_all_menus()
                    else:
                        self.running = False
                elif event.key == pygame.K_RETURN:
                    if not self.game_state.game_over:
                        self._handle_end_turn()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    self.handle_mouse_click(event.pos)
                elif event.button == 3:  # Right click
                    # Deselect character
                    self.game_state.deselect_character()
                    self.game_state.close_all_menus()

    def _handle_end_turn(self):
        """Handles the end turn action and camera refocus."""
        self.game_state.end_turn(self.red_team, self.blue_team)

        # Update fog of war for the new active team
        current_team = self._get_current_team()
        self.fog_of_war.update_team_visibility(current_team)

        # Center camera on the new team's first capital or character
        self._center_camera_on_team(current_team)

    def _get_current_team(self):
        """Returns the team whose turn it is."""
        if self.game_state.is_red_turn():
            return self.red_team
        else:
            return self.blue_team

    def _get_enemy_team(self):
        """Returns the team that is not currently playing."""
        if self.game_state.is_red_turn():
            return self.blue_team
        else:
            return self.red_team

    def _center_camera_on_team(self, team):
        """Centers the camera on a team's capital or character."""
        if team.capitals:
            self.camera.center_on_entity(team.capitals[0])
        elif team.get_living_characters():
            self.camera.center_on_entity(team.get_living_characters()[0])

    def _get_focus_entity(self):
        """Returns the entity that should be the focus for camera operations."""
        if self.game_state.selected_character:
            return self.game_state.selected_character

        current_team = self._get_current_team()
        if current_team.capitals:
            return current_team.capitals[0]
        elif current_team.get_living_characters():
            return current_team.get_living_characters()[0]

        # Fallback to center of map
        class MapCenter:
            def __init__(self):
                self.x = MAP_WIDTH // 2
                self.y = MAP_HEIGHT // 2

        return MapCenter()

    def handle_mouse_click(self, mouse_pos):
        """Handles all logic for mouse clicks."""
        if self.game_state.game_over:
            return

        current_team = self._get_current_team()
        enemy_team = self._get_enemy_team()

        # Check UI interactions first
        if self._handle_ui_click(mouse_pos, current_team):
            return

        # Calculate clicked tile
        tile_x = math.floor(
            (mouse_pos[0] + self.camera.offset_x) / self.camera.tile_size
        )
        tile_y = math.floor(
            (mouse_pos[1] + self.camera.offset_y) / self.camera.tile_size
        )

        # Handle creation menu mode (placing capital)
        if self.game_state.show_creation_menu:
            self._handle_capital_placement(tile_x, tile_y, current_team)
            return

        # Handle character menu mode
        if self.game_state.show_character_menu:
            # Check if clicking a character button
            char_type = self.ui_manager.get_char_button_at(mouse_pos)
            if char_type:
                self._handle_character_purchase(char_type, current_team)
            elif not self.ui_manager.is_click_in_char_menu(mouse_pos):
                self.game_state.close_character_menu()
            return

        # Check if clicking on own capital (open character menu)
        for capital in current_team.capitals:
            if capital.x == tile_x and capital.y == tile_y:
                if capital.can_spawn_character():
                    self.game_state.open_character_menu(capital)
                return

        # Check if clicking on own character (select it)
        for char in current_team.get_living_characters():
            if char.x == tile_x and char.y == tile_y:
                if self.game_state.selected_character == char:
                    # Clicking selected character deselects it
                    self.game_state.deselect_character()
                else:
                    self.game_state.select_character(char)
                return

        # If a character is selected, handle movement/attack
        if self.game_state.selected_character:
            self._handle_character_action(tile_x, tile_y, current_team, enemy_team)

    def _handle_ui_click(self, mouse_pos, current_team):
        """Handles clicks on UI elements. Returns True if a UI element was clicked."""
        # End Turn button
        if self.ui_manager.end_turn_button_rect.collidepoint(mouse_pos):
            self._handle_end_turn()
            return True

        # Creation menu button
        if self.ui_manager.creation_menu_button_rect.collidepoint(mouse_pos):
            self.game_state.toggle_creation_menu()
            return True

        # Check if clicking in creation menu area (don't pass through)
        if self.game_state.show_creation_menu:
            if self.ui_manager.is_click_in_creation_menu(mouse_pos):
                return True

        return False

    def _handle_capital_placement(self, tile_x, tile_y, current_team):
        """Handles placing a new capital."""
        # Check if team can afford
        if not current_team.can_afford(Capital.COST):
            return

        # Check if valid position (not water, not too close to other capitals)
        if not (0 <= tile_x < MAP_WIDTH and 0 <= tile_y < MAP_HEIGHT):
            return

        tile = self.world.world_map[tile_y][tile_x]
        if tile == "water":
            return

        # Check distance from all capitals
        all_capitals = self.red_team.capitals + self.blue_team.capitals
        if not Capital.is_valid_capital_position(tile_x, tile_y, all_capitals):
            return

        # Check if position is revealed
        if not current_team.is_tile_revealed(tile_x, tile_y):
            return

        # Create the capital
        current_team.spend_money(Capital.COST)
        new_capital = Capital(tile_x, tile_y, current_team)
        current_team.add_capital(new_capital)

        # Update fog of war
        self.fog_of_war.update_team_visibility(current_team)

        # Close the menu
        self.game_state.close_all_menus()

    def _handle_character_purchase(self, char_type, current_team):
        """Handles purchasing a character from the character menu."""
        capital = self.game_state.selected_capital
        if not capital:
            return

        # Check if capital can spawn
        if not capital.can_spawn_character():
            return

        # Check cost
        cost = CharacterType.get_cost(char_type)
        if not current_team.can_afford(cost):
            return

        # Find valid spawn position
        spawn_pos = self._find_spawn_position(capital)
        if not spawn_pos:
            return

        # Create the character
        current_team.spend_money(cost)
        new_char = Character(spawn_pos[0], spawn_pos[1], current_team, char_type)
        sprite = self.asset_manager.get_character_sprite(char_type)
        new_char.set_sprite(sprite)

        current_team.add_character(new_char)
        capital.spawn_character()

        # Update fog of war
        self.fog_of_war.update_team_visibility(current_team)

        # Close the menu
        self.game_state.close_character_menu()

    def _find_spawn_position(self, capital):
        """Finds a valid spawn position around a capital."""
        spawn_positions = capital.get_spawn_positions()
        all_chars = self.red_team.characters + self.blue_team.characters
        all_capitals = self.red_team.capitals + self.blue_team.capitals

        for pos in spawn_positions:
            x, y = pos
            if not (0 <= x < MAP_WIDTH and 0 <= y < MAP_HEIGHT):
                continue

            # Check if tile is walkable
            tile = self.world.world_map[y][x]
            if tile == "water":
                continue

            # Check if position is occupied by character
            occupied = any(c.x == x and c.y == y and not c.is_dead() for c in all_chars)
            if occupied:
                continue

            # Check if position is occupied by capital
            cap_occupied = any(c.x == x and c.y == y for c in all_capitals)
            if cap_occupied:
                continue

            return pos

        return None

    def _handle_character_action(self, tile_x, tile_y, current_team, enemy_team):
        """Handles movement or attack for the selected character."""
        selected = self.game_state.selected_character

        if not selected or not selected.can_act():
            return

        # Check if tile is revealed
        if not current_team.is_tile_revealed(tile_x, tile_y):
            return

        # Check if attacking an enemy character
        for enemy in enemy_team.get_living_characters():
            if enemy.x == tile_x and enemy.y == tile_y:
                if selected.is_in_range(tile_x, tile_y):
                    # Attack!
                    enemy.take_damage(selected.damage)
                    selected.has_moved = True

                    # Check if enemy died
                    if enemy.is_dead():
                        enemy_team.remove_character(enemy)

                    # Check victory conditions
                    self.game_state.check_victory_conditions(
                        self.red_team, self.blue_team
                    )

                    # Deselect after action
                    self.game_state.deselect_character()
                return

        # Check if conquering an enemy capital
        for capital in enemy_team.capitals:
            if capital.x == tile_x and capital.y == tile_y:
                if selected.is_in_range(tile_x, tile_y):
                    # Check if capital is unprotected
                    all_chars = self.red_team.characters + self.blue_team.characters
                    if not capital.is_protected(all_chars):
                        # Conquer the capital!
                        enemy_team.remove_capital(capital)
                        selected.has_moved = True

                        # Check victory conditions
                        self.game_state.check_victory_conditions(
                            self.red_team, self.blue_team
                        )

                        self.game_state.deselect_character()
                return

        # Check if moving to a valid tile
        if selected.is_valid_move(tile_x, tile_y):
            # Check bounds
            if not (0 <= tile_x < MAP_WIDTH and 0 <= tile_y < MAP_HEIGHT):
                return

            # Check if tile is walkable
            tile = self.world.world_map[tile_y][tile_x]
            if tile == "water":
                return

            # Check if occupied
            all_chars = self.red_team.characters + self.blue_team.characters
            occupied = any(
                c.x == tile_x and c.y == tile_y and not c.is_dead() for c in all_chars
            )
            if occupied:
                return

            all_capitals = self.red_team.capitals + self.blue_team.capitals
            cap_occupied = any(c.x == tile_x and c.y == tile_y for c in all_capitals)
            if cap_occupied:
                return

            # Move!
            selected.move(tile_x, tile_y)

            # Check for money pickup
            self._check_money_pickup(tile_x, tile_y, current_team)

            # Update fog of war
            self.fog_of_war.update_team_visibility(current_team)

            # Deselect after move
            self.game_state.deselect_character()

    def _check_money_pickup(self, tile_x, tile_y, team):
        """Checks if a character picked up money at the given position."""
        for money in self.money_pickups:
            if money.is_at(tile_x, tile_y):
                money.collect(team)
                break

    def update(self):
        """Updates the state of all game components."""
        self.animation_timer += 1

        # Handle camera controls
        keys = pygame.key.get_pressed()
        focus_entity = self._get_focus_entity()
        needs_rescale = self.camera.update(keys, ZOOM_SPEED, SCROLL_SPEED, focus_entity)

        if needs_rescale:
            self.asset_manager.rescale_textures(self.camera.tile_size)
            self.renderer.create_glow_surfaces(self.camera.tile_size)
            self.renderer.set_money_sprite(self.asset_manager.get_money_sprite())
            self.renderer.set_fog_tile(self.asset_manager.get_fog_tile())

        # Update hovered tile
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
                self.red_team,
                self.blue_team,
                self.money_pickups,
                self.fog_of_war,
                self.ui_manager,
                self.game_state,
                self.hovered_tile,
                self.animation_timer,
            )


if __name__ == "__main__":
    game = Game()
    game.run()
