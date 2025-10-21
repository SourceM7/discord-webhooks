"""
Enhanced Moon Phase Discord Bot
A professional-grade Discord bot for posting detailed lunar information with astronomy data,
photography guidance, and rich visual embeds.
"""

import ephem
import requests
import json
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional, Dict, Any, Tuple, List
from dataclasses import dataclass, asdict
from enum import Enum
import time
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('moon_bot.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class MoonPhase(Enum):
    """Enumeration of moon phases"""
    NEW_MOON = "New Moon"
    WAXING_CRESCENT = "Waxing Crescent"
    FIRST_QUARTER = "First Quarter"
    WAXING_GIBBOUS = "Waxing Gibbous"
    FULL_MOON = "Full Moon"
    WANING_GIBBOUS = "Waning Gibbous"
    LAST_QUARTER = "Last Quarter"
    WANING_CRESCENT = "Waning Crescent"


@dataclass
class MoonData:
    """Comprehensive moon phase and astronomical data"""
    phase_name: str
    phase_enum: MoonPhase
    illumination: float
    distance_km: int
    angular_diameter: float
    next_full_moon: str
    next_new_moon: str
    age_days: float
    altitude: float
    azimuth: float
    rise_time: Optional[str]
    set_time: Optional[str]
    transit_time: Optional[str]
    is_visible: bool
    constellation: str
    right_ascension: str
    declination: str
    libration_lat: float
    libration_lon: float
    phase_angle: float
    distance_variation: float  # % from mean distance
    image_file: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        data['phase_enum'] = self.phase_enum.value
        return data


class MoonFactCategory(Enum):
    """Categories for moon facts"""
    PHYSICAL = "Physical Properties"
    ORBITAL = "Orbital Mechanics"
    HISTORICAL = "Historical Facts"
    FORMATION = "Formation & Geology"
    OBSERVATION = "Observation & Phenomena"


class Configuration:
    """Bot configuration manager"""
    
    def __init__(self, config_path: Path = Path('config.json')):
        self.config_path = config_path
        self.message_id_path = Path('message_id.txt')
        self.image_cache_path = Path('image_cache.json')
        self.config = self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file or create default"""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Could not load config: {e}. Using defaults.")
        
        return {
            'observer_latitude': 51.99,  # Naaldwijk, NL
            'observer_longitude': 4.21,
            'observer_elevation': 0,
            'timezone_offset': 1,  # CET
            'update_interval_hours': 6,
            'retry_attempts': 3,
            'retry_delay_seconds': 5
        }
    
    def get_message_id(self) -> Optional[str]:
        """Retrieve stored Discord message ID"""
        try:
            if self.message_id_path.exists():
                return self.message_id_path.read_text().strip()
        except Exception as e:
            logger.error(f"Error reading message ID: {e}")
        return None
    
    def save_message_id(self, message_id: str) -> None:
        """Save Discord message ID"""
        try:
            self.message_id_path.write_text(message_id)
            logger.info(f"Saved message ID: {message_id}")
        except Exception as e:
            logger.error(f"Error saving message ID: {e}")


class AstronomicalCalculator:
    """Handles all astronomical calculations"""
    
    def __init__(self, config: Configuration):
        self.config = config
        self.observer = self._create_observer()
        
    def _create_observer(self) -> ephem.Observer:
        """Create configured observer"""
        observer = ephem.Observer()
        observer.lat = str(self.config.config['observer_latitude'])
        observer.lon = str(self.config.config['observer_longitude'])
        observer.elevation = self.config.config['observer_elevation']
        observer.date = datetime.now(timezone.utc)
        return observer
    
    def calculate_moon_data(self) -> MoonData:
        """Calculate comprehensive moon data"""
        moon = ephem.Moon()
        self.observer.date = datetime.now(timezone.utc)
        moon.compute(self.observer)
        
        # Basic phase calculations
        phase_name, phase_enum, image_file = self._determine_phase(moon)
        
        # Distance calculations
        distance_km = int(moon.earth_distance * 149597870.7)
        mean_distance = 384400  # km
        distance_variation = ((distance_km - mean_distance) / mean_distance) * 100
        
        # Angular diameter in arcminutes
        angular_diameter = moon.size / 60.0
        
        # Lunar age (days since new moon)
        prev_new = ephem.previous_new_moon(self.observer.date)
        age_days = self.observer.date - prev_new
        
        # Position data
        altitude_deg = float(moon.alt) * 180.0 / ephem.pi
        azimuth_deg = float(moon.az) * 180.0 / ephem.pi
        
        # Rise/set times
        rise_time, set_time, transit_time = self._calculate_rise_set_times(moon)
        
        # Visibility
        is_visible = altitude_deg > 0
        
        # Constellation
        constellation = ephem.constellation(moon)[1]
        
        # Coordinates
        ra_hours = float(moon.ra) * 12.0 / ephem.pi
        ra_str = self._format_ra(ra_hours)
        dec_deg = float(moon.dec) * 180.0 / ephem.pi
        dec_str = self._format_dec(dec_deg)
        
        # Libration (apparent wobble)
        libration_lat = float(moon.libration_lat) * 180.0 / ephem.pi
        libration_lon = float(moon.libration_lon) * 180.0 / ephem.pi
        
        # Phase angle
        phase_angle = float(moon.phase_angle) * 180.0 / ephem.pi
        
        # Next events
        next_full = ephem.next_full_moon(self.observer.date)
        next_new = ephem.next_new_moon(self.observer.date)
        
        return MoonData(
            phase_name=phase_name,
            phase_enum=phase_enum,
            illumination=round(moon.phase, 1),
            distance_km=distance_km,
            angular_diameter=round(angular_diameter, 2),
            next_full_moon=ephem.Date(next_full).datetime().strftime('%B %d, %Y at %H:%M UTC'),
            next_new_moon=ephem.Date(next_new).datetime().strftime('%B %d, %Y at %H:%M UTC'),
            age_days=round(float(age_days), 1),
            altitude=round(altitude_deg, 1),
            azimuth=round(azimuth_deg, 1),
            rise_time=rise_time,
            set_time=set_time,
            transit_time=transit_time,
            is_visible=is_visible,
            constellation=constellation,
            right_ascension=ra_str,
            declination=dec_str,
            libration_lat=round(libration_lat, 2),
            libration_lon=round(libration_lon, 2),
            phase_angle=round(phase_angle, 1),
            distance_variation=round(distance_variation, 2),
            image_file=image_file
        )
    
    def _determine_phase(self, moon: ephem.Moon) -> Tuple[str, MoonPhase, str]:
        """Determine moon phase name and corresponding image"""
        prev_new = ephem.previous_new_moon(self.observer.date)
        days_since_new = self.observer.date - prev_new
        
        phase_mapping = [
            (1, MoonPhase.NEW_MOON, "Moon_Phase_5_Alt.png"),
            (6, MoonPhase.WAXING_CRESCENT, "Moon_Phase_6_Alt.png"),
            (9, MoonPhase.FIRST_QUARTER, "Moon_Phase_7_Alt.png"),
            (13, MoonPhase.WAXING_GIBBOUS, "Moon_Phase_8_Alt.png"),
            (16, MoonPhase.FULL_MOON, "Moon_Phase_1_Alt.png"),
            (20, MoonPhase.WANING_GIBBOUS, "Moon_Phase_2_Alt.png"),
            (23, MoonPhase.LAST_QUARTER, "Moon_Phase_3_Alt.png"),
            (30, MoonPhase.WANING_CRESCENT, "Moon_Phase_4_Alt.png"),
        ]
        
        for days, phase_enum, image in phase_mapping:
            if days_since_new < days:
                return phase_enum.value, phase_enum, image
        
        return MoonPhase.WANING_CRESCENT.value, MoonPhase.WANING_CRESCENT, "Moon_Phase_4_Alt.png"
    
    def _calculate_rise_set_times(self, moon: ephem.Moon) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """Calculate moonrise, moonset, and transit times"""
        try:
            rise = self.observer.next_rising(moon)
            rise_time = ephem.Date(rise).datetime().strftime('%H:%M')
        except (ephem.AlwaysUpError, ephem.NeverUpError):
            rise_time = None
        
        try:
            set_time_date = self.observer.next_setting(moon)
            set_time = ephem.Date(set_time_date).datetime().strftime('%H:%M')
        except (ephem.AlwaysUpError, ephem.NeverUpError):
            set_time = None
        
        try:
            transit = self.observer.next_transit(moon)
            transit_time = ephem.Date(transit).datetime().strftime('%H:%M')
        except:
            transit_time = None
        
        return rise_time, set_time, transit_time
    
    @staticmethod
    def _format_ra(ra_hours: float) -> str:
        """Format right ascension as HH:MM:SS"""
        hours = int(ra_hours)
        minutes = int((ra_hours - hours) * 60)
        seconds = int(((ra_hours - hours) * 60 - minutes) * 60)
        return f"{hours:02d}h {minutes:02d}m {seconds:02d}s"
    
    @staticmethod
    def _format_dec(dec_deg: float) -> str:
        """Format declination as DD:MM:SS"""
        sign = '+' if dec_deg >= 0 else '-'
        dec_deg = abs(dec_deg)
        degrees = int(dec_deg)
        minutes = int((dec_deg - degrees) * 60)
        seconds = int(((dec_deg - degrees) * 60 - minutes) * 60)
        return f"{sign}{degrees:02d}° {minutes:02d}' {seconds:02d}\""


class ContentGenerator:
    """Generates facts, tips, and descriptions"""
    
    MOON_FACTS = {
        MoonFactCategory.PHYSICAL: [
            "has a mass of 7.342 × 10²² kg, about 1.2% of Earth's mass",
            "has a surface area of 38 million km², roughly the size of Asia and Africa combined",
            "experiences surface temperatures ranging from -173°C in shadows to 127°C in sunlight",
            "has gravity only 16.6% of Earth's, allowing Apollo astronauts to jump higher",
            "contains mountains reaching heights of 10,786 meters (higher than Everest relative to surroundings)",
            "has no atmosphere, so footprints left by Apollo astronauts remain undisturbed",
            "has a very thin exosphere containing helium, neon, and argon from solar wind",
        ],
        MoonFactCategory.ORBITAL: [
            "drifts 3.78cm away from Earth each year due to tidal forces",
            "is tidally locked, always showing the same face to Earth",
            "takes 27.3 days to orbit Earth (sidereal month)",
            "takes 29.5 days between full moons (synodic month)",
            "has an elliptical orbit varying from 356,500 km to 406,700 km from Earth",
            "orbits Earth at an average speed of 3,683 km/h",
            "has an orbit inclined 5.14° to Earth's ecliptic plane",
        ],
        MoonFactCategory.HISTORICAL: [
            "was first reached by humans on July 20, 1969 during Apollo 11",
            "has been visited by 12 astronauts across 6 Apollo missions",
            "received 842 pounds of samples returned to Earth by Apollo missions",
            "was last visited by humans in December 1972 during Apollo 17",
            "has been impacted by spacecraft from USA, USSR, ESA, India, China, Japan, and Israel",
        ],
        MoonFactCategory.FORMATION: [
            "formed about 4.5 billion years ago from debris after a Mars-sized object hit Earth",
            "contains ancient impact basins, some 3.9 billion years old",
            "has maria (dark plains) formed by ancient volcanic eruptions",
            "experiences 'moonquakes' that can last up to an hour",
            "has a crust 60-70 km thick on the near side, 150 km thick on the far side",
            "contains water ice in permanently shadowed craters at its poles",
        ],
        MoonFactCategory.OBSERVATION: [
            "appears the same size as the Sun from Earth (0.5°) - a cosmic coincidence enabling total eclipses",
            "causes Earth's tides through gravitational pull, creating two tidal bulges",
            "is gradually slowing Earth's rotation, lengthening our days by 2ms per century",
            "exhibits libration, allowing us to see 59% of its surface over time despite tidal locking",
            "creates lunar eclipses when Earth passes between the Sun and Moon",
            "appears larger near the horizon due to the 'Moon illusion' optical effect",
            "reflects only 12% of sunlight hitting it (albedo of 0.12)",
        ]
    }
    
    PHOTOGRAPHY_TIPS = {
        MoonPhase.NEW_MOON: {
            'settings': "ISO 3200-6400, f/1.4-f/2.8, 15-30s exposure",
            'technique': "Perfect for deep sky astrophotography. Use manual focus at infinity. Stack 10-20 frames to reduce noise. Consider light pollution filters.",
            'composition': "Capture Milky Way, constellations, or meteor showers without moon interference."
        },
        MoonPhase.WAXING_CRESCENT: {
            'settings': "ISO 400-800, f/5.6-f/8, 1/60-1/125s",
            'technique': "Bracket exposures ±2 EV to capture both lit portion and earthshine (sunlight reflected from Earth). Best 30-60 min after sunset.",
            'composition': "Include foreground silhouettes for scale. Golden hour colors enhance the scene."
        },
        MoonPhase.FIRST_QUARTER: {
            'settings': "ISO 100-200, f/8-f/11, 1/125-1/250s",
            'technique': "Optimal terminator contrast reveals surface detail. Use 300mm+ focal length. Best atmospheric seeing 2 hours after moonrise.",
            'composition': "Maximize crater shadows along terminator. Consider HDR for dynamic range."
        },
        MoonPhase.WAXING_GIBBOUS: {
            'settings': "ISO 200-400, f/8-f/11, 1/250-1/500s",
            'technique': "HDR bracketing recommended (5 exposures, ±2 EV) for mare and highland detail. Use mirror lock-up to minimize vibration.",
            'composition': "Terminator provides depth. Excellent for high-resolution mosaics."
        },
        MoonPhase.FULL_MOON: {
            'settings': "ISO 100, f/11-f/16, 1/250-1/500s",
            'technique': "Use spot metering or lunar mode. 400mm+ recommended for maximum detail. Avoid overexposure - histogram should peak left of center.",
            'composition': "Less dramatic shadows but great for color variations. Shoot in RAW for maximum flexibility."
        },
        MoonPhase.WANING_GIBBOUS: {
            'settings': "ISO 100-200, f/8-f/11, 1/125-1/250s",
            'technique': "Morning shoot requires faster shutter (atmospheric turbulence increases). Wait 2-3 hours after moonrise for best seeing conditions.",
            'composition': "Western terminator visible. Good for tracking same features as waxing phase."
        },
        MoonPhase.LAST_QUARTER: {
            'settings': "ISO 100-200, f/8-f/11, 1/125-1/250s",
            'technique': "Best atmospheric seeing pre-dawn. Use dewshield to prevent condensation. Eastern terminator provides excellent crater detail.",
            'composition': "Complement to First Quarter shots. Captures opposite lighting of same features."
        },
        MoonPhase.WANING_CRESCENT: {
            'settings': "ISO 400-800, f/5.6-f/8, 1/60-1/125s",
            'technique': "Pre-dawn shoot. Graduated ND filter balances sky if including foreground. Challenge: capture earthshine on dark side.",
            'composition': "Include eastern horizon with pre-sunrise colors for dramatic effect."
        }
    }
    
    @classmethod
    def get_random_fact(cls, phase_enum: MoonPhase) -> Tuple[str, str]:
        """Get a random moon fact with category"""
        import random
        category = random.choice(list(cls.MOON_FACTS.keys()))
        fact = random.choice(cls.MOON_FACTS[category])
        return fact, category.value
    
    @classmethod
    def get_photography_guide(cls, phase_enum: MoonPhase) -> Dict[str, str]:
        """Get comprehensive photography guide for current phase"""
        return cls.PHOTOGRAPHY_TIPS.get(phase_enum, {
            'settings': "ISO 100-200, f/8-f/11, 1/125-1/250s",
            'technique': "Use sturdy tripod and remote shutter release for sharp results.",
            'composition': "Experiment with different focal lengths and compositions."
        })
    
    @staticmethod
    def get_phase_color(phase_enum: MoonPhase) -> int:
        """Return Discord embed color based on moon phase"""
        colors = {
            MoonPhase.NEW_MOON: 0x0a0e27,
            MoonPhase.WAXING_CRESCENT: 0x2d3748,
            MoonPhase.FIRST_QUARTER: 0x4a5568,
            MoonPhase.WAXING_GIBBOUS: 0x718096,
            MoonPhase.FULL_MOON: 0xf7fafc,
            MoonPhase.WANING_GIBBOUS: 0x718096,
            MoonPhase.LAST_QUARTER: 0x4a5568,
            MoonPhase.WANING_CRESCENT: 0x2d3748
        }
        return colors.get(phase_enum, 0x2C2F33)
    
    @staticmethod
    def get_visibility_status(moon_data: MoonData) -> str:
        """Generate human-readable visibility status"""
        if not moon_data.is_visible:
            if moon_data.rise_time:
                return f"Below horizon • Rises at {moon_data.rise_time} UTC"
            return "Below horizon"
        
        status = f"Visible • Alt: {moon_data.altitude}° • Az: {moon_data.azimuth}°"
        if moon_data.transit_time:
            status += f" • Culminates at {moon_data.transit_time} UTC"
        return status


class DiscordWebhookManager:
    """Manages Discord webhook operations"""
    
    def __init__(self, webhook_url: str, config: Configuration):
        self.webhook_url = webhook_url
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'MoonPhaseBot/2.0 (Astronomical Information Bot)'
        })
    
    def delete_message(self, message_id: str) -> bool:
        """Delete a previous Discord message"""
        try:
            parts = self.webhook_url.rstrip('/').split('/')
            webhook_id = parts[-2]
            webhook_token = parts[-1]
            
            delete_url = f"https://discord.com/api/webhooks/{webhook_id}/{webhook_token}/messages/{message_id}"
            
            response = self.session.delete(delete_url, timeout=10)
            
            if response.status_code == 204:
                logger.info("Successfully deleted old message")
                return True
            else:
                logger.warning(f"Could not delete old message: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error deleting message: {e}")
            return False
    
    def post_message(self, moon_data: MoonData) -> Optional[str]:
        """Post new moon phase message to Discord"""
        try:
            # Load image
            image_path = Path(moon_data.image_file)
            if not image_path.exists():
                logger.error(f"Image file not found: {moon_data.image_file}")
                return None
            
            with open(image_path, 'rb') as f:
                image_data = f.read()
            
            # Generate content
            fact, fact_category = ContentGenerator.get_random_fact(moon_data.phase_enum)
            photo_guide = ContentGenerator.get_photography_guide(moon_data.phase_enum)
            phase_color = ContentGenerator.get_phase_color(moon_data.phase_enum)
            visibility = ContentGenerator.get_visibility_status(moon_data)
            
            # Build embed
            embed = self._build_embed(moon_data, fact, fact_category, photo_guide, phase_color, visibility)
            
            # Prepare request
            files = {
                'file': (moon_data.image_file, image_data, 'image/png')
            }
            
            payload = {
                'embeds': [embed]
            }
            
            # Post with retry logic
            for attempt in range(self.config.config['retry_attempts']):
                try:
                    response = self.session.post(
                        self.webhook_url,
                        data={'payload_json': json.dumps(payload)},
                        files=files,
                        params={'wait': 'true'},
                        timeout=30
                    )
                    
                    if response.status_code in [200, 204]:
                        logger.info("Successfully posted message to Discord")
                        response_data = response.json()
                        return response_data.get('id')
                    else:
                        logger.error(f"Discord API error: {response.status_code} - {response.text}")
                        
                except requests.exceptions.RequestException as e:
                    logger.error(f"Request failed (attempt {attempt + 1}): {e}")
                    
                if attempt < self.config.config['retry_attempts'] - 1:
                    time.sleep(self.config.config['retry_delay_seconds'])
            
            return None
            
        except Exception as e:
            logger.error(f"Error posting message: {e}", exc_info=True)
            return None
    
    def _build_embed(self, moon_data: MoonData, fact: str, fact_category: str, 
                     photo_guide: Dict[str, str], color: int, visibility: str) -> Dict[str, Any]:
        """Build Discord embed structure"""
        
        # Distance context
        distance_context = "🔴 Far" if moon_data.distance_variation > 0 else "🔵 Near"
        if abs(moon_data.distance_variation) > 3:
            distance_context += f" ({abs(moon_data.distance_variation):.1f}% from average)"
        
        fields = [
            {
                "name": "💫 Current Phase",
                "value": f"**{moon_data.phase_name}**\n{moon_data.illumination}% illuminated\n{moon_data.age_days} days old",
                "inline": True
            },
            {
                "name": "📏 Distance & Size",
                "value": f"**{moon_data.distance_km:,} km** {distance_context}\nAngular size: {moon_data.angular_diameter}'",
                "inline": True
            },
            {
                "name": "🌍 Visibility",
                "value": visibility,
                "inline": True
            },
            {
                "name": "📅 Next Events",
                "value": f"🌕 Full: {moon_data.next_full_moon}\n🌑 New: {moon_data.next_new_moon}",
                "inline": False
            },
            {
                "name": f"🔭 Observation Data",
                "value": (
                    f"**Constellation:** {moon_data.constellation}\n"
                    f"**Position:** RA {moon_data.right_ascension} • Dec {moon_data.declination}\n"
                    f"**Libration:** Lat {moon_data.libration_lat}° • Lon {moon_data.libration_lon}°\n"
                    f"**Phase Angle:** {moon_data.phase_angle}°"
                ),
                "inline": False
            },
            {
                "name": f"💡 Moon Fact • {fact_category}",
                "value": f"The Moon {fact}",
                "inline": False
            },
            {
                "name": "📸 Photography Guide",
                "value": (
                    f"**Settings:** {photo_guide['settings']}\n"
                    f"**Technique:** {photo_guide['technique']}\n"
                    f"**Composition:** {photo_guide['composition']}"
                ),
                "inline": False
            }
        ]
        
        # Add rise/set times if available
        if moon_data.rise_time or moon_data.set_time:
            timing = []
            if moon_data.rise_time:
                timing.append(f"🌄 Rise: {moon_data.rise_time} UTC")
            if moon_data.set_time:
                timing.append(f"🌅 Set: {moon_data.set_time} UTC")
            if moon_data.transit_time:
                timing.append(f"⬆️ Transit: {moon_data.transit_time} UTC")
            
            fields.insert(3, {
                "name": "⏰ Today's Times (UTC)",
                "value": " • ".join(timing),
                "inline": False
            })
        
        return {
            "title": f"🌙 {moon_data.phase_name}",
            "description": f"*Real-time lunar data for astronomical observation and photography*",
            "color": color,
            "fields": fields,
            "image": {
                "url": f"attachment://{moon_data.image_file}"
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "footer": {
                "text": f"Outlaw on watch duty • Updated every 6 hours • Observer: Naaldwijk, NL"
            }
        }


class MoonPhaseBot:
    """Main bot orchestrator"""
    
    def __init__(self, webhook_url: str, config_path: Optional[Path] = None):
        self.config = Configuration(config_path or Path('config.json'))
        self.calculator = AstronomicalCalculator(self.config)
        self.webhook = DiscordWebhookManager(webhook_url, self.config)
        
    def run(self) -> bool:
        """Execute bot workflow"""
        try:
            logger.info("=" * 60)
            logger.info("Moon Phase Bot - Starting Update Cycle")
            logger.info("=" * 60)
            
            # Calculate moon data
            logger.info("Calculating astronomical data...")
            moon_data = self.calculator.calculate_moon_data()
            
            logger.info(f"Current phase: {moon_data.phase_name} ({moon_data.illumination}%)")
            logger.info(f"Distance: {moon_data.distance_km:,} km ({moon_data.distance_variation:+.2f}%)")
            logger.info(f"Visibility: {'Visible' if moon_data.is_visible else 'Below horizon'}")
            
            # Delete old message
            old_message_id = self.config.get_message_id()
            if old_message_id:
                logger.info(f"Deleting old message: {old_message_id}")
                self.webhook.delete_message(old_message_id)
            
            # Post new message
            logger.info("Posting new message to Discord...")
            new_message_id = self.webhook.post_message(moon_data)
            
            if new_message_id:
                self.config.save_message_id(new_message_id)
                logger.info(f"✅ Successfully posted message: {new_message_id}")
                logger.info("=" * 60)
                return True
            else:
                logger.error("❌ Failed to post message")
                logger.info("=" * 60)
                return False
                
        except Exception as e:
            logger.error(f"Critical error in bot execution: {e}", exc_info=True)
            return False


def main():
    """Main entry point"""
    import os
    
    webhook_url = os.getenv('DISCORD_WEBHOOK')
    
    if not webhook_url:
        logger.error("DISCORD_WEBHOOK environment variable not set")
        sys.exit(1)
    
    bot = MoonPhaseBot(webhook_url)
    success = bot.run()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
