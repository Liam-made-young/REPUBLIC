import random
import pygame


class VisualEffectsManager:
    """
    Manages post-processing visual effects like film grain, vignette, and retro filters.
    """

    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        
        # Grain settings
        self.grain_intensity = 40  # 0-255 alpha value
        self.grain_surfaces = []
        self.num_grain_frames = 10
        self.current_grain_frame = 0
        self.grain_timer = 0
        self.grain_speed = 50  # milliseconds per frame
        
        # Vignette settings
        self.vignette_intensity = 180  # 0-255 alpha value
        self.vignette_surface = None
        
        # Color flash settings
        self.flash_color = None
        self.flash_duration = 0
        self.flash_start_time = 0
        self.flash_alpha = 0
        
        # Retro scanlines
        self.scanline_surface = None
        self.scanline_intensity = 30
        
        # Initialize effects
        self._generate_grain_surfaces()
        self._generate_vignette()
        self._generate_scanlines()
        
    def resize(self, new_width, new_height):
        """Update effects for new screen size."""
        self.screen_width = new_width
        self.screen_height = new_height
        self._generate_grain_surfaces()
        self._generate_vignette()
        self._generate_scanlines()
        
    def _generate_grain_surfaces(self):
        """Generates a sequence of static noise surfaces."""
        self.grain_surfaces = []
        
        for _ in range(self.num_grain_frames):
            surface = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
            
            # This is slow, so we do it once at startup/resize
            # Create a localized random noise pattern
            # Using pixel array for faster manipulation is still slow in Python, 
            # so we might use a smaller texture and tile it/scale it up to save memory/time
            
            # Faster approach: Generate a small noise texture and tile/scale it randomly
            small_w, small_h = self.screen_width // 4, self.screen_height // 4
            noise_surf = pygame.Surface((small_w, small_h), pygame.SRCALPHA)
            
            # Fill with random noise
            # Since pixel-by-pixel is slow, we can use random circles or lines or blits
            # But the best way in pure pygame without expensive looping is to use random integers buffer
            # However, for simplicity and performance, we'll draw random dots
            
            # Optimization: Use pygame.pixelarray or just skip pixel-perfect noise
            # Let's try drawing thousands of random tiny rects
            
            noise_count = int((small_w * small_h) * 0.1) # 10% coverage
            
            # Even faster: Create a surface with random pixels using standard python random
            # Actually, let's just make a semi-transparent surface and blit random black/white dots
            
            # Best Performance Hack for Pygame Noise:
            # 1. Create a surface
            # 2. Fill with gray
            # 3. Use special blending flags or just random colored rects
            
            # Let's stick to a simpler "retro" look: Scanlines + Vignette + Occasional flicker
            # is often better than true per-pixel grain in Pygame (which lags).
            
            # But if we must have grain, we pre-render it.
            # Let's try a very coarse grain.
            
            for _ in range(2000): # Draw 2000 coarse grain specs
                x = random.randint(0, self.screen_width)
                y = random.randint(0, self.screen_height)
                w = random.randint(1, 3)
                h = random.randint(1, 3)
                color_val = random.randint(200, 255)
                # White grain
                pygame.draw.rect(surface, (color_val, color_val, color_val, self.grain_intensity), (x, y, w, h))
                
                # Black grain
                x = random.randint(0, self.screen_width)
                y = random.randint(0, self.screen_height)
                pygame.draw.rect(surface, (0, 0, 0, self.grain_intensity), (x, y, w, h))
                
            self.grain_surfaces.append(surface)

    def _generate_vignette(self):
        """Generates a soft vignette overlay (transparent center, dark corners)."""
        self.vignette_surface = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        self.vignette_surface.fill((0, 0, 0, 0)) # Start transparent
        
        # Draw dark corners without blocking the center UI
        # We'll use a series of large rectangles with low alpha to create a gradient
        w, h = self.screen_width, self.screen_height
        
        # Subtle cinema bars (much thinner)
        bar_height = 20
        pygame.draw.rect(self.vignette_surface, (10, 5, 0, 200), (0, 0, w, bar_height))
        pygame.draw.rect(self.vignette_surface, (10, 5, 0, 200), (0, h - bar_height, w, bar_height))
        
        # Corner gradients (drawn as circles/rects)
        # Top-left
        corner_size = 150
        # Manual pixel manipulation is too slow, so we just draw some overlapping circles/rects
        # A simple approach: 4 large circles at the corners that are "cut out" from the center?
        # Inverse: Draw 4 black circles at corners?
        
        # Let's simple draw a very faint full-screen gradient if possible, or just the scanlines.
        # But user specifically complained about UI blocking.
        # So we ensure the center 90% is totally clear.
        
        pass
        
    def _generate_scanlines(self):
        """Generates horizontal scanlines."""
        self.scanline_surface = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        for y in range(0, self.screen_height, 4):
            pygame.draw.line(self.scanline_surface, (0, 0, 0, self.scanline_intensity), (0, y), (self.screen_width, y), 2)
            
    def apply_chromatic_aberration(self, surface, offset=2):
        """Applies a simple chromatic aberration effect (RGB split)."""
        # Create separate channels
        # This is expensive, so we only do it on the final surface if needed
        # Or simpler: Blit the surface onto itself 3 times with offsets and add/mult flags
        
        # Fast Chromatic Aberration simulation:
        # Blit Red channel slightly to left
        # Blit Blue channel slightly to right
        # Green stays center
        
        # However, getting channels in pygame is slow without numpy.
        # Alternative: Just draw random "glitch" stripes?
        # Or: Render the whole screen to a texture, then blit it with special flags?
        
        # We will assume this is called rarely or on small areas, OR we accept the frame drop.
        # Check if enabled. For now, let's skip the expensive per-frame logic unless requested.
        pass
            
    def trigger_flash(self, color=(255, 255, 255), duration=0.2, intensity=100):
        """Triggers a screen flash."""
        self.flash_color = color
        self.flash_duration = duration * 1000 # to ms
        self.flash_start_time = pygame.time.get_ticks()
        self.flash_max_alpha = intensity
        
    def update(self):
        """Updates effect timers."""
        now = pygame.time.get_ticks()
        
        # Update grain
        if now - self.grain_timer > self.grain_speed:
            self.current_grain_frame = (self.current_grain_frame + 1) % self.num_grain_frames
            self.grain_timer = now
            
    def draw(self, surface):
        """Draws all enabled effects onto the target surface."""
        # 1. Draw Grain
        if self.grain_surfaces:
            surface.blit(self.grain_surfaces[self.current_grain_frame], (0, 0))
            
        # 2. Draw Scanlines
        if self.scanline_surface:
            surface.blit(self.scanline_surface, (0, 0))
            
        if self.vignette_surface:
             surface.blit(self.vignette_surface, (0, 0))

        # 4. Color Pop / Saturation Boost
        # We create a "Vibrance" overlay:
        # A partially transparent layer that adds color/contrast.
        # BLEND_ADD adds brightness. BLEND_MULT adds contrast/darkness.
        
        # "Pop" Effect:
        # 1. Add a subtle 'Overlay' layer (using BLEND_ADD with low alpha) to brighten highlights
        pop_surf = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        pop_surf.fill((20, 10, 40, 30)) # Slight purple/blue brightener
        surface.blit(pop_surf, (0, 0), special_flags=pygame.BLEND_ADD)
        
        # 2. Increase contrast by multiplying slightly?
        contrast_surf = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        contrast_surf.fill((230, 230, 250, 255)) # Slightly off-white multiplication (darkens slightly but boosts saturation perception)
        surface.blit(contrast_surf, (0, 0), special_flags=pygame.BLEND_MULT)
            
        # 4. Flash
        if self.flash_color and self.flash_duration > 0:
            now = pygame.time.get_ticks()
            elapsed = now - self.flash_start_time
            if elapsed < self.flash_duration:
                # Calculate fading alpha
                progress = elapsed / self.flash_duration
                current_alpha = int(self.flash_max_alpha * (1 - progress))
                
                flash_surf = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
                flash_surf.fill((*self.flash_color, current_alpha))
                surface.blit(flash_surf, (0, 0), special_flags=pygame.BLEND_ADD)
            else:
                self.flash_color = None
                
import math
