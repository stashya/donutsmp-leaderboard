import os
import json
import re
import requests
from datetime import datetime

DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN")
CHANNEL_ID = "1373579452998746155"  # The spawner prices channel

def fetch_latest_messages(limit=10):
    """Fetch the latest messages from the Discord channel."""
    if not DISCORD_TOKEN:
        print("Error: DISCORD_TOKEN environment variable not set")
        return None
    
    url = f"https://discord.com/api/v9/channels/{CHANNEL_ID}/messages"
    headers = {
        "Authorization": DISCORD_TOKEN,
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    params = {"limit": limit}
    
    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code != 200:
        print(f"Error fetching messages: {response.status_code}")
        print(response.text)
        return None
    
    return response.json()

def parse_spawner_prices(messages):
    """
    Parse spawner prices from messages.
    
    Expected format:
    > - <:SkeletonFace:1379787344495771698>Skeleton Spawners  **1.2m** each
    > - Spider Spawners **450k** each
    """
    data = {
        "buying": {},   # Prices when YOU sell TO them
        "selling": {}   # Prices when YOU buy FROM them
    }
    
    # Regex to extract spawner name and price
    # Matches lines with spawner type and **price** each
    price_pattern = re.compile(
        r'([A-Za-z\s]+?)\s*Spawners?\s+\*\*([0-9.]+[kmb]?(?:\s*-\s*[0-9.]+[kmb])?)\*\*\s*each',
        re.IGNORECASE
    )
    
    for msg in messages:
        content = msg.get("content", "")
        timestamp = msg.get("timestamp", "")
        author = msg.get("author", {}).get("username", "unknown")
        
        # Remove custom Discord emojis for cleaner parsing
        content_clean = re.sub(r'<a?:\w+:\d+>', '', content)
        
        # Determine current section (buying vs selling)
        current_section = None
        
        for line in content_clean.split("\n"):
            line_lower = line.lower()
            
            # Detect section headers
            if "buying" in line_lower and "you sell" in line_lower:
                current_section = "buying"
                continue
            elif "selling" in line_lower and ("we sell" in line_lower or "you buy" in line_lower):
                current_section = "selling"
                continue
            
            # Try to extract price
            match = price_pattern.search(line)
            if match:
                spawner_type = match.group(1).strip()
                price = match.group(2).strip().lower()
                
                # Normalize spawner type name
                spawner_type = spawner_type.title().strip()
                
                # Skip empty names
                if not spawner_type or len(spawner_type) < 2:
                    continue
                
                section = current_section or "unknown"
                
                data[section][spawner_type] = {
                    "price": price,
                    "source_timestamp": timestamp,
                    "author": author
                }
                
                print(f"  Found: {spawner_type} = {price} ({section})")
    
    # Remove empty sections
    data = {k: v for k, v in data.items() if v}
    
    return data

def main():
    print("Fetching Discord messages...")
    messages = fetch_latest_messages(limit=10)
    
    if not messages:
        print("Failed to fetch messages")
        return
    
    print(f"Fetched {len(messages)} messages")
    
    # Parse prices
    prices = parse_spawner_prices(messages)
    
    # Count total prices found
    total_prices = sum(len(section) for section in prices.values())
    
    # Create output
    output = {
        "updated_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "channel_id": CHANNEL_ID,
        "total_prices": total_prices,
        "prices": prices,
        "raw_messages": [
            {
                "id": msg["id"],
                "content": msg.get("content", ""),
                "timestamp": msg.get("timestamp", ""),
                "author": msg.get("author", {}).get("username", "unknown")
            }
            for msg in messages
        ]
    }
    
    # Save to file
    with open("spawner_prices.json", "w") as f:
        json.dump(output, f, indent=2)
    
    print(f"\nDone! Found {total_prices} spawner prices")
    for section, items in prices.items():
        print(f"  {section.title()}: {len(items)} types")
    print("Saved to spawner_prices.json")

if __name__ == "__main__":
    main()
