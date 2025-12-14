import math

import pygame

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

# Hover and attack colors
HOVER_GLOW_COLOR = (255, 255, 255)
ATTACK_HOVER_GLOW_COLOR = (255, 100, 0)

# Money glow color
MONEY_GLOW_COLOR = (255, 215, 0)


class MapRenderer:
    """Handles rendering of the game world, characters, capitals, and effects."""

    def __init__(self, screen):
        self.screen = screen

        # Glow surfaces - now cached by color
        self.glow_cache = {}  # {(r, g, b, size): surface}
        self.hover_glow_surf = None
        self.attack_hover_glow_surf = None
        self.money_glow_surf = None

        # Capital font
        self.capital_font = None

        # Name label font
        self.name_font = None

        # Money sprite
        self.money_sprite = None

        # Fog tile
        self.fog_tile = None

        # Current tile size for caching
        self.current_tile_size = 0

    def create_glow_surfaces(self, tile_size):
        """Create gradient glow surfaces for various effects."""
        self.current_tile_size = tile_size

        # Clear glow cache when tile size changes
        self.glow_cache = {}

        # Hover glows
        self.hover_glow_surf = self._create_gradient_circle(
            int(tile_size * 1.0), HOVER_GLOW_COLOR
        )
        self.attack_hover_glow_surf = self._create_gradient_circle(
            int(tile_size * 1.2), ATTACK_HOVER_GLOW_COLOR
        )

        # Money glow
        self.money_glow_surf = self._create_gradient_circle(
            int(tile_size * 0.8), MONEY_GLOW_COLOR
        )

        # Capital font
        try:
            self.capital_font = pygame.font.SysFont("Georgia", tile_size, bold=True)
        except pygame.error:
            self.capital_font = pygame.font.Font(None, tile_size)

        # Name label font (smaller)
        try:
            self.name_font = pygame.font.SysFont(
                "Georgia", max(10, tile_size // 3), bold=True
            )
        except pygame.error:
            self.name_font = pygame.font.Font(None, max(12, tile_size // 3))

    def _get_glow_surface(self, color, size_multiplier=1.2):
        """Gets or creates a glow surface for the given color."""
        size = int(self.current_tile_size * size_multiplier)
        cache_key = (color[0], color[1], color[2], size)

        if cache_key not in self.glow_cache:
            self.glow_cache[cache_key] = self._create_gradient_circle(size, color)

        return self.glow_cache[cache_key]

    def _create_gradient_circle(self, radius, color):
        """Creates a circular surface with a soft, gradient glow."""
        if radius <= 0:
            return None

        surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)

        for i in range(radius, 0, -2):
            alpha = 255 * (1 - (i / radius)) ** 1.5
            final_alpha = int(max(0, min(255, alpha * 1.2)))
            pygame.draw.circle(surf, (*color, final_alpha), (radius, radius), i)

        return surf

    def set_money_sprite(self, money_sprite):
        """Sets the money sprite for rendering."""
        self.money_sprite = money_sprite

    def set_fog_tile(self, fog_tile):
        """Sets the fog of war tile for rendering."""
        self.fog_tile = fog_tile

    def draw(
        self,
        world,
        camera,
        textures,
        teams,
        money_pickups,
        fog_of_war,
        ui_manager,
        game_state,
        hovered_tile,
        animation_timer,
        current_team,
    ):
        """Draws all game elements to the screen."""
        self.screen.fill(BLACK)

        # Draw map with fog of war
        self._draw_map(world, camera, textures, current_team, fog_of_war)

        # Draw money pickups (only visible ones)
        self._draw_money(money_pickups, camera, current_team, animation_timer)

        # Draw capital glow effects
        self._draw_capital_glows(teams, camera, current_team, animation_timer)

        # Draw capitals
        self._draw_capitals(teams, camera, current_team)

        # Draw seer effects and seers
        self._draw_seer_effects(teams, camera, animation_timer, current_team)
        self._draw_seers(teams, camera, current_team)

        # Draw character effects and characters
        self._draw_character_effects(
            teams,
            camera,
            game_state,
            hovered_tile,
            animation_timer,
            current_team,
        )
        self._draw_characters(teams, camera, current_team)

        # UI is drawn last, on top of everything
        ui_manager.draw(self.screen, game_state, teams)

        pygame.display.flip()

    def _draw_map(self, world, camera, textures, current_team, fog_of_war):
        """Draws the game map with fog of war."""
        # Culling logic to only draw visible tiles
        start_col = max(0, camera.offset_x // camera.tile_size)
        end_col = min(
            world.width, (camera.offset_x + camera.screen_width) // camera.tile_size + 2
        )
        start_row = max(0, camera.offset_y // camera.tile_size)
        end_row = min(
            world.height,
            (camera.offset_y + camera.screen_height) // camera.tile_size + 2,
        )

        for y in range(start_row, end_row):
            for x in range(start_col, end_col):
                screen_x = x * camera.tile_size - camera.offset_x
                screen_y = y * camera.tile_size - camera.offset_y

                # Check if tile is revealed
                if current_team.is_tile_revealed(x, y):
                    # Draw normal tile
                    tile_type = world.world_map[y][x]
                    if tile_type in textures:
                        self.screen.blit(textures[tile_type], (screen_x, screen_y))
                else:
                    # Draw fog tile
                    if self.fog_tile:
                        self.screen.blit(self.fog_tile, (screen_x, screen_y))
                    else:
                        # Fallback: draw dark gray
                        pygame.draw.rect(
                            self.screen,
                            (40, 40, 45),
                            (screen_x, screen_y, camera.tile_size, camera.tile_size),
                        )

    def _draw_money(self, money_pickups, camera, current_team, animation_timer):
        """Draws money pickups with glow effect."""
        if not self.money_sprite:
            return

        pulse = (math.sin(animation_timer * 0.15) + 1) / 2

        for money in money_pickups:
            if money.collected:
                continue

            # Only draw if visible to current team
            if not current_team.is_tile_revealed(money.x, money.y):
                continue

            screen_x = money.x * camera.tile_size - camera.offset_x
            screen_y = money.y * camera.tile_size - camera.offset_y

            # Draw glow
            if self.money_glow_surf:
                glow_alpha = int(100 + pulse * 100)
                self.money_glow_surf.set_alpha(glow_alpha)
                self._blit_centered_on_tile(
                    self.money_glow_surf, money.x, money.y, camera
                )

            # Draw money sprite
            scaled_sprite = pygame.transform.scale(
                self.money_sprite, (camera.tile_size, camera.tile_size)
            )
            self.screen.blit(scaled_sprite, (screen_x, screen_y))

    def _draw_capital_glows(self, teams, camera, current_team, animation_timer):
        """Draws glow effects around capitals."""
        pulse = (math.sin(animation_timer * 0.08) + 1) / 2

        for team in teams:
            for capital in team.capitals:
                # Only draw if visible
                if not current_team.is_tile_revealed(capital.x, capital.y):
                    continue

                # Get glow surface in team's color
                glow_surf = self._get_glow_surface(team.dark_color, 2.0)

                if glow_surf:
                    glow_alpha = int(60 + pulse * 40)
                    glow_surf.set_alpha(glow_alpha)
                    self._blit_centered_on_tile(glow_surf, capital.x, capital.y, camera)

    def _draw_capitals(self, teams, camera, current_team):
        """Draws capital buildings."""
        for team in teams:
            for capital in team.capitals:
                # Only draw if visible
                if not current_team.is_tile_revealed(capital.x, capital.y):
                    continue

                screen_x = capital.x * camera.tile_size - camera.offset_x
                screen_y = capital.y * camera.tile_size - camera.offset_y

                # Use capital's draw method
                capital.draw_placeholder(
                    self.screen, screen_x, screen_y, camera.tile_size, self.capital_font
                )

    def _draw_character_effects(
        self,
        teams,
        camera,
        game_state,
        hovered_tile,
        animation_timer,
        current_team,
    ):
        """Draws glow effects for characters."""
        pulse = (math.sin(animation_timer * 0.1) + 1) / 2

        # Draw glows for all visible characters
        for team in teams:
            for char in team.characters:
                if char.is_dead():
                    continue

                # Only draw if visible to current team
                if not current_team.is_tile_revealed(char.x, char.y):
                    continue

                # Get glow surface in character's team color
                glow_surf = self._get_glow_surface(char.get_team_color(), 1.2)

                if glow_surf:
                    # Brighter glow for current team's characters
                    is_current_team = char.team == current_team
                    if is_current_team:
                        # Even brighter if selected
                        if game_state.selected_character == char:
                            dynamic_alpha = int(150 + pulse * 105)
                        else:
                            dynamic_alpha = int(100 + pulse * 80)
                    else:
                        dynamic_alpha = int(50 + pulse * 30)

                    glow_surf.set_alpha(dynamic_alpha)
                    self._blit_centered_on_tile(glow_surf, char.x, char.y, camera)

        # Draw hover effects
        if hovered_tile and not game_state.game_over:
            self._draw_hover_effects(
                teams,
                camera,
                game_state,
                hovered_tile,
                animation_timer,
                current_team,
            )

    def _draw_hover_effects(
        self,
        teams,
        camera,
        game_state,
        hovered_tile,
        animation_timer,
        current_team,
    ):
        """Draws hover glow effects for movement and attack."""
        htx, hty = hovered_tile
        pulse = (math.sin(animation_timer * 0.2) + 1) / 2

        # Only show hover effects when not in menus
        if game_state.show_creation_menu or game_state.show_character_menu:
            return

        selected = game_state.selected_character

        if selected and selected.can_act():
            # Check if hovering over an enemy (attack)
            target_enemy = None

            for team in teams:
                if team == current_team:
                    continue
                for enemy in team.characters:
                    if not enemy.is_dead() and enemy.x == htx and enemy.y == hty:
                        target_enemy = enemy
                        break
                if target_enemy:
                    break

            if target_enemy and selected.is_in_range(htx, hty):
                # Show attack hover glow
                if self.attack_hover_glow_surf:
                    attack_alpha = int(150 + pulse * 105)
                    self.attack_hover_glow_surf.set_alpha(attack_alpha)
                    self._blit_centered_on_tile(
                        self.attack_hover_glow_surf, htx, hty, camera
                    )
            elif selected.is_valid_move(htx, hty):
                # Check if tile is not occupied
                all_chars = []
                all_capitals = []
                for team in teams:
                    all_chars.extend(team.characters)
                    all_capitals.extend(team.capitals)

                occupied = any(
                    c.x == htx and c.y == hty and not c.is_dead() for c in all_chars
                )
                capital_occupied = any(c.x == htx and c.y == hty for c in all_capitals)

                if not occupied and not capital_occupied:
                    # Show movement hover glow
                    if self.hover_glow_surf:
                        self._blit_centered_on_tile(
                            self.hover_glow_surf, htx, hty, camera
                        )

    def _draw_seer_effects(self, teams, camera, animation_timer, current_team):
        """Draws glow effects for seers."""
        pulse = (
            math.sin(animation_timer * 0.15) + 1
        ) / 2  # Slightly faster pulse for seers

        for team in teams:
            if not hasattr(team, "seers"):
                continue

            for seer in team.seers:
                # Only draw if visible to current team
                if not current_team.is_tile_revealed(seer.x, seer.y):
                    continue

                # Get glow surface in seer's team color (slightly larger glow)
                glow_surf = self._get_glow_surface(seer.get_team_color(), 1.4)

                if glow_surf:
                    # Seers have a mystical pulsing glow
                    is_current_team = seer.team == current_team
                    if is_current_team:
                        dynamic_alpha = int(120 + pulse * 100)
                    else:
                        dynamic_alpha = int(60 + pulse * 40)

                    glow_surf.set_alpha(dynamic_alpha)
                    self._blit_centered_on_tile(glow_surf, seer.x, seer.y, camera)

    def _draw_seers(self, teams, camera, current_team):
        """Draws all seers with name labels."""
        for team in teams:
            if not hasattr(team, "seers"):
                continue

            for seer in team.seers:
                # Only draw if visible to current team
                if not current_team.is_tile_revealed(seer.x, seer.y):
                    continue

                sprite = seer.get_display_sprite()
                if not sprite:
                    continue

                screen_x = seer.x * camera.tile_size - camera.offset_x
                screen_y = seer.y * camera.tile_size - camera.offset_y

                scaled_sprite = pygame.transform.scale(
                    sprite, (camera.tile_size, camera.tile_size)
                )
                self.screen.blit(scaled_sprite, (screen_x, screen_y))

                # Draw player name above seer
                self._draw_seer_name(seer, screen_x, screen_y, camera.tile_size)

    def _draw_seer_name(self, seer, screen_x, screen_y, tile_size):
        """Draws the player's name above the seer sprite with 'Seer' suffix."""
        if not self.name_font:
            return

        # Get the team/player name with Seer suffix
        name = f"{seer.team.name}"

        # Render name text with team color
        text_color = seer.get_team_light_color()
        name_surf = self.name_font.render(name, True, text_color)

        # Create shadow for readability
        shadow_surf = self.name_font.render(name, True, (0, 0, 0))

        # Position above the sprite
        name_rect = name_surf.get_rect(
            centerx=screen_x + tile_size // 2, bottom=screen_y - 2
        )

        # Draw shadow slightly offset
        shadow_rect = name_rect.copy()
        shadow_rect.x += 1
        shadow_rect.y += 1
        self.screen.blit(shadow_surf, shadow_rect)

        # Draw main text
        self.screen.blit(name_surf, name_rect)

    def _draw_characters(self, teams, camera, current_team):
        """Draws all characters with name labels."""
        for team in teams:
            for char in team.characters:
                if char.is_dead():
                    continue

                # Only draw if visible to current team
                if not current_team.is_tile_revealed(char.x, char.y):
                    continue

                sprite = char.get_display_sprite()
                if not sprite:
                    continue

                screen_x = char.x * camera.tile_size - camera.offset_x
                screen_y = char.y * camera.tile_size - camera.offset_y

                scaled_sprite = pygame.transform.scale(
                    sprite, (camera.tile_size, camera.tile_size)
                )
                self.screen.blit(scaled_sprite, (screen_x, screen_y))

                # Draw player name above character
                self._draw_character_name(char, screen_x, screen_y, camera.tile_size)

                # Draw health bar above character if damaged
                if char.health < char.max_health:
                    self._draw_character_health_bar(
                        char, screen_x, screen_y, camera.tile_size
                    )

    def _draw_character_name(self, char, screen_x, screen_y, tile_size):
        """Draws the player's name above the character sprite."""
        if not self.name_font:
            return

        # Get the team/player name
        name = char.team.name

        # Render name text with team color
        text_color = char.get_team_light_color()
        name_surf = self.name_font.render(name, True, text_color)

        # Create shadow for readability
        shadow_surf = self.name_font.render(name, True, (0, 0, 0))

        # Position above the sprite
        name_rect = name_surf.get_rect(
            centerx=screen_x + tile_size // 2, bottom=screen_y - 2
        )

        # Draw shadow slightly offset
        shadow_rect = name_rect.copy()
        shadow_rect.x += 1
        shadow_rect.y += 1
        self.screen.blit(shadow_surf, shadow_rect)

        # Draw main text
        self.screen.blit(name_surf, name_rect)

    def _draw_character_health_bar(self, char, screen_x, screen_y, tile_size):
        """Draws a small health bar above a character (below the name)."""
        bar_width = tile_size - 4
        bar_height = 4
        bar_x = screen_x + 2
        bar_y = screen_y - 6

        # Background
        pygame.draw.rect(
            self.screen, (40, 35, 30), (bar_x, bar_y, bar_width, bar_height)
        )

        # Health fill
        health_ratio = char.health / char.max_health
        fill_width = int(bar_width * health_ratio)

        if fill_width > 0:
            # Color based on team
            fill_color = char.get_team_color()
            pygame.draw.rect(
                self.screen, fill_color, (bar_x, bar_y, fill_width, bar_height)
            )

        # Border
        pygame.draw.rect(
            self.screen, (80, 70, 55), (bar_x, bar_y, bar_width, bar_height), 1
        )

    def _blit_centered_on_tile(self, surface, tile_x, tile_y, camera):
        """Helper to draw a surface centered on a specific tile."""
        tile_screen_x = tile_x * camera.tile_size - camera.offset_x
        tile_screen_y = tile_y * camera.tile_size - camera.offset_y

        surf_rect = surface.get_rect()
        surf_rect.center = (
            tile_screen_x + camera.tile_size / 2,
            tile_screen_y + camera.tile_size / 2,
        )

        self.screen.blit(surface, surf_rect.topleft)
