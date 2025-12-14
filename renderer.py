import math

import pygame

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

# Team glow colors
RED_GLOW_COLOR = (255, 80, 80)
BLUE_GLOW_COLOR = (80, 150, 255)

# Hover and attack colors
HOVER_GLOW_COLOR = (255, 255, 255)
ATTACK_HOVER_GLOW_COLOR = (255, 100, 0)

# Capital glow colors
CAPITAL_GLOW_RED = (180, 60, 60)
CAPITAL_GLOW_BLUE = (60, 100, 180)

# Money glow color
MONEY_GLOW_COLOR = (255, 215, 0)


class MapRenderer:
    """Handles rendering of the game world, characters, capitals, and effects."""

    def __init__(self, screen):
        self.screen = screen

        # Glow surfaces
        self.red_glow_surf = None
        self.blue_glow_surf = None
        self.hover_glow_surf = None
        self.attack_hover_glow_surf = None
        self.capital_glow_red_surf = None
        self.capital_glow_blue_surf = None
        self.money_glow_surf = None

        # Capital font
        self.capital_font = None

        # Money sprite
        self.money_sprite = None

        # Fog tile
        self.fog_tile = None

    def create_glow_surfaces(self, tile_size):
        """Create gradient glow surfaces for various effects."""
        # Character glows
        self.red_glow_surf = self._create_gradient_circle(
            int(tile_size * 1.2), RED_GLOW_COLOR
        )
        self.blue_glow_surf = self._create_gradient_circle(
            int(tile_size * 1.2), BLUE_GLOW_COLOR
        )

        # Hover glows
        self.hover_glow_surf = self._create_gradient_circle(
            int(tile_size * 1.0), HOVER_GLOW_COLOR
        )
        self.attack_hover_glow_surf = self._create_gradient_circle(
            int(tile_size * 1.2), ATTACK_HOVER_GLOW_COLOR
        )

        # Capital glows (larger)
        self.capital_glow_red_surf = self._create_gradient_circle(
            int(tile_size * 2.0), CAPITAL_GLOW_RED
        )
        self.capital_glow_blue_surf = self._create_gradient_circle(
            int(tile_size * 2.0), CAPITAL_GLOW_BLUE
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
        red_team,
        blue_team,
        money_pickups,
        fog_of_war,
        ui_manager,
        game_state,
        hovered_tile,
        animation_timer,
    ):
        """Draws all game elements to the screen."""
        self.screen.fill(BLACK)

        # Get current team for fog of war
        from team import TeamSide

        current_team = red_team if game_state.is_red_turn() else blue_team

        # Draw map with fog of war
        self._draw_map(world, camera, textures, current_team, fog_of_war)

        # Draw money pickups (only visible ones)
        self._draw_money(money_pickups, camera, current_team, animation_timer)

        # Draw capital glow effects
        self._draw_capital_glows(
            red_team, blue_team, camera, current_team, animation_timer
        )

        # Draw capitals
        self._draw_capitals(red_team, blue_team, camera, current_team)

        # Draw character effects and characters
        self._draw_character_effects(
            red_team,
            blue_team,
            camera,
            game_state,
            hovered_tile,
            animation_timer,
            current_team,
        )
        self._draw_characters(red_team, blue_team, camera, current_team)

        # UI is drawn last, on top of everything
        ui_manager.draw(self.screen, game_state, red_team, blue_team)

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

    def _draw_capital_glows(
        self, red_team, blue_team, camera, current_team, animation_timer
    ):
        """Draws glow effects around capitals."""
        pulse = (math.sin(animation_timer * 0.08) + 1) / 2

        # Draw red team capitals
        for capital in red_team.capitals:
            # Only draw if visible
            if not current_team.is_tile_revealed(capital.x, capital.y):
                continue

            if self.capital_glow_red_surf:
                glow_alpha = int(60 + pulse * 40)
                self.capital_glow_red_surf.set_alpha(glow_alpha)
                self._blit_centered_on_tile(
                    self.capital_glow_red_surf, capital.x, capital.y, camera
                )

        # Draw blue team capitals
        for capital in blue_team.capitals:
            if not current_team.is_tile_revealed(capital.x, capital.y):
                continue

            if self.capital_glow_blue_surf:
                glow_alpha = int(60 + pulse * 40)
                self.capital_glow_blue_surf.set_alpha(glow_alpha)
                self._blit_centered_on_tile(
                    self.capital_glow_blue_surf, capital.x, capital.y, camera
                )

    def _draw_capitals(self, red_team, blue_team, camera, current_team):
        """Draws capital buildings."""
        all_capitals = red_team.capitals + blue_team.capitals

        for capital in all_capitals:
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
        red_team,
        blue_team,
        camera,
        game_state,
        hovered_tile,
        animation_timer,
        current_team,
    ):
        """Draws glow effects for characters."""
        pulse = (math.sin(animation_timer * 0.1) + 1) / 2

        # Draw glows for all visible characters
        all_characters = red_team.characters + blue_team.characters

        for char in all_characters:
            if char.is_dead():
                continue

            # Only draw if visible to current team
            if not current_team.is_tile_revealed(char.x, char.y):
                continue

            # Determine glow color based on team
            from team import TeamSide

            if char.team.side == TeamSide.RED:
                glow_surf = self.red_glow_surf
            else:
                glow_surf = self.blue_glow_surf

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
                red_team,
                blue_team,
                camera,
                game_state,
                hovered_tile,
                animation_timer,
                current_team,
            )

    def _draw_hover_effects(
        self,
        red_team,
        blue_team,
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
            enemy_team = blue_team if current_team.side == red_team.side else red_team
            target_enemy = None

            for enemy in enemy_team.characters:
                if not enemy.is_dead() and enemy.x == htx and enemy.y == hty:
                    target_enemy = enemy
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
                all_chars = red_team.characters + blue_team.characters
                occupied = any(
                    c.x == htx and c.y == hty and not c.is_dead() for c in all_chars
                )

                all_capitals = red_team.capitals + blue_team.capitals
                capital_occupied = any(c.x == htx and c.y == hty for c in all_capitals)

                if not occupied and not capital_occupied:
                    # Show movement hover glow
                    if self.hover_glow_surf:
                        self._blit_centered_on_tile(
                            self.hover_glow_surf, htx, hty, camera
                        )

    def _draw_characters(self, red_team, blue_team, camera, current_team):
        """Draws all characters."""
        all_characters = red_team.characters + blue_team.characters

        for char in all_characters:
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

            # Draw health bar above character if damaged
            if char.health < char.max_health:
                self._draw_character_health_bar(
                    char, screen_x, screen_y, camera.tile_size
                )

    def _draw_character_health_bar(self, char, screen_x, screen_y, tile_size):
        """Draws a small health bar above a character."""
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
            from team import TeamSide

            if char.team.side == TeamSide.RED:
                fill_color = (180, 50, 50)
            else:
                fill_color = (50, 100, 180)

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
