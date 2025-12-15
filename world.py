import random

import noise


# --- Generation Constants ---
class GenConst:
    """
    A container for all default constants related to procedural world generation.
    These are the base values that will be slightly randomized.
    """

    # --- Elevation thresholds (0.0 is deep sea, 1.0 is high mountain) ---
    WATER_LEVEL = 0.3  # Below this is water
    SAND_LEVEL = 0.35  # Below this is sand
    MOUNTAIN_LEVEL = 0.7  # Above this is mountainous granite terrain
    MOUNTAIN_PEAK_LEVEL = 0.8  # Above this is considered a mountain peak

    # --- Temperature thresholds (0.0 is freezing, 1.0 is scorching) ---
    HOT_CLIMATE_TEMP = 0.65  # Above this is considered a hot climate
    MOUNTAIN_ICE_TEMP_LIMIT = 0.15  # Peaks colder than this will be ice
    COASTAL_ICE_TEMP_LIMIT = 0.25  # Shores colder than this can freeze

    # --- Moisture and Feature thresholds (0.0 - 1.0) ---
    DESERT_MOISTURE_LIMIT = 0.35  # Hot climates drier than this are deserts
    ROUGH_TERRAIN_THRESHOLD = 0.5  # How much "roughness" is needed for granite patches
    VOLCANO_THRESHOLD = 0.97  # Likelihood of volcanoes. Higher is rarer.

    # --- Modifiers ---
    TEMP_ALTITUDE_FALLOFF = 0.5  # How much temperature drops with elevation

    # --- Noise Map Scaling ---
    # Higher values = more features, more "zoomed out". Lower values = larger, "zoomed in" features.
    ELEVATION_SCALE = 10.0
    TEMP_SCALE = 5.0
    MOISTURE_SCALE = 5.0
    ROUGHNESS_SCALE = 16.0
    VOLCANO_SCALE = 24.0


class World:
    """A class to hold all data related to the game world."""

    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.world_map = [[0 for _ in range(width)] for _ in range(height)]
        self.elevation_map = [[0 for _ in range(width)] for _ in range(height)]
        self.temperature_map = [[0 for _ in range(width)] for _ in range(height)]
        self.moisture_map = [[0 for _ in range(width)] for _ in range(height)]
        self.roughness_map = [[0 for _ in range(width)] for _ in range(height)]
        self.volcano_map = [[0 for _ in range(width)] for _ in range(height)]


class WorldGenerator:
    """Handles the procedural generation of the world."""

    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.world = World(width, height)
        self.consts = self._generate_randomized_consts()

    def _generate_randomized_consts(self):
        """Generates a randomized set of constants based on the base GenConst values."""
        consts = {}
        # List of attributes to not randomize (scaling factors might need to stay constant or have different logic)
        # But user asked for "elevation and different variables... generate slightly more randomly"
        
        # Get all attributes from GenConst that are uppercase (constants)
        attributes = [a for a in dir(GenConst) if not a.startswith('__') and a.isupper()]
        
        for attr in attributes:
            base_val = getattr(GenConst, attr)
            # Randomize by +/- 10-30%
            # Generate a random factor between 0.7 and 0.9 (negative variation) or 1.1 and 1.3 (positive variation)
            # Or simply +/- 10-30% range: 0.7 to 1.3 (excluding 0.9-1.1 maybe? No, "differ 10-30%" implies wide range)
            # Let's use a simpler approach: random factor between 0.8 and 1.2 (+/- 20%) 
            # The user asked for "differ 10-30% across the map as a whole"
            # It implies the *parameters* should vary.
            
            # Use 0.8 to 1.2 for most, maybe clamp probabilities 0-1
            factor = random.uniform(0.8, 1.2)
            
            new_val = base_val * factor
            
            # Special handling for probabilities (0-1 range)
            if attr.endswith('LEVEL') or attr.endswith('LIMIT') or attr.endswith('THRESHOLD') or attr.endswith('TEMP'):
                 new_val = max(0.0, min(1.0, new_val))
                 
            # Special handling for Volcano threshold (it's close to 1, so changing it by 20% might make it 1.2 or 0.8)
            # 0.97 -> 1.1 (no volcanoes) or 0.77 (too many volcanoes)
            # For thresholds close to 1, we might want to perturb the *gap* to 1.
            if attr == 'VOLCANO_THRESHOLD':
                # Base gap is 0.03. Randomize the gap by 10-30%
                gap = 1.0 - base_val
                new_gap = gap * random.uniform(0.7, 1.3)
                new_val = 1.0 - new_gap
                
            consts[attr] = new_val
            
        return consts

    def generate(self):
        """Generate the world map using a multi-pass model. Returns a World object."""
        self._generate_noise_maps()
        self._redistribute_elevation()
        self._create_adjusted_temperature()
        self._build_base_terrain()
        self._place_special_features()
        return self.world

    def _generate_noise_maps(self):
        seed = random.randint(0, 100)
        self.world.elevation_map = self._noise_map(self.consts['ELEVATION_SCALE'], seed)
        base_temp_map = self._noise_map(self.consts['TEMP_SCALE'], seed + 1)
        self.world.moisture_map = self._noise_map(self.consts['MOISTURE_SCALE'], seed + 2)
        self.world.roughness_map = self._noise_map(self.consts['ROUGHNESS_SCALE'], seed + 3)
        self.world.volcano_map = self._noise_map(self.consts['VOLCANO_SCALE'], seed + 4)
        self.base_temp_map = base_temp_map  # Store temporarily

    def _redistribute_elevation(self):
        for y in range(self.height):
            for x in range(self.width):
                e = self.world.elevation_map[y][x]
                self.world.elevation_map[y][x] = 3 * (e**2) - 2 * (e**3)

    def _create_adjusted_temperature(self):
        for y in range(self.height):
            for x in range(self.width):
                temp_falloff = (
                    self.world.elevation_map[y][x] * self.consts['TEMP_ALTITUDE_FALLOFF']
                )
                adjusted_temp = self.base_temp_map[y][x] - temp_falloff
                self.world.temperature_map[y][x] = max(0, min(adjusted_temp, 1))

    def _build_base_terrain(self):
        for y in range(self.height):
            for x in range(self.width):
                self.world.world_map[y][x] = self._get_base_tile_type(
                    self.world.elevation_map[y][x],
                    self.world.temperature_map[y][x],
                    self.world.moisture_map[y][x],
                    self.world.roughness_map[y][x],
                )

    def _place_special_features(self):
        self._place_lava_in_mountains()
        self._place_ice_near_water()

    def _place_lava_in_mountains(self):
        for y in range(self.height):
            for x in range(self.width):
                if self.world.world_map[y][x] == "granite":
                    if self.world.volcano_map[y][x] > self.consts['VOLCANO_THRESHOLD']:
                        self.world.world_map[y][x] = "lava"

    def _place_ice_near_water(self):
        new_map = [row[:] for row in self.world.world_map]
        for y in range(self.height):
            for x in range(self.width):
                if self.world.world_map[y][x] in ["grass", "sand"]:
                    temp = self.world.temperature_map[y][x]
                    if temp < self.consts['COASTAL_ICE_TEMP_LIMIT']:
                        if self._is_near_water(x, y):
                            new_map[y][x] = "ice"
        self.world.world_map = new_map

    def _is_near_water(self, x, y):
        for dy in range(-1, 2):
            for dx in range(-1, 2):
                if dy == 0 and dx == 0:
                    continue
                ny, nx = y + dy, x + dx
                if 0 <= ny < self.height and 0 <= nx < self.width:
                    if self.world.world_map[ny][nx] == "water":
                        return True
        return False

    def _noise_map(self, scale, seed, octaves=6, persistence=0.5, lacunarity=2.0):
        noise_map = [[0 for _ in range(self.width)] for _ in range(self.height)]
        for y in range(self.height):
            for x in range(self.width):
                nx = x / self.width * scale
                ny = y / self.height * scale
                noise_val = noise.pnoise2(
                    nx, ny, octaves, persistence, lacunarity, base=seed
                )
                noise_map[y][x] = (noise_val + 1) / 2
        return noise_map

    def _get_base_tile_type(self, elevation, temperature, moisture, roughness):
        if elevation < self.consts['WATER_LEVEL']:
            return "water"
        if elevation < self.consts['SAND_LEVEL']:
            return "sand"

        if elevation > self.consts['MOUNTAIN_PEAK_LEVEL']:
            if temperature < self.consts['MOUNTAIN_ICE_TEMP_LIMIT']:
                return "ice"
            return "granite"
        if elevation > self.consts['MOUNTAIN_LEVEL']:
            return "granite"

        if temperature > self.consts['HOT_CLIMATE_TEMP']:
            if moisture < self.consts['DESERT_MOISTURE_LIMIT']:
                return "sand"

        if roughness > self.consts['ROUGH_TERRAIN_THRESHOLD']:
            return "granite"

        return "grass"
