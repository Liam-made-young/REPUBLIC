import math
import time

import pygame
from assets import AssetManager
from camera import Camera
from capital import Capital
from character import Character, CharacterType
from fog_of_war import FogOfWar
from game_state import GameState
from main_menu import PLAYER_COLORS, MainMenu
from money import Money
from renderer import MapRenderer
from seer import Seer
from team import Team, TeamSide
from ui import UIManager
from world import WorldGenerator

# --- Screen Constants ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 800

# --- Default Game Constants ---
DEFAULT_MAP_WIDTH = 125
DEFAULT_MAP_HEIGHT = 125
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

        # Initialize asset manager (always needed)
        self.asset_manager = AssetManager()

        # Initialize main menu
        self.main_menu = MainMenu(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.main_menu.open_menu()  # Start with menu open

        # Game state - will be initialized when game starts
        self.game_initialized = False
        self.game_state = None
        self.teams = []
        self.world = None
        self.world_generator = None
        self.camera = None
        self.renderer = None
        self.fog_of_war = None
        self.ui_manager = None
        self.money_pickups = []

        # Map dimensions (set from menu)
        self.map_width = DEFAULT_MAP_WIDTH
        self.map_height = DEFAULT_MAP_HEIGHT

        # UI state
        self.hovered_tile = None
        self.animation_timer = 0

        # Timers
        self.game_start_time = None
        self.turn_start_time = None
        self.total_game_time = 0
        self.current_turn_time = 0

    def run(self):
        """Starts and runs the main game loop."""
        print("Loading assets...")
        self.asset_manager.load_assets()

        # Create renderer for menu background
        self.renderer = MapRenderer(self.screen)

        print("Game ready. Opening main menu.")

        while self.running:
            self.events()
            self.update()
            self.draw()
            self.clock.tick(60)

        pygame.quit()

    def _initialize_game(self, game_settings):
        """Initializes a new game with the given settings."""
        print("Initializing new game...")

        # Get map dimensions from settings
        self.map_width, self.map_height = game_settings.get_map_dimensions()
        print(f"Map size: {self.map_width}x{self.map_height}")

        # Initialize world generator
        self.world_generator = WorldGenerator(self.map_width, self.map_height)

        # Initialize camera
        self.camera = Camera(
            SCREEN_WIDTH,
            SCREEN_HEIGHT,
            self.map_width,
            self.map_height,
            INITIAL_TILE_SIZE,
        )

        # Create scaled textures and glow surfaces
        self.asset_manager.rescale_textures(self.camera.tile_size)
        self.renderer.create_glow_surfaces(self.camera.tile_size)

        # Set up renderer with money sprite and fog tile
        self.renderer.set_money_sprite(self.asset_manager.get_money_sprite())
        self.renderer.set_fog_tile(self.asset_manager.get_fog_tile())

        # Initialize game state
        self.game_state = GameState(num_players=game_settings.num_players)

        # Initialize teams from player settings
        self.teams = []
        team_sides = [
            TeamSide.PLAYER_1,
            TeamSide.PLAYER_2,
            TeamSide.PLAYER_3,
            TeamSide.PLAYER_4,
        ]

        for i, player_setup in enumerate(game_settings.players):
            color_data = player_setup.get_color_data()
            team = Team(
                side=team_sides[i],
                player_name=player_setup.name,
                color_key=player_setup.color_key,
                color_data={
                    "rgb": color_data["rgb"],
                    "light": color_data["light"],
                    "dark": color_data["dark"],
                },
            )
            self.teams.append(team)
            print(f"Created team: {team}")

        # Initialize fog of war
        self.fog_of_war = FogOfWar(self.map_width, self.map_height)

        # Initialize UI Manager
        self.ui_manager = UIManager(SCREEN_WIDTH, SCREEN_HEIGHT)

        # Generate world
        print("Generating world...")
        self.world = self.world_generator.generate()
        print("World generation complete.")

        # Generate money pickups
        self._generate_money()

        # Set up starting capitals and characters
        self._setup_starting_positions()

        # Update fog of war for all teams
        for team in self.teams:
            self.fog_of_war.update_team_visibility(team)

        # Center camera on first team's starting capital
        if self.teams and self.teams[0].capitals:
            self.camera.center_on_entity(self.teams[0].capitals[0])

        # Initialize timers
        self.game_start_time = time.time()
        self.turn_start_time = time.time()
        self.total_game_time = 0
        self.current_turn_time = 0

        self.game_initialized = True
        print("Game initialization complete.")

    def _generate_money(self):
        """Generates money pickups across the map."""
        self.money_pickups = Money.generate_money_positions(
            self.world.world_map, self.map_width, self.map_height
        )
        print(f"Generated {len(self.money_pickups)} money pickups.")

    def _setup_starting_positions(self):
        """Sets up starting capitals and characters for all teams."""
        num_teams = len(self.teams)

        # Calculate capital positions based on number of teams
        # For 2 players: left and right
        # For 3 players: triangle formation
        # For 4 players: four corners
        capital_positions = self._calculate_capital_positions(num_teams)

        for i, team in enumerate(self.teams):
            if i < len(capital_positions):
                cap_x, cap_y = capital_positions[i]

                # Ensure position is valid (not water)
                cap_y = self._find_valid_capital_y(cap_x, cap_y)

                # Create starting capital
                capital = Capital(cap_x, cap_y, team)
                team.add_capital(capital)

                # Create starting warrior
                char = self._create_starting_character(
                    team, capital, CharacterType.WARRIOR
                )
                if char:
                    team.add_character(char)

                print(f"{team.name} capital at ({cap_x}, {cap_y})")

    def _calculate_capital_positions(self, num_teams):
        """Calculates starting capital positions based on team count."""
        positions = []
        center_x = self.map_width // 2
        center_y = self.map_height // 2

        if num_teams == 2:
            # Left and right
            positions = [
                (CAPITAL_MARGIN, center_y),
                (self.map_width - CAPITAL_MARGIN - 1, center_y),
            ]
        elif num_teams == 3:
            # Triangle formation
            positions = [
                (CAPITAL_MARGIN, center_y),
                (self.map_width - CAPITAL_MARGIN - 1, CAPITAL_MARGIN),
                (
                    self.map_width - CAPITAL_MARGIN - 1,
                    self.map_height - CAPITAL_MARGIN - 1,
                ),
            ]
        elif num_teams == 4:
            # Four corners
            positions = [
                (CAPITAL_MARGIN, CAPITAL_MARGIN),
                (self.map_width - CAPITAL_MARGIN - 1, CAPITAL_MARGIN),
                (CAPITAL_MARGIN, self.map_height - CAPITAL_MARGIN - 1),
                (
                    self.map_width - CAPITAL_MARGIN - 1,
                    self.map_height - CAPITAL_MARGIN - 1,
                ),
            ]

        return positions

    def _find_valid_capital_y(self, x, preferred_y):
        """Finds a valid y position for a capital at the given x coordinate."""
        # Try preferred position first, then expand outward
        for offset in range(0, self.map_height // 2):
            for y in [preferred_y + offset, preferred_y - offset]:
                if 0 <= y < self.map_height:
                    tile = self.world.world_map[y][x]
                    if tile != "water":
                        return y
        return preferred_y  # Fallback

    def _create_starting_character(self, team, capital, char_type):
        """Creates a starting character next to a capital."""
        spawn_positions = capital.get_spawn_positions()

        for pos in spawn_positions:
            x, y = pos
            if 0 <= x < self.map_width and 0 <= y < self.map_height:
                tile = self.world.world_map[y][x]
                if tile != "water":
                    char = Character(x, y, team, char_type)
                    # Set the sprite based on character type and team color
                    sprite = self.asset_manager.get_character_sprite(
                        char_type, team.color_key
                    )
                    char.set_sprite(sprite)
                    return char
        return None

    def events(self):
        """Handles user input and events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                continue

            # Check for menu button click first (before other handling)
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.main_menu.menu_button_rect.collidepoint(event.pos):
                    self.main_menu.toggle_menu()
                    continue

            # Handle main menu events (when menu is open)
            if self.main_menu.is_open:
                result = self.main_menu.handle_event(event, from_menu_button=False)
                if result == "new_game":
                    # Start a new game with current settings
                    self._initialize_game(self.main_menu.get_game_settings())
                elif result == "resume":
                    # Just close the menu
                    pass
                continue

            # Game events (only when menu is closed and game is initialized)
            if not self.game_initialized:
                continue

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.game_state.show_character_menu:
                        self.game_state.close_character_menu()
                    elif self.game_state.show_creation_menu:
                        self.game_state.close_all_menus()
                    else:
                        # Open main menu
                        self.main_menu.open_menu()
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
        # Process seer movements for the current team before ending turn
        current_team = self._get_current_team()
        if current_team:
            self._process_seer_movements(current_team)

        self.game_state.end_turn(self.teams)

        # Reset turn timer
        self.turn_start_time = time.time()

        # Update fog of war for the new active team
        current_team = self._get_current_team()
        if current_team:
            self.fog_of_war.update_team_visibility(current_team)

            # Center camera on the new team's first capital or character
            self._center_camera_on_team(current_team)

    def _process_seer_movements(self, team):
        """Processes automatic seer movements for a team."""
        if not hasattr(team, "seers") or not team.seers:
            return

        # Gather all characters and capitals for collision detection
        all_chars = []
        all_capitals = []
        for t in self.teams:
            all_chars.extend(t.characters)
            all_capitals.extend(t.capitals)

        # Process each seer's movements
        for seer in team.seers:
            # Seers move multiple times per turn
            while seer.can_act():
                moved = seer.perform_auto_move(
                    self.world,
                    team,
                    all_chars,
                    all_capitals,
                    self.map_width,
                    self.map_height,
                )
                if not moved:
                    break

                # Update fog of war after each move
                self.fog_of_war.update_team_visibility(team)

            seer.has_acted_this_turn = True

    def _get_current_team(self):
        """Returns the team whose turn it is."""
        return self.game_state.get_current_team(self.teams)

    def _center_camera_on_team(self, team):
        """Centers the camera on a team's capital or character."""
        if team.capitals:
            self.camera.center_on_entity(team.capitals[0])
        elif team.get_living_characters():
            self.camera.center_on_entity(team.get_living_characters()[0])

    def _get_focus_entity(self):
        """Returns the entity that should be the focus for camera operations."""
        if self.game_state and self.game_state.selected_character:
            return self.game_state.selected_character

        current_team = self._get_current_team()
        if current_team:
            if current_team.capitals:
                return current_team.capitals[0]
            elif current_team.get_living_characters():
                return current_team.get_living_characters()[0]

        # Fallback to center of map
        class MapCenter:
            def __init__(self, map_w, map_h):
                self.x = map_w // 2
                self.y = map_h // 2

        return MapCenter(self.map_width, self.map_height)

    def handle_mouse_click(self, mouse_pos):
        """Handles all logic for mouse clicks."""
        # Menu button is handled in events() now to prevent duplication

        if not self.game_initialized or self.game_state.game_over:
            return

        current_team = self._get_current_team()
        if not current_team:
            return

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

        # Handle creation menu mode (placing capital or spawning seer)
        if self.game_state.show_creation_menu:
            # Check if clicking seer spawn button
            if hasattr(self.ui_manager, "seer_button_rect"):
                if self.ui_manager.seer_button_rect.collidepoint(mouse_pos):
                    self._handle_seer_spawn(current_team)
                    return
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
            self._handle_character_action(tile_x, tile_y, current_team)

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
        if not (0 <= tile_x < self.map_width and 0 <= tile_y < self.map_height):
            return

        tile = self.world.world_map[tile_y][tile_x]
        if tile == "water":
            return

        # Check distance from all capitals
        all_capitals = []
        for team in self.teams:
            all_capitals.extend(team.capitals)

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

    def _handle_seer_spawn(self, current_team):
        """Handles spawning a seer from the nearest capital."""
        # Check if team can afford
        if not current_team.can_afford(Seer.COST):
            return

        # Find a capital with valid spawn position
        for capital in current_team.capitals:
            spawn_pos = self._find_spawn_position(capital)
            if spawn_pos:
                # Create the seer
                current_team.spend_money(Seer.COST)
                new_seer = Seer(spawn_pos[0], spawn_pos[1], current_team)

                # Set sprite
                sprite = self.asset_manager.get_seer_sprite(current_team.color_key)
                new_seer.set_sprite(sprite)

                current_team.add_seer(new_seer)

                # Update fog of war
                self.fog_of_war.update_team_visibility(current_team)

                print(f"Spawned seer at ({spawn_pos[0]}, {spawn_pos[1]})")
                return

        print("No valid spawn position for seer")

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
        sprite = self.asset_manager.get_character_sprite(
            char_type, current_team.color_key
        )
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

        all_chars = []
        all_capitals = []
        for team in self.teams:
            all_chars.extend(team.characters)
            all_capitals.extend(team.capitals)

        for pos in spawn_positions:
            x, y = pos
            if not (0 <= x < self.map_width and 0 <= y < self.map_height):
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

    def _handle_character_action(self, tile_x, tile_y, current_team):
        """Handles movement or attack for the selected character."""
        selected = self.game_state.selected_character

        if not selected or not selected.can_act():
            return

        # Check if tile is revealed
        if not current_team.is_tile_revealed(tile_x, tile_y):
            return

        # Get all enemy teams
        enemy_teams = [t for t in self.teams if t != current_team]

        # Check if attacking an enemy character
        for enemy_team in enemy_teams:
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
                        self.game_state.check_victory_conditions(self.teams)

                        # Deselect after action
                        self.game_state.deselect_character()
                    return

        # Check if conquering an enemy capital
        for enemy_team in enemy_teams:
            for capital in enemy_team.capitals:
                if capital.x == tile_x and capital.y == tile_y:
                    if selected.is_in_range(tile_x, tile_y):
                        # Check if capital is unprotected
                        all_chars = []
                        for t in self.teams:
                            all_chars.extend(t.characters)

                        if not capital.is_protected(all_chars):
                            # Conquer the capital!
                            enemy_team.remove_capital(capital)
                            selected.has_moved = True

                            # Check victory conditions
                            self.game_state.check_victory_conditions(self.teams)

                            self.game_state.deselect_character()
                    return

        # Check if moving to a valid tile
        if selected.is_valid_move(tile_x, tile_y):
            # Check bounds
            if not (0 <= tile_x < self.map_width and 0 <= tile_y < self.map_height):
                return

            # Check if tile is walkable
            tile = self.world.world_map[tile_y][tile_x]
            if tile == "water":
                return

            # Check if occupied by character
            all_chars = []
            for t in self.teams:
                all_chars.extend(t.characters)
            occupied = any(
                c.x == tile_x and c.y == tile_y and not c.is_dead() for c in all_chars
            )
            if occupied:
                return

            # Check if occupied by capital
            all_capitals = []
            for t in self.teams:
                all_capitals.extend(t.capitals)
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

        # Update timers
        if self.game_initialized and self.game_start_time:
            self.total_game_time = time.time() - self.game_start_time
            if self.turn_start_time:
                self.current_turn_time = time.time() - self.turn_start_time

        # Only update game state if initialized and menu is closed
        if not self.game_initialized or self.main_menu.is_open:
            return

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
        # Clear screen
        self.screen.fill((15, 12, 10))

        # Draw game if initialized
        if self.game_initialized and self.world:
            current_team = self._get_current_team()
            if current_team:
                self.renderer.draw(
                    self.world,
                    self.camera,
                    self.asset_manager.scaled_textures,
                    self.teams,
                    self.money_pickups,
                    self.fog_of_war,
                    self.ui_manager,
                    self.game_state,
                    self.hovered_tile,
                    self.animation_timer,
                    current_team,
                )

        # Draw main menu (always draws button, timers, and full menu when open)
        self.main_menu.draw(
            self.screen,
            game_in_progress=self.game_initialized,
            turn_time=self.current_turn_time,
            total_time=self.total_game_time,
        )

        pygame.display.flip()


if __name__ == "__main__":
    game = Game()
    game.run()
