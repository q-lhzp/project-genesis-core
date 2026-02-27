"""
World Engine Plugin - Atmosphere, Weather & Lighting
Handles real-time world state synchronization (weather, daylight cycles)
"""

import json
import time
import logging
import math
import random
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='[WORLD] %(message)s')
logger = logging.getLogger("world")

# =============================================================================
# WEATHER SIMULATION & LIGHTING ENGINE
# =============================================================================

class WorldState:
    """Manages world state persistence via Kernel state_manager."""

    def __init__(self, state_manager):
        self.state_manager = state_manager
        self._load_or_initialize()

    def _load_or_initialize(self):
        """Load existing world state or initialize defaults."""
        state = self.state_manager.get_domain("world_state")
        if not state or not state.get("initialized"):
            # Initialize default world state
            self._state = {
                "initialized": True,
                "location": {
                    "city": "Berlin",
                    "latitude": 52.52,
                    "longitude": 13.405,
                    "timezone": "Europe/Berlin"
                },
                "weather": {
                    "temperature": 18.0,
                    "feels_like": 17.0,
                    "condition": "clear",
                    "humidity": 65,
                    "wind_speed": 12.0,
                    "pressure": 1013.25,
                    "visibility": 10000,
                    "uv_index": 3,
                    "last_updated": datetime.now().isoformat()
                },
                "lighting": {
                    "sunrise": "06:45",
                    "sunset": "18:30",
                    "daylight_minutes": 705,
                    "is_daytime": True,
                    "golden_hour_morning": True,
                    "golden_hour_evening": False,
                    "moon_phase": "waxing_gibbous",
                    "moon_illumination": 75
                },
                "atmosphere": {
                    "fog_density": 0.0,
                    "cloud_cover": 20,
                    "precipitation_chance": 10,
                    "air_quality_index": 35
                },
                "forecast": {
                    "today_high": 20,
                    "today_low": 12,
                    "tomorrow_high": 18,
                    "tomorrow_low": 10
                },
                "season": "winter",
                "world_time": datetime.now().isoformat()
            }
            self._save()
        else:
            self._state = state

    def _save(self):
        """Persist state to kernel."""
        self._save_to_manager()

    def _save_to_manager(self):
        """Save state through kernel state_manager."""
        self.state_manager.update_domain("world_state", self._state)

    def get(self) -> Dict[str, Any]:
        """Get current world state."""
        return self._state

    def update_weather(self, weather_data: Dict[str, Any]):
        """Update weather data."""
        self._state["weather"].update(weather_data)
        self._state["weather"]["last_updated"] = datetime.now().isoformat()
        self._save_to_manager()

    def update_lighting(self, lighting_data: Dict[str, Any]):
        """Update lighting data."""
        self._state["lighting"].update(lighting_data)
        self._save_to_manager()

    def update_atmosphere(self, atmosphere_data: Dict[str, Any]):
        """Update atmosphere data."""
        self._state["atmosphere"].update(atmosphere_data)
        self._save_to_manager()


class WeatherSimulator:
    """Simulates realistic weather patterns with optional OpenWeather integration."""

    # Weather conditions with transitions
    CONDITIONS = ["clear", "partly_cloudy", "cloudy", "overcast", "rain", "light_rain", "heavy_rain", "snow", "fog", "storm"]
    CONDITION_WEIGHTS = [0.25, 0.15, 0.15, 0.10, 0.10, 0.08, 0.05, 0.05, 0.04, 0.03]

    def __init__(self, state: WorldState, model_config: Dict[str, Any]):
        self.state = state
        self.model_config = model_config
        self.openweather_key = model_config.get("openweather_api_key")
        self.use_api = bool(self.openweather_key)

        # Season-based temperature ranges
        self.season_temps = {
            "winter": (-5, 8),
            "spring": (8, 18),
            "summer": (18, 30),
            "autumn": (8, 16)
        }

    def get_current_season(self) -> str:
        """Determine current season based on date."""
        month = datetime.now().month
        if month in [12, 1, 2]:
            return "winter"
        elif month in [3, 4, 5]:
            return "spring"
        elif month in [6, 7, 8]:
            return "summer"
        else:
            return "autumn"

    def simulate_weather(self) -> Dict[str, Any]:
        """Generate simulated weather data."""
        state = self.state.get()
        current_weather = state.get("weather", {})
        current_condition = current_weather.get("condition", "clear")

        # Get current temperature or use base
        current_temp = current_weather.get("temperature", 15.0)
        season = self.get_current_season()
        min_temp, max_temp = self.season_temps[season]

        # Temperature drift (small changes over time)
        temp_change = random.uniform(-0.5, 0.5)
        new_temp = max(min_temp - 5, min(max_temp + 5, current_temp + temp_change))

        # Condition transition (most likely to stay similar)
        condition = self._transition_condition(current_condition)

        # Calculate derived values
        humidity = self._calculate_humidity(condition, new_temp)
        wind_speed = self._calculate_wind_speed(condition)

        weather = {
            "temperature": round(new_temp, 1),
            "feels_like": round(new_temp - (2 if humidity > 70 else 0) + (wind_speed * 0.1), 1),
            "condition": condition,
            "humidity": humidity,
            "wind_speed": round(wind_speed, 1),
            "pressure": 1013.25 + random.uniform(-20, 20),
            "visibility": self._calculate_visibility(condition),
            "uv_index": self._calculate_uv_index(condition)
        }

        return weather

    def _transition_condition(self, current: str) -> str:
        """Transition to a similar or related weather condition."""
        # Add some persistence - high chance to stay same
        if random.random() < 0.7:
            return current

        # Find related conditions for smooth transitions
        transitions = {
            "clear": ["partly_cloudy", "cloudy"],
            "partly_cloudy": ["clear", "cloudy"],
            "cloudy": ["partly_cloudy", "overcast", "light_rain"],
            "overcast": ["cloudy", "rain", "fog"],
            "rain": ["light_rain", "heavy_rain", "cloudy"],
            "light_rain": ["rain", "cloudy"],
            "heavy_rain": ["rain", "storm"],
            "snow": ["cloudy", "clear"],
            "fog": ["cloudy", "overcast"],
            "storm": ["heavy_rain", "rain"]
        }

        options = transitions.get(current, self.CONDITIONS)
        return random.choice(options)

    def _calculate_humidity(self, condition: str, temp: float) -> int:
        """Calculate humidity based on condition and temperature."""
        base_humidity = {
            "clear": 50,
            "partly_cloudy": 60,
            "cloudy": 75,
            "overcast": 85,
            "rain": 90,
            "light_rain": 88,
            "heavy_rain": 95,
            "snow": 80,
            "fog": 98,
            "storm": 92
        }

        base = base_humidity.get(condition, 70)
        # Higher humidity in warmer weather
        temp_factor = (temp + 10) / 40  # Normalize
        return min(100, int(base * (0.8 + temp_factor * 0.4) + random.uniform(-5, 5)))

    def _calculate_wind_speed(self, condition: str) -> float:
        """Calculate wind speed based on condition."""
        base_wind = {
            "clear": 8,
            "partly_cloudy": 12,
            "cloudy": 18,
            "overcast": 15,
            "rain": 25,
            "light_rain": 20,
            "heavy_rain": 35,
            "snow": 15,
            "fog": 5,
            "storm": 50
        }
        return base_wind.get(condition, 10) + random.uniform(-5, 5)

    def _calculate_visibility(self, condition: str) -> int:
        """Calculate visibility in meters."""
        visibility = {
            "clear": 10000,
            "partly_cloudy": 10000,
            "cloudy": 8000,
            "overcast": 6000,
            "rain": 4000,
            "light_rain": 6000,
            "heavy_rain": 2000,
            "snow": 1500,
            "fog": 500,
            "storm": 1000
        }
        return visibility.get(condition, 10000)

    def _calculate_uv_index(self, condition: str) -> int:
        """Calculate UV index based on cloud cover."""
        base_uv = {
            "clear": 8,
            "partly_cloudy": 5,
            "cloudy": 3,
            "overcast": 1,
            "rain": 0,
            "light_rain": 1,
            "heavy_rain": 0,
            "snow": 3,  # Snow reflects UV
            "fog": 0,
            "storm": 0
        }
        return base_uv.get(condition, 3)

    async def fetch_live_weather(self, lat: float, lon: float) -> Optional[Dict[str, Any]]:
        """Fetch weather from OpenWeather API if configured."""
        if not self.use_api:
            return None

        try:
            import urllib.request
            import urllib.parse

            url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={self.openweather_key}&units=metric"

            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read())

            return {
                "temperature": data["main"]["temp"],
                "feels_like": data["main"]["feels_like"],
                "condition": data["weather"][0]["main"].lower().replace(" ", "_"),
                "humidity": data["main"]["humidity"],
                "wind_speed": data["wind"]["speed"] * 3.6,  # m/s to km/h
                "pressure": data["main"]["pressure"],
                "visibility": data.get("visibility", 10000),
                "uv_index": 3  # OpenWeather free tier doesn't include UV
            }
        except Exception as e:
            logger.warning(f"OpenWeather API error: {e}, falling back to simulation")
            return None


class LightingEngine:
    """Calculates sunrise, sunset, and daylight information."""

    def __init__(self, state: WorldState):
        self.state = state

    def calculate_lighting(self) -> Dict[str, Any]:
        """Calculate lighting data based on location and time."""
        state = self.state.get()
        location = state.get("location", {})
        lat = location.get("latitude", 52.52)

        now = datetime.now()

        # Calculate day of year
        day_of_year = now.timetuple().tm_yday

        # Solar declination angle
        declination = 23.45 * math.sin(math.radians(360/365 * (day_of_year - 81)))

        # Hour angle at sunrise/sunset
        lat_rad = math.radians(lat)
        decl_rad = math.radians(declination)

        cos_hour_angle = -math.tan(lat_rad) * math.tan(decl_rad)

        # Clamp to handle polar day/night
        cos_hour_angle = max(-1, min(1, cos_hour_angle))

        hour_angle = math.degrees(math.acos(cos_hour_angle))

        # Sunrise/sunset in hours (UTC)
        sunrise_hour = 12 - hour_angle / 15
        sunset_hour = 12 + hour_angle / 15

        # Adjust for timezone (simple offset)
        tz_offset = now.astimezone().utcoffset().total_seconds() / 3600 if now.astimezone().utcoffset() else 1
        sunrise_hour += tz_offset
        sunset_hour += tz_offset

        sunrise = now.replace(hour=int(sunrise_hour), minute=int((sunrise_hour % 1) * 60), second=0)
        sunset = now.replace(hour=int(sunset_hour), minute=int((sunset_hour % 1) * 60), second=0)

        # Daylight minutes
        daylight_minutes = int((sunset - sunrise).total_seconds() / 60)

        # Current daytime status
        current_hour = now.hour + now.minute / 60
        sunrise_h = sunrise_hour
        sunset_h = sunset_hour
        is_daytime = sunrise_h <= current_hour <= sunset_h

        # Golden hour (1 hour after sunrise, 1 hour before sunset)
        golden_hour_morning = sunrise_h <= current_hour <= sunrise_h + 1
        golden_hour_evening = sunset_h - 1 <= current_hour <= sunset_h

        # Simplified moon phase calculation
        moon_phase, moon_illumination = self._calculate_moon(now)

        lighting = {
            "sunrise": sunrise.strftime("%H:%M"),
            "sunset": sunset.strftime("%H:%M"),
            "daylight_minutes": daylight_minutes,
            "is_daytime": is_daytime,
            "golden_hour_morning": golden_hour_morning,
            "golden_hour_evening": golden_hour_evening,
            "moon_phase": moon_phase,
            "moon_illumination": moon_illumination
        }

        return lighting

    def _calculate_moon(self, date: datetime) -> tuple:
        """Calculate approximate moon phase."""
        # Simplified moon phase (29.53 day cycle)
        known_new_moon = datetime(2000, 1, 6, 18, 14)  # Known new moon
        days_since = (date - known_new_moon).total_seconds() / 86400
        lunations = days_since / 29.53
        phase = lunations % 1

        phases = [
            ("new_moon", 0),
            ("waxing_crescent", 12),
            ("first_quarter", 25),
            ("waxing_gibbous", 37),
            ("full_moon", 50),
            ("waning_gibbous", 62),
            ("last_quarter", 75),
            ("waning_crescent", 87)
        ]

        phase_percent = int(phase * 100)

        for name, threshold in phases:
            if phase_percent < threshold:
                illumination = int(50 * (1 + math.cos(phase * 2 * math.pi)))
                return name, illumination

        return "new_moon", 0


class AtmosphereEngine:
    """Calculates atmospheric conditions based on weather."""

    def __init__(self, state: WorldState):
        self.state = state

    def calculate_atmosphere(self) -> Dict[str, Any]:
        """Calculate atmospheric conditions."""
        weather = self.state.get().get("weather", {})
        condition = weather.get("condition", "clear")

        # Fog density based on conditions
        fog_density = 0.0
        if condition == "fog":
            fog_density = random.uniform(0.7, 1.0)
        elif condition == "overcast":
            fog_density = random.uniform(0.1, 0.3)

        # Cloud cover percentage
        cloud_cover = {
            "clear": random.randint(0, 20),
            "partly_cloudy": random.randint(20, 50),
            "cloudy": random.randint(50, 80),
            "overcast": random.randint(80, 100),
            "rain": random.randint(70, 100),
            "light_rain": random.randint(60, 90),
            "heavy_rain": random.randint(80, 100),
            "snow": random.randint(70, 100),
            "fog": 100,
            "storm": 100
        }.get(condition, 30)

        # Precipitation chance
        precip_chance = {
            "clear": random.randint(0, 10),
            "partly_cloudy": random.randint(5, 20),
            "cloudy": random.randint(20, 40),
            "overcast": random.randint(40, 60),
            "rain": random.randint(70, 90),
            "light_rain": random.randint(50, 70),
            "heavy_rain": random.randint(80, 100),
            "snow": random.randint(40, 70),
            "fog": random.randint(20, 40),
            "storm": random.randint(80, 100)
        }.get(condition, 10)

        # Air quality (simplified - good when clear)
        aqi = 25 if condition == "clear" else 50 if condition in ["partly_cloudy", "cloudy"] else 75
        aqi = min(100, aqi + random.randint(-10, 10))

        return {
            "fog_density": round(fog_density, 2),
            "cloud_cover": cloud_cover,
            "precipitation_chance": precip_chance,
            "air_quality_index": aqi
        }


# =============================================================================
# WORLD PLUGIN
# =============================================================================

class WorldPlugin:
    """World Engine Plugin - manages atmosphere, weather, and lighting."""

    def __init__(self):
        self.kernel = None
        self.world_state = None
        self.weather_sim = None
        self.lighting_engine = None
        self.atmosphere_engine = None
        self.model_config = {}

    def initialize(self, kernel):
        """Initialize the World Plugin with kernel reference."""
        self.kernel = kernel
        self.model_config = getattr(kernel, 'model_config', {})

        # Initialize state manager
        self.world_state = WorldState(kernel.state_manager)

        # Initialize engines
        self.weather_sim = WeatherSimulator(self.world_state, self.model_config)
        self.lighting_engine = LightingEngine(self.world_state)
        self.atmosphere_engine = AtmosphereEngine(self.world_state)

        # Initial update
        self._update_all()

        logger.info("WorldPlugin initialized successfully")

    def on_event(self, event):
        """Handle incoming events - primarily TICK_HOURLY for world updates."""
        event_type = event.get("event")

        if event_type == "TICK_HOURLY":
            logger.info("Hourly tick: Updating world conditions")
            self._update_all()

        elif event_type == "TICK_MINUTELY":
            # Optional: more frequent lighting updates
            lighting = self.lighting_engine.calculate_lighting()
            self.world_state.update_lighting(lighting)

    def _update_all(self):
        """Update all world systems."""
        state = self.world_state.get()
        location = state.get("location", {})
        lat = location.get("latitude", 52.52)
        lon = location.get("longitude", 13.405)

        # Try live weather first, fallback to simulation
        import asyncio

        # Check if we should use live weather
        live_weather = None
        if self.weather_sim.use_api:
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # We're in async context, use ensure_future
                    future = asyncio.run_coroutine_threadsafe(
                        self.weather_sim.fetch_live_weather(lat, lon),
                        loop
                    )
                    live_weather = future.result(timeout=3)
                else:
                    live_weather = asyncio.run(self.weather_sim.fetch_live_weather(lat, lon))
            except Exception as e:
                logger.warning(f"Live weather fetch failed: {e}")

        # Use live weather or simulation
        if live_weather:
            weather = live_weather
            logger.info("Using live weather data")
        else:
            weather = self.weather_sim.simulate_weather()
            logger.info(f"Using simulated weather: {weather['condition']}, {weather['temperature']}°C")

        # Calculate lighting and atmosphere
        lighting = self.lighting_engine.calculate_lighting()
        atmosphere = self.atmosphere_engine.calculate_atmosphere()

        # Update state
        self.world_state.update_weather(weather)
        self.world_state.update_lighting(lighting)
        self.world_state.update_atmosphere(atmosphere)

        # Update season
        self.world_state._state["season"] = self.weather_sim.get_current_season()
        self.world_state._state["world_time"] = datetime.now().isoformat()
        self.world_state._save_to_manager()

        # Publish weather update event
        if self.kernel and self.kernel.event_bus:
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.run_coroutine_threadsafe(
                        self.kernel.event_bus.publish(
                            "EVENT_WEATHER_UPDATE",
                            "plugin.world",
                            weather
                        ),
                        loop
                    )
            except Exception as e:
                logger.debug(f"Could not publish weather event: {e}")

    def handle_get_state(self) -> Dict[str, Any]:
        """API handler: Get current world state."""
        return {
            "success": True,
            "world": self.world_state.get()
        }

    def handle_get_weather(self) -> Dict[str, Any]:
        """API handler: Get current weather."""
        return {
            "success": True,
            "weather": self.world_state.get().get("weather", {})
        }

    def handle_get_lighting(self) -> Dict[str, Any]:
        """API handler: Get current lighting."""
        return {
            "success": True,
            "lighting": self.world_state.get().get("lighting", {})
        }

    def handle_set_location(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """API handler: Set location."""
        city = data.get("city")
        latitude = data.get("latitude")
        longitude = data.get("longitude")

        if not city or latitude is None or longitude is None:
            return {"success": False, "error": "Missing required fields: city, latitude, longitude"}

        self.world_state._state["location"] = {
            "city": city,
            "latitude": latitude,
            "longitude": longitude,
            "timezone": data.get("timezone", "UTC")
        }
        self.world_state._save_to_manager()

        # Trigger immediate update
        self._update_all()

        return {"success": True, "location": self.world_state._state["location"]}


# =============================================================================
# PLUGIN EXPORTS
# =============================================================================

# Global instance for plugin loader
plugin = WorldPlugin()


def initialize(kernel):
    """Plugin initialization entry point."""
    plugin.initialize(kernel)


def on_event(event):
    """Event handler for plugin."""
    plugin.on_event(event)


def handle_get_state():
    """API handler: Get world state."""
    return plugin.handle_get_state()


def handle_get_weather():
    """API handler: Get weather."""
    return plugin.handle_get_weather()


def handle_get_lighting():
    """API handler: Get lighting."""
    return plugin.handle_get_lighting()


def handle_set_location(data):
    """API handler: Set location."""
    return plugin.handle_set_location(data)
