import requests
import re
import json

# ==========================================
# CONFIGURATION: Source Playlists
# ==========================================
sources = [
    {"tag": "link1", "url": "https://raw.githubusercontent.com/Aftab071/AftabIPTV/refs/heads/main/SyncIT"},
    {"tag": "link2", "url": "https://raw.githubusercontent.com/sm-monirulislam/SM-Live-TV/refs/heads/main/Combined_Live_TV.m3u"},
    {"tag": "link3", "url": "https://raw.githubusercontent.com/DrSujonPaul/Sujon/refs/heads/main/iptv"},
    {"tag": "link4", "url": "https://sonamul4545.vercel.app/siyam3535.m3u"},
    {"tag": "link5", "url": "https://raw.githubusercontent.com/sm-monirulislam/AynaOTT-auto-update-playlist/refs/heads/main/AynaOTT.m3u"}
]

# ==========================================
# CONFIGURATION: Manual Channels (Admin Links)
# ==========================================
manual_channels = [
    {
        "name": "Join Telegram: t.me/aftaahi_iptv",
        "group": "Admin Info",
        "logo": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/82/Telegram_logo.svg/1024px-Telegram_logo.svg.png",
        "link": "https://t.me/aftaahi_iptv"
    },
    {
        "name": "Admin : Aftab Uddin",
        "group": "Admin Info",
        "logo": "https://i.ibb.co/hRvpjD8/telegram-logo.png",
        "link": "https://t.me/aftaahi"
    }
]

# ==========================================
# CONFIGURATION: Group Sorting Priority
# ==========================================
group_priority = [
    "Admin Info",
    "Live Event",
    "Bangla",
    "Kolkata",
    "Sports",
    "India",
    "Hindi",
    "Others"
]

# ==========================================
# HELPER FUNCTIONS
# ==========================================
def load_logos():
    """Loads logo mapping from logos.json file."""
    try:
        with open("logos.json", "r", encoding="utf-8", errors="ignore") as f:
            data = json.load(f)
            return {k.strip().lower(): v.strip() for k, v in data.items()}
    except Exception:
        return {}

def find_smart_logo(channel_name, logo_map):
    """Fuzzy logic to find logos matching channel names."""
    if channel_name in logo_map:
        return logo_map[channel_name]
    
    clean_channel = channel_name.replace(" ", "").replace("-", "").replace(":", "")
    clean_channel = clean_channel.replace("hd", "").replace("fhd", "").replace("4k", "")
    
    for key, url in logo_map.items():
        clean_key = key.replace(" ", "").replace("-", "").replace(":", "")
        if clean_key in clean_channel:
            return url
    return None

def generate_playlist():
    """Main function to fetch, filter, and generate the playlist."""
    specific_rules = {} 
    wildcard_rules = []
    
    logo_map = load_logos()
    print(f"[-] Loaded {len(logo_map)} logos.")

    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
    
    all_channels = []

    # 1. Add Manual Channels (Admin Links)
    for manual in manual_channels:
        m_name = manual["name"]
        m_group = manual["group"]
        m_logo = manual["logo"]
        m_link = manual["link"]
        
        # Try to find logo if missing
        if not m_logo:
            found = find_smart_logo(m_name.lower(), logo_map)
            if found: m_logo = found

        content = f'#EXTINF:-1 group-title="{m_group}" tvg-logo="{m_logo}", {m_name}\n{m_link}\n'
        all_channels.append({"group": m_group, "content": content})

    # 2. Load Filtering Rules
    try:
        with open("my_channels.txt", "r", encoding="utf-8", errors="ignore") as file:
            for line in file:
                line = line.strip()
                if not line or line.startswith("#"): continue
                parts = [p.strip() for p in line.split("|")]
                
                if len(parts) == 3:
                    tag, src_grp, src_nm, tgt_grp = "*", parts[0], parts[1].lower(), parts[2]
                elif len(parts) == 4:
                    tag, src_grp, src_nm, tgt_grp = parts[0].lower(), parts[1], parts[2].lower(), parts[3]
                else: continue

                if src_nm == "*":
                    wildcard_rules.append({"tag": tag, "src_group": src_grp, "target": tgt_grp})
                else:
                    specific_rules[(tag, src_grp, src_nm)] = tgt_grp
    except Exception:
        print("[!] Warning: Could not read my_channels.txt")

    # 3. Fetch and Process Sources
    added_ids = set() 
    
    for source in sources:
        tag, url = source["tag"], source["url"]
        try:
            print(f"[*] Scanning source: {tag}...")
            response = requests.get(url, headers=headers, timeout=20)
            
            if response.status_code == 200:
                lines = response.text.split('\n')
                for i in range(len(lines)):
                    line = lines[i].strip()
                    if line.startswith("#EXTINF"):
                        grp_match = re.search(r'group-title="([^"]*)"', line)
                        name_raw = line.split(',')[-1].strip()
                        
                        if grp_match:
                            cur_grp = grp_match.group(1).strip()
                            cur_nm = name_raw.strip().lower()
                            final_tgt = None
                            
                            # Check Specific Rules
                            if (tag, cur_grp, cur_nm) in specific_rules:
                                final_tgt = specific_rules[(tag, cur_grp, cur_nm)]
                            elif ("*", cur_grp, cur_nm) in specific_rules:
                                final_tgt = specific_rules[("*", cur_grp, cur_nm)]
                            else:
                                # Check Wildcard Rules
                                for rule in wildcard_rules:
                                    if (rule["tag"] == tag or rule["tag"] == "*") and (rule["src_group"].lower() in cur_grp.lower()):
                                        final_tgt = rule["target"]
                                        break
                            
                            if final_tgt:
                                link_line = lines[i+1].strip() if i+1 < len(lines) and not lines[i+1].startswith("#") else ""
                                
                                if link_line and (final_tgt, cur_nm) not in added_ids:
                                    # Update Group Title
                                    mod_line = re.sub(r'group-title="[^"]*"', f'group-title="{final_tgt}"', line)
                                    
                                    # Update Logo if available
                                    found_logo_url = find_smart_logo(cur_nm, logo_map)
                                    if found_logo_url:
                                        if 'tvg-logo="' in mod_line:
                                            mod_line = re.sub(r'tvg-logo="[^"]*"', f'tvg-logo="{found_logo_url}"', mod_line)
                                        else:
                                            mod_line = mod_line.replace("#EXTINF:-1", f'#EXTINF:-1 tvg-logo="{found_logo_url}"')
                                    
                                    all_channels.append({"group": final_tgt, "content": mod_line + "\n" + link_line + "\n"})
                                    added_ids.add((final_tgt, cur_nm))
        except Exception as e:
            print(f"[!] Error processing {tag}: {e}")

    # 4. Sort and Save Playlist
    all_channels.sort(key=lambda x: group_priority.index(x["group"]) if x["group"] in group_priority else 999)

    with open("my_playlist.m3u", "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for ch in all_channels:
            f.write(ch["content"])
    
    print(f"[+] Success! Generated playlist with {len(all_channels)} channels.")

if __name__ == "__main__":
    generate_playlist()
