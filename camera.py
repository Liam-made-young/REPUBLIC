import math

import pygame


class Camera:
    def __init__(
        self, screen_width, screen_height, map_width, map_height, initial_tile_size
    ):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.map_width = map_width
        self.map_height = map_height

        self.offset_x = 0
        self.offset_y = 0
        self.tile_size = initial_tile_size

        # Calculate dynamic zoom limits
        self.min_zoom_level = math.ceil(
            max(screen_width / map_width, screen_height / map_height)
        )
        self.max_zoom_level = int(min(screen_width / 5, screen_height / 5))

    def update(self, keys, zoom_speed, scroll_speed, player):
        """

        Updates camera position and zoom based on user input.

        Returns a boolean indicating if textures need to be rescaled.

        """

        # --- Handle Scrolling Input ---

        if self.map_width * self.tile_size > self.screen_width:
            if keys[pygame.K_a]:
                self.offset_x -= scroll_speed

            if keys[pygame.K_d]:
                self.offset_x += scroll_speed

        if self.map_height * self.tile_size > self.screen_height:
            if keys[pygame.K_w]:
                self.offset_y -= scroll_speed

            if keys[pygame.K_s]:
                self.offset_y += scroll_speed

        # --- Handle Zoom Input ---

        zoom_changed = False

        old_tile_size = self.tile_size

        if keys[pygame.K_e]:
            self.tile_size += zoom_speed

            zoom_changed = True

        if keys[pygame.K_q]:
            self.tile_size -= zoom_speed

            zoom_changed = True

        # Clamp zoom level

        self.tile_size = max(
            self.min_zoom_level, min(self.max_zoom_level, self.tile_size)
        )

        if zoom_changed and self.tile_size != old_tile_size:
            # Use player's position as the focal point for the zoom

            player_world_x = (player.x + 0.5) * old_tile_size

            player_world_y = (player.y + 0.5) * old_tile_size

            player_screen_x = player_world_x - self.offset_x

            player_screen_y = player_world_y - self.offset_y

            new_player_world_x = (player.x + 0.5) * self.tile_size

            new_player_world_y = (player.y + 0.5) * self.tile_size

            # Adjust offset to keep the player at the same screen position

            self.offset_x = new_player_world_x - player_screen_x

            self.offset_y = new_player_world_y - player_screen_y

            needs_rescale = True

        else:
            needs_rescale = False

        # --- Final Clamping and Centering ---

        self.clamp_and_center()

        return needs_rescale

    def clamp_and_center(self):
        map_width_px = self.map_width * self.tile_size
        map_height_px = self.map_height * self.tile_size
        # If map is wider than screen, clamp to boundaries. Otherwise, center it.
        if map_width_px > self.screen_width:
            self.offset_x = max(0, min(self.offset_x, map_width_px - self.screen_width))
        else:
            self.offset_x = (map_width_px - self.screen_width) / 2

        # If map is taller than screen, clamp to boundaries. Otherwise, center it.
        if map_height_px > self.screen_height:
            self.offset_y = max(
                0, min(self.offset_y, map_height_px - self.screen_height)
            )
        else:
            self.offset_y = (map_height_px - self.screen_height) / 2

        # Ensure camera offsets are integers for drawing
        self.offset_x = int(self.offset_x)
        self.offset_y = int(self.offset_y)
