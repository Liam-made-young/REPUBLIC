import math

import pygame

# UI Colors
BLACK = (0, 0, 0)
PLAYER_GLOW_COLOR = (255, 255, 0)  # Yellow
HOVER_GLOW_COLOR = (255, 255, 255)  # White
ENEMY_GLOW_COLOR = (255, 0, 0)  # Red
ATTACK_HOVER_GLOW_COLOR = (255, 100, 0)  # Orange for attack hover


class MapRenderer:
    def __init__(self, screen):
        self.screen = screen
        self.player_glow_surf = None
        self.hover_glow_surf = None
        self.enemy_glow_surf = None
        self.attack_hover_glow_surf = None

    def create_glow_surfaces(self, tile_size):
        """Create multi-layered, gradient surfaces for glow effects."""
        self.player_glow_surf = self._create_gradient_circle(
            int(tile_size * 1.2), PLAYER_GLOW_COLOR
        )
        self.hover_glow_surf = self._create_gradient_circle(
            int(tile_size * 1.0), HOVER_GLOW_COLOR
        )
        self.enemy_glow_surf = self._create_gradient_circle(
            int(tile_size * 1.2), ENEMY_GLOW_COLOR
        )
        self.attack_hover_glow_surf = self._create_gradient_circle(
            int(tile_size * 1.2), ATTACK_HOVER_GLOW_COLOR
        )

    def _create_gradient_circle(self, radius, color):
        """Creates a circular surface with a soft, gradient glow."""
        if radius <= 0:
            return None
        surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        # Draw several concentric circles with decreasing alpha to create a gradient
        for i in range(radius, 0, -2):
            alpha = 255 * (1 - (i / radius)) ** 1.5
            final_alpha = int(max(0, min(255, alpha * 1.2)))
            pygame.draw.circle(surf, (*color, final_alpha), (radius, radius), i)
        return surf

    def draw(
        self,
        world,
        camera,
        textures,
        player,
        enemy,
        ui_manager,
        game_state,
        hovered_tile,
        movement_range,
        animation_timer,
    ):
        """Draws all game elements to the screen."""
        self.screen.fill(BLACK)

        self._draw_map(world, camera, textures)
        self._draw_visual_effects(
            player,
            enemy,
            camera,
            hovered_tile,
            game_state,
            movement_range,
            animation_timer,
        )
        self._draw_enemy(enemy, camera, game_state)
        self._draw_player(player, camera, game_state)

        # UI is drawn last, on top of everything
        ui_manager.draw(self.screen, game_state, player, enemy)

        pygame.display.flip()

    def _draw_map(self, world, camera, textures):
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
                tile_type = world.world_map[y][x]
                if tile_type in textures:
                    screen_x = x * camera.tile_size - camera.offset_x
                    screen_y = y * camera.tile_size - camera.offset_y
                    self.screen.blit(textures[tile_type], (screen_x, screen_y))

    def _draw_visual_effects(
        self,
        player,
        enemy,
        camera,
        hovered_tile,
        game_state,
        movement_range,
        animation_timer,
    ):
        # Use a sine wave for a smooth pulse effect
        pulse = (math.sin(animation_timer * 0.1) + 1) / 2  # Varies between 0 and 1

        # Draw player glow with a pulsing animation
        if self.player_glow_surf and not player.is_dead():
            if game_state.is_player_turn():
                # Brighter glow when it's player's turn
                dynamic_alpha = 100 + pulse * 100  # Varies between 100 and 200
            else:
                # Dimmer glow when it's not player's turn
                dynamic_alpha = 50 + pulse * 30  # Varies between 50 and 80
            self.player_glow_surf.set_alpha(dynamic_alpha)
            self._blit_centered_on_tile(
                self.player_glow_surf, player.x, player.y, camera
            )

        # Draw enemy glow with a pulsing animation
        if self.enemy_glow_surf and enemy and not enemy.is_dead():
            if game_state.is_enemy_turn():
                # Brighter glow when it's enemy's turn
                dynamic_alpha = 100 + pulse * 100  # Varies between 100 and 200
            else:
                # Dimmer glow when it's not enemy's turn
                dynamic_alpha = 50 + pulse * 30  # Varies between 50 and 80
            self.enemy_glow_surf.set_alpha(dynamic_alpha)
            self._blit_centered_on_tile(self.enemy_glow_surf, enemy.x, enemy.y, camera)

        # Draw hover glow based on context (move or attack)
        if hovered_tile and not game_state.game_over:
            htx, hty = hovered_tile

            if game_state.is_player_turn() and not game_state.player_has_moved:
                # Check if hovering over enemy (attack)
                if enemy and htx == enemy.x and hty == enemy.y and not enemy.is_dead():
                    # Check if enemy is in range
                    if player.is_valid_move(htx, hty, movement_range):
                        # Show attack hover glow on enemy
                        if self.attack_hover_glow_surf:
                            attack_pulse = (math.sin(animation_timer * 0.2) + 1) / 2
                            self.attack_hover_glow_surf.set_alpha(
                                150 + attack_pulse * 105
                            )
                            self._blit_centered_on_tile(
                                self.attack_hover_glow_surf, htx, hty, camera
                            )
                elif self.hover_glow_surf:
                    # Player's turn - show hover for player movement
                    if player.is_valid_move(htx, hty, movement_range):
                        self._blit_centered_on_tile(
                            self.hover_glow_surf, htx, hty, camera
                        )

            elif game_state.is_enemy_turn() and not game_state.enemy_has_moved:
                # Check if hovering over player (attack)
                if htx == player.x and hty == player.y and not player.is_dead():
                    # Check if player is in range
                    if enemy and enemy.is_valid_move(htx, hty, movement_range):
                        # Show attack hover glow on player
                        if self.attack_hover_glow_surf:
                            attack_pulse = (math.sin(animation_timer * 0.2) + 1) / 2
                            self.attack_hover_glow_surf.set_alpha(
                                150 + attack_pulse * 105
                            )
                            self._blit_centered_on_tile(
                                self.attack_hover_glow_surf, htx, hty, camera
                            )
                elif self.hover_glow_surf and enemy:
                    # Enemy's turn - show hover for enemy movement (pass to play)
                    if enemy.is_valid_move(htx, hty, movement_range):
                        self._blit_centered_on_tile(
                            self.hover_glow_surf, htx, hty, camera
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

    def _draw_player(self, player, camera, game_state):
        if not player.sprite or player.is_dead():
            return

        scaled_sprite = pygame.transform.scale(
            player.sprite, (camera.tile_size, camera.tile_size)
        )

        screen_x = player.x * camera.tile_size - camera.offset_x
        screen_y = player.y * camera.tile_size - camera.offset_y

        self.screen.blit(scaled_sprite, (screen_x, screen_y))

    def _draw_enemy(self, enemy, camera, game_state):
        """Draws the enemy with its inverted sprite."""
        if not enemy or enemy.is_dead():
            return

        sprite = enemy.get_display_sprite()
        if not sprite:
            return

        scaled_sprite = pygame.transform.scale(
            sprite, (camera.tile_size, camera.tile_size)
        )

        screen_x = enemy.x * camera.tile_size - camera.offset_x
        screen_y = enemy.y * camera.tile_size - camera.offset_y

        self.screen.blit(scaled_sprite, (screen_x, screen_y))
