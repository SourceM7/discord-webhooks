import ephem
import requests
import os
import json
from datetime import datetime

def get_moon_phase():
    """Calculate current moon phase and return details"""
    moon = ephem.Moon()
    moon.compute()
    
    illumination = moon.phase
    

    if illumination >= 96:
        phase_name = "Full Moon"
        image_file = "Moon_Phase_1_Alt.png"
    elif illumination >= 76:
        phase_name = "Waxing Gibbous"
        image_file = "Moon_Phase_8_Alt.png"
    elif illumination >= 51:
        phase_name = "First Quarter"
        image_file = "Moon_Phase_7_Alt.png"
    elif illumination >= 26:
        phase_name = "Waxing Crescent"
        image_file = "Moon_Phase_6_Alt.png"
    elif illumination >= 4:
        phase_name = "New Moon"
        image_file = "Moon_Phase_5_Alt.png"
    elif illumination >= 1:
        observer = ephem.Observer()
        observer.date = datetime.utcnow()
        prev_new = ephem.previous_new_moon(observer.date)
        next_new = ephem.next_new_moon(observer.date)
        
        if abs(observer.date - prev_new) < abs(observer.date - next_new):
            phase_name = "Waxing Crescent"
            image_file = "Moon_Phase_6_Alt.png"
        else:
            phase_name = "Waning Crescent"
            image_file = "Moon_Phase_4_Alt.png"
    else:
        phase_name = "New Moon"
        image_file = "Moon_Phase_5_Alt.png"
    
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

def update_discord_message(webhook_url, moon_data, message_id=None):
    """Update or create Discord message with moon phase"""
    
    with open(moon_data['image_file'], 'rb') as f:
        image_data = f.read()
    
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
    
    if message_id:

      
        parts = webhook_url.rstrip('/').split('/')
        webhook_id = parts[-2]
        webhook_token = parts[-1]
        
        update_url = f"https://discord.com/api/webhooks/{webhook_id}/{webhook_token}/messages/{message_id}"
        
        response = requests.patch(
            update_url,
            data={'payload_json': json.dumps(payload)},
            files=files
        )
        
        if response.status_code == 200:
            print("✅ Successfully updated Discord message!")
            return message_id
        else:
            print(f"⚠️ Failed to update message: {response.status_code}")
            print(f"Creating new message instead...")
            return None
    
    response = requests.post(
        webhook_url,
        data={'payload_json': json.dumps(payload)},
        files=files,
        params={'wait': 'true'}  
    )
    
    if response.status_code in [200, 204]:
        print("✅ Successfully posted to Discord!")
        try:
            response_data = response.json()
            new_message_id = response_data.get('id')
            if new_message_id:
                save_message_id(new_message_id)
                print(f"💾 Saved message ID: {new_message_id}")
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
    
    new_message_id = update_discord_message(webhook_url, moon_data, message_id)
    
    if new_message_id and not message_id:
        print("🆕 First time posting - future runs will update this message")
