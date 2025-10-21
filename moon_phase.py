import ephem
import requests
import os
import json
from datetime import datetime
import random

def get_moon_distance():
    """Calculate current distance to the moon in km"""
    moon = ephem.Moon()
    observer = ephem.Observer()
    observer.date = datetime.utcnow()
    moon.compute(observer)
    distance_km = moon.earth_distance * 149597870.7
    return round(distance_km)

def get_fun_fact():
    """Return an engaging, detailed moon fact"""
    facts = [
        "The Moon is receding from Earth at 3.78cm per year—in 600 million years, total solar eclipses will become impossible as it appears too small to cover the Sun",
        "Moonquakes occur up to 1,200km deep (Earth's deepest quakes are ~700km), and unlike Earth quakes that last seconds, they can reverberate for over 10 minutes due to the dry, rigid interior",
        "The Moon's gravity is slowing Earth's rotation by 2 milliseconds per century—when dinosaurs roamed, a day was only 23 hours long",
        "With no atmosphere to erode them, Neil Armstrong's footprints will remain pristine for at least 100 million years, preserved in the lunar regolith",
        "The Moon and Sun appear the same size from Earth (0.5° angular diameter) purely by cosmic coincidence—no other known planet-moon system shares this perfect alignment for total eclipses",
        "A lunar day (sunrise to sunrise) lasts 29.5 Earth days, meaning the Apollo astronauts experienced less than one full 'day' during their entire moon missions",
        "The Moon is the fifth-largest natural satellite in the Solar System, but proportionally the largest—it's 27% the size of Earth, while most moons are <5% of their planet's diameter",
        "The Moon's gravitational influence creates two tidal bulges on Earth, but friction causes them to drag ahead—this angular momentum transfer is what pushes the Moon farther from us each year",
        "Tidal locking occurred within the first 100 million years of the Moon's formation, meaning the far side remained unseen by humanity until Luna 3 photographed it in 1959",
        "The Moon's surface temperature swings 300°C between lunar day (+127°C) and night (-173°C)—the most extreme temperature range of any airless body in the inner Solar System",
        "The Moon has a mass of 7.342 × 10²² kg, which is roughly 1.2% of Earth's mass—large enough to make the Earth-Moon system technically a double planet rather than a planet-moon system",
        "Lunar soil contains helium-3, an isotope extremely rare on Earth but abundant on the Moon—just 100 tonnes could power humanity's energy needs for a year with fusion reactors",
        "The Moon's origin from a Mars-sized impactor 4.5 billion years ago means Earth and Moon share remarkably similar isotopic compositions—they're essentially made from the same cosmic material",
        "Ancient coral fossils reveal that 400 million years ago, the Moon was 10,000km closer, making it appear 50% larger in the sky and creating massive 300-meter tides",
        "The Moon's center of mass is offset 2km toward Earth from its geometric center, creating a permanent gravitational asymmetry that reinforces its tidal lock"
    ]
    return random.choice(facts)

def get_phase_color(phase_name):
    """Return sophisticated embed color based on moon phase"""
    phase_colors = {
        "New Moon": 0x0B0D21,        # Deep space black-blue
        "Waxing Crescent": 0x1A2332,  # Dark slate blue
        "First Quarter": 0x4A5F7F,    # Steel blue
        "Waxing Gibbous": 0x7A8FA8,   # Silver-blue
        "Full Moon": 0xE8EAF0,        # Luminous silver-white
        "Waning Gibbous": 0x8B9AAE,   # Muted silver-blue
        "Last Quarter": 0x5A6B82,     # Twilight blue
        "Waning Crescent": 0x242D3D   # Midnight blue
    }
    return phase_colors.get(phase_name, 0x2C2F33)

def get_photography_tip(phase_name):
    """Return professional-grade photography guidance"""
    tips = {
        "New Moon": """**Deep Sky Opportunity** • No lunar interference
ISO 3200-6400 • f/2.8-f/4 • 15-30s exposures
Target Milky Way core, nebulae, or galaxies. Use wide-angle (14-24mm) for landscapes. Manual focus at infinity with live view magnification. Stack 20+ frames in Sequator/Starry Landscape Stacker. Apply gradient removal and star enhancement in post.""",
        
        "Waxing Crescent": """**Earthshine Detail Challenge** • Thin illuminated crescent with ghostly Earth-lit portion
ISO 400-800 • f/5.6-f/8 • 1/60-1/125s for crescent
Bracket ±2-3 EV to capture both bright crescent and subtle earthshine. Use 200-400mm focal length. Merge exposures in HDR or manual blend. Blue hour timing optimal for atmospheric color gradients. Enhance earthshine subtly—aim for natural luminosity.""",
        
        "First Quarter": """**Terminator Detail Maximum** • Optimal relief and shadow contrast
ISO 100-200 • f/8-f/11 • 1/125-1/250s
Golden hour for lunar photography: terminator reveals craters, mountains, and rilles in stark relief. Use 400mm+ for crater detail (Copernicus, Tycho, Clavius). Lucky imaging: capture 1000+ frames at 30fps, stack best 10% in AutoStakkert. Wavelets sharpen in Registax. Target: Montes Apenninus, Mare Imbrium.""",
        
        "Waxing Gibbous": """**Full Surface Coverage** • Mare and highland detail preservation
ISO 200-400 • f/8-f/11 • 1/250-1/500s
HDR bracketing essential: 5-7 exposures, ±2 EV. Merge in Photoshop/Affinity with detail preservation. Use RGB filters or color camera to capture subtle surface color variations. Target Tycho ray system, Mare Nectaris. Apply subtle local contrast enhancement. Atmospheric dispersion correction if shooting low elevation.""",
        
        "Full Moon": """**Maximum Resolution Challenge** • Surface detail vs. overexposure balance
ISO 100 • f/11-f/16 • 1/250-1/500s
Spot meter on Moon to avoid overexposure. 600mm+ ideal for full disc detail. Use electronic first curtain shutter to minimize vibration. Shoot in RAW for highlight recovery. Atmospheric seeing critical: wait for calm air (avoid nights after cold fronts). Create mosaic from multiple exposures. Apply clarity and texture enhancement conservatively.""",
        
        "Waning Gibbous": """**Pre-Dawn Surface Detail** • Western terminator visible
ISO 100-200 • f/8-f/11 • 1/125-1/250s
Best atmospheric seeing 2-3 hours before sunrise when air is stable. Faster shutter compensates for atmospheric turbulence. Target: Mare Crisium, Mare Fecunditatis. Use barlow or teleconverter for magnification. Apply deconvolution sharpening in post. Pre-dawn blue hour allows foreground incorporation with graduated ND.""",
        
        "Last Quarter": """**Western Terminator Study** • Crater relief from opposite angle
ISO 100-200 • f/8-f/11 • 1/125-1/250s
Mirror image of First Quarter with reversed shadows revealing different surface features. Best seeing before astronomical twilight ends. Target: Grimaldi, Oceanus Procellarum, Aristarchus (brightest crater). Use video capture for lucky imaging. 400-600mm optimal. Process with high-pass filter for micro-contrast.""",
        
        "Waning Crescent": """**Pre-Dawn Earthshine** • Delicate crescent in twilight
ISO 400-800 • f/5.6-f/8 • 1/60-1/125s
Shoot 30-45min before sunrise. Use 200-300mm for crescent isolation. Graduated ND filter if including foreground landscape. Bracket for HDR merge of bright crescent and dim earthshine. Venus often visible nearby—compositional opportunity. Manual blend for natural atmospheric glow. Enhance earthshine blues subtly."""
    }
    return tips.get(phase_name, "ISO 100-200 • f/8-f/11 • 1/125-1/250s baseline\nTripod essential. Mirror lock-up or electronic shutter. 2-second timer or remote release. Shoot RAW for maximum post-processing flexibility.")

def get_moon_emoji(phase_name):
    """Return appropriate moon emoji for phase"""
    emojis = {
        "New Moon": "🌑",
        "Waxing Crescent": "🌒",
        "First Quarter": "🌓",
        "Waxing Gibbous": "🌔",
        "Full Moon": "🌕",
        "Waning Gibbous": "🌖",
        "Last Quarter": "🌗",
        "Waning Crescent": "🌘"
    }
    return emojis.get(phase_name, "🌙")

def get_moon_phase():
    """Calculate current moon phase and return details"""
    moon = ephem.Moon()
    moon.compute()
    
    illumination = moon.phase
    
    observer = ephem.Observer()
    observer.date = datetime.utcnow()
    
    prev_new = ephem.previous_new_moon(observer.date)
    next_new = ephem.next_new_moon(observer.date)
    prev_full = ephem.previous_full_moon(observer.date)
    next_full = ephem.next_full_moon(observer.date)
    
    days_since_new = observer.date - prev_new
    
    if days_since_new < 1:
        phase_name = "New Moon"
        image_file = "Moon_Phase_5_Alt.png"
    elif days_since_new < 6:
        phase_name = "Waxing Crescent"
        image_file = "Moon_Phase_6_Alt.png"
    elif days_since_new < 9:
        phase_name = "First Quarter"
        image_file = "Moon_Phase_7_Alt.png"
    elif days_since_new < 13:
        phase_name = "Waxing Gibbous"
        image_file = "Moon_Phase_8_Alt.png"
    elif days_since_new < 16:
        phase_name = "Full Moon"
        image_file = "Moon_Phase_1_Alt.png"
    elif days_since_new < 20:
        phase_name = "Waning Gibbous"
        image_file = "Moon_Phase_2_Alt.png"
    elif days_since_new < 23:
        phase_name = "Last Quarter"
        image_file = "Moon_Phase_3_Alt.png"
    else:
        phase_name = "Waning Crescent"
        image_file = "Moon_Phase_4_Alt.png"
    
    return {
        'name': phase_name,
        'illumination': round(illumination, 1),
        'next_full': ephem.Date(next_full).datetime().strftime('%B %d, %Y'),
        'next_new': ephem.Date(next_new).datetime().strftime('%B %d, %Y'),
        'image_file': image_file
    }

def get_message_id():
    """Retrieve stored message ID from file"""
    try:
        with open('message_id.txt', 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        return None

def save_message_id(message_id):
    """Save message ID to file"""
    with open('message_id.txt', 'w') as f:
        f.write(message_id)

def delete_and_post_discord_message(webhook_url, moon_data, message_id=None):
    """Delete old message and create new Discord message with moon phase"""
    
    # Delete old message if it exists
    if message_id:
        parts = webhook_url.rstrip('/').split('/')
        webhook_id = parts[-2]
        webhook_token = parts[-1]
        
        delete_url = f"https://discord.com/api/webhooks/{webhook_id}/{webhook_token}/messages/{message_id}"
        delete_response = requests.delete(delete_url)
        
        if delete_response.status_code == 204:
            print("🗑️ Successfully deleted old message!")
        else:
            print(f"⚠️ Could not delete old message: {delete_response.status_code}")
    
    # Prepare the image
    with open(moon_data['image_file'], 'rb') as f:
        image_data = f.read()
    
    # Get enhanced data
    distance = get_moon_distance()
    fun_fact = get_fun_fact()
    photo_tip = get_photography_tip(moon_data['name'])
    phase_color = get_phase_color(moon_data['name'])
    phase_emoji = get_moon_emoji(moon_data['name'])
    
    # Create sophisticated embed message
    embed = {
        "title": f"{phase_emoji}  {moon_data['name'].upper()}",
        "description": f"*Current lunar observation data and photography guidance*",
        "color": phase_color,
        "fields": [
            {
                "name": "◐ Phase Illumination",
                "value": f"**{moon_data['illumination']}%**",
                "inline": True
            },
            {
                "name": "○ Distance from Earth",
                "value": f"**{distance:,}** km\n*{distance / 1000:.1f}k km*",
                "inline": True
            },
            {
                "name": "⦿ Angular Size",
                "value": f"**~0.5°**\nApparent diameter",
                "inline": True
            },
            {
                "name": "━━━━━━━━━━━━━━━━━━━━━━━",
                "value": "",
                "inline": False
            },
            {
                "name": "🌕 Next Full Moon",
                "value": f"`{moon_data['next_full']}`",
                "inline": True
            },
            {
                "name": "🌑 Next New Moon",
                "value": f"`{moon_data['next_new']}`",
                "inline": True
            },
            {
                "name": "\u200b",
                "value": "\u200b",
                "inline": True
            },
            {
                "name": "━━━━━━━━━━━━━━━━━━━━━━━",
                "value": "",
                "inline": False
            },
            {
                "name": "📚 Lunar Science",
                "value": fun_fact,
                "inline": False
            },
            {
                "name": "━━━━━━━━━━━━━━━━━━━━━━━",
                "value": "",
                "inline": False
            },
            {
                "name": "📷 Photography Guide",
                "value": photo_tip,
                "inline": False
            }
        ],
        "image": {
            "url": f"attachment://{moon_data['image_file']}"
        },
        "timestamp": datetime.utcnow().isoformat(),
        "footer": {
            "text": "Outlaw Observatory • Lunar Observation Program"
        }
    }
    
    files = {
        'file': (moon_data['image_file'], image_data, 'image/png')
    }
    
    payload = {
        'embeds': [embed]
    }
    
    # Create new message
    response = requests.post(
        webhook_url,
        data={'payload_json': json.dumps(payload)},
        files=files,
        params={'wait': 'true'}
    )
    
    if response.status_code in [200, 204]:
        print("✅ Successfully posted new message to Discord!")
        try:
            response_data = response.json()
            new_message_id = response_data.get('id')
            if new_message_id:
                save_message_id(new_message_id)
                print(f"💾 Saved new message ID: {new_message_id}")
            return new_message_id
        except:
            print("⚠️ Could not extract message ID")
            return None
    else:
        print(f"❌ Error: {response.status_code} - {response.text}")
        return None

if __name__ == "__main__":
    webhook_url = os.getenv('DISCORD_WEBHOOK')
    
    if not webhook_url:
        print("❌ Error: DISCORD_WEBHOOK environment variable not set")
        exit(1)
    
    moon_data = get_moon_phase()
    print(f"🌙 Current phase: {moon_data['name']} ({moon_data['illumination']}%)")
    print(f"📁 Using image: {moon_data['image_file']}")
    
    message_id = get_message_id()
    new_message_id = delete_and_post_discord_message(webhook_url, moon_data, message_id)
    
    if new_message_id:
        print("🔄 Message replaced successfully!")
