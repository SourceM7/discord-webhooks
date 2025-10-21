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
    # Convert from AU to km (1 AU ≈ 149,597,870.7 km)
    distance_km = moon.earth_distance * 149597870.7
    return round(distance_km)

def get_fun_fact():
    """Return a random moon fact"""
    facts = [
        "drifts 3.8cm away from Earth each year",
        "has quakes called 'moonquakes' that can last up to an hour",
        "is slowly slowing Earth's rotation",
        "has no atmosphere, so there's no weather",
        "appears the same size as the Sun from Earth due to cosmic coincidence",
        "has a day that lasts about 29.5 Earth days",
        "is the fifth largest moon in our solar system",
        "causes Earth's tides through gravitational pull",
        "always shows the same face to Earth due to tidal locking",
        "has temperatures ranging from -173°C to 127°C"
    ]
    return random.choice(facts)

def get_photography_tip(phase_name):
    """Return technical photography settings based on moon phase"""
    tips = {
        "New Moon": "ISO 3200-6400, f/2.8-f/4, 15-30s exposure for deep sky. Use manual focus at infinity. Stack multiple frames to reduce noise.",
        "Waxing Crescent": "ISO 400-800, f/5.6-f/8, 1/60-1/125s for lit portion. Bracket exposures ±2 EV to capture earthshine detail.",
        "First Quarter": "ISO 100-200, f/8-f/11, 1/125-1/250s. Optimal terminator contrast for surface detail. Use 300mm+ focal length.",
        "Waxing Gibbous": "ISO 200-400, f/8-f/11, 1/250-1/500s. HDR bracketing recommended for mare and highland detail preservation.",
        "Full Moon": "ISO 100, f/11-f/16, 1/250-1/500s. Use lunar mode or spot metering. 400mm+ recommended for maximum surface resolution.",
        "Waning Gibbous": "ISO 100-200, f/8-f/11, 1/125-1/250s. Morning shoot requires faster shutter to freeze atmospheric turbulence.",
        "Last Quarter": "ISO 100-200, f/8-f/11, 1/125-1/250s. Western terminator visible. Best atmospheric seeing 2-3 hours before sunrise.",
        "Waning Crescent": "ISO 400-800, f/5.6-f/8, 1/60-1/125s. Pre-dawn shoot with graduated ND filter for sky balance if including foreground."
    }
    return tips.get(phase_name, "ISO 100-200, f/8-f/11, 1/125-1/250s baseline. Tripod and remote shutter essential for sharp results.")

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
    
    # Determine if waxing or waning
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
    
    # Create embed message
    embed = {
        "title": f"🌙 {moon_data['name']}",
        "color": 0x2C2F33,
        "fields": [
            {
                "name": "Illumination",
                "value": f"{moon_data['illumination']}%",
                "inline": True
            },
            {
                "name": "Next Full Moon",
                "value": moon_data['next_full'],
                "inline": True
            },
            {
                "name": "Next New Moon",
                "value": moon_data['next_new'],
                "inline": True
            },
            {
                "name": "Distance",
                "value": f"{distance:,} km",
                "inline": True
            },
            {
                "name": "Moon Fact",
                "value": fun_fact.capitalize(),
                "inline": True
            },
            {
                "name": "\u200b",
                "value": "\u200b",
                "inline": True
            },
            {
                "name": "Camera Settings",
                "value": photo_tip,
                "inline": False
            }
        ],
        "image": {
            "url": f"attachment://{moon_data['image_file']}"
        },
        "timestamp": datetime.utcnow().isoformat(),
        "footer": {
            "text": "Outlaw on watch duty"
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
