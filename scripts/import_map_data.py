
import re
import pandas as pd
from pathlib import Path
import html

def parse_folium_map(html_path, output_csv):
    """Parse Folium HTML map to extract mineral data."""
    if not Path(html_path).exists():
        print(f"Error: File not found {html_path}")
        return

    with open(html_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Regex to find markers and their popups
    # Matches patterns like:
    # circle_marker_... = L.circleMarker([35.8533, -79.42], ...
    # ...
    # <h4 ...>(.*?)</h4>
    # ...
    # <strong>County:</strong> (.*?)</p>
    # ...
    # <strong>Minerals:</strong></p>\s*<p.*?>(.*?)</p>
    
    # We'll first split by "L.circleMarker" to get chunks, then parse each chunk
    chunks = content.split('L.circleMarker(')
    
    sites = []
    
    print(f"Found {len(chunks)-1} potential markers")
    
    for chunk in chunks[1:]: # Skip first split (header)
        try:
            # Extract coordinates
            coord_match = re.search(r'\[([\d.-]+),\s*([\d.-]+)\]', chunk)
            if not coord_match:
                continue
            lat, lon = coord_match.groups()
            
            # Extract Name
            name_match = re.search(r'<h4.*?>(.*?)</h4>', chunk, re.DOTALL)
            name = html.unescape(name_match.group(1).strip()) if name_match else "Unknown Site"
            
            # Extract County
            county_match = re.search(r'<strong>County:</strong> (.*?)</p>', chunk)
            county = html.unescape(county_match.group(1).strip()) if county_match else ""
            
            # Extract Minerals
            minerals_match = re.search(r'<strong>Minerals:</strong></p>\s*<p.*?>(.*?)</p>', chunk, re.DOTALL)
            minerals = html.unescape(minerals_match.group(1).strip()) if minerals_match else ""
            
            # Clean up minerals string (remove newlines/tabs)
            minerals = re.sub(r'\s+', ' ', minerals)

            # Determine category
            min_lower = minerals.lower()
            name_lower = name.lower()
            
            m_type = "other"
            
            # Check for specific precious metals/gems first (Priority order)
            if "platinum" in min_lower or "palladium" in min_lower:
                m_type = "platinum"
            elif "uraninite" in min_lower or "uranium" in min_lower:
                m_type = "uranium"
            elif "diamond" in min_lower:
                m_type = "gems" # Diamond is a gem
            elif "emerald" in min_lower or "emerald" in name_lower:
                m_type = "emerald"
            elif "hiddenite" in min_lower or "hiddenite" in name_lower:
                m_type = "hiddenite"
            elif "ruby" in min_lower or "sapphire" in min_lower or "corundum" in min_lower:
                m_type = "ruby_sapphire"
            elif "gold" in min_lower or "gold" in name_lower:
                m_type = "gold"
            elif "silver" in min_lower or "silver" in name_lower:
                m_type = "silver"
            elif "copper" in min_lower or "chalcopyrite" in min_lower or "malachite" in min_lower or "azurite" in min_lower:
                # Chalcopyrite/Malachite/Azurite are copper ores
                m_type = "copper"
            elif "garnet" in min_lower:
                m_type = "garnet"
            elif "gem" in min_lower or "topaz" in min_lower or "beryl" in min_lower or "amethyst" in min_lower or "aquamarine" in min_lower or "tourmaline" in min_lower:
                m_type = "gems"
            elif "iron" in min_lower or "magnetite" in min_lower or "hematite" in min_lower:
                m_type = "iron"
            elif "lithium" in min_lower or "spodumene" in min_lower:
                m_type = "lithium"
            elif "mica" in min_lower or "feldspar" in min_lower or "kaolin" in min_lower or "pyrophyllite" in min_lower:
                m_type = "industrial"
            
            # Description
            desc = f"{minerals}. {county} County."
            
            sites.append({
                "name": name,
                "latitude": lat,
                "longitude": lon,
                "mineral_type": m_type,
                "description": desc
            })
            
        except Exception as e:
            print(f"Error parsing chunk: {e}")
            continue

    if not sites:
        print("No sites extracted!")
        return

    # Create DataFrame
    df = pd.DataFrame(sites)
    
    # Save to CSV
    df.to_csv(output_csv, index=False)
    print(f"Successfully exported {len(df)} sites to {output_csv}")
    print("\nMineral type distribution:")
    print(df['mineral_type'].value_counts())

if __name__ == "__main__":
    parse_folium_map(
        "C:/Users/Registered User/nc-localities/data/user_map.html",
        "C:/Users/Registered User/nc-localities/data/mineral_localities.csv"
    )
