import requests
import re
import json
import base64

# ==========================================
# আপনার ওয়েবসাইট লিংক (Link Masking Server)
# ==========================================
MY_SERVER_URL = "http://aftabiptv.rf.gd/play.php"
# ==========================================

sources = [
    {"tag": "link1", "url": "https://raw.githubusercontent.com/Aftab071/AftabIPTV/refs/heads/main/SyncIT"},
    {"tag": "link2", "url": "https://raw.githubusercontent.com/sm-monirulislam/SM-Live-TV/refs/heads/main/Combined_Live_TV.m3u"},
    {"tag": "link3", "url": "https://raw.githubusercontent.com/DrSujonPaul/Sujon/refs/heads/main/iptv"},
    {"tag": "link4", "url": "https://sonamul4545.vercel.app/siyam3535.m3u"},
    {"tag": "link5", "url": "https://raw.githubusercontent.com/sm-monirulislam/AynaOTT-auto-update-playlist/refs/heads/main/AynaOTT.m3u"}
]

group_priority = ["Live Event", "Bangla", "Kolkata", "Sports", "India", "Hindi", "Others"]

def load_logos():
    try:
        with open("logos.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            return {k.strip().lower(): v.strip() for k, v in data.items()}
    except:
        return {}

def find_smart_logo(channel_name, logo_map):
    if channel_name in logo_map: return logo_map[channel_name]
    clean_channel = channel_name.replace(" ", "").replace("-", "").replace(":", "").replace("hd", "").replace("fhd", "").replace("4k", "")
    for key, url in logo_map.items():
        clean_key = key.replace(" ", "").replace("-", "").replace(":", "")
        if clean_key in clean_channel: return url
    return None

def generate_playlist():
    specific_rules = {} 
    wildcard_rules = []
    
    logo_map = load_logos()
    print(f"✅ Loaded {len(logo_map)} logos")

    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
    
    try:
        with open("my_channels.txt", "r", encoding="utf-8") as file:
            for line in file:
                line = line.strip()
                if not line or line.startswith("#"): continue
                
                parts = [p.strip() for p in line.split("|")]
                if len(parts) == 3:
                    tag, src_grp, src_nm, tgt_grp = "*", parts[0], parts[1].lower(), parts[2]
                elif len(parts) == 4:
                    tag, src_grp, src_nm, tgt_grp = parts[0].lower(), parts[1], parts[2].lower(), parts[3]
                else: continue

                if src_nm == "*": wildcard_rules.append({"tag": tag, "src_group": src_grp, "target": tgt_grp})
                else: specific_rules[(tag, src_grp, src_nm)] = tgt_grp
    except:
        print("Error reading my_channels.txt")
        return

    all_channels = []
    added_ids = set() 
    
    for source in sources:
        tag, url = source["tag"], source["url"]
        try:
            print(f"Scanning [{tag}]...")
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
                            
                            if (tag, cur_grp, cur_nm) in specific_rules: final_tgt = specific_rules[(tag, cur_grp, cur_nm)]
                            elif ("*", cur_grp, cur_nm) in specific_rules: final_tgt = specific_rules[("*", cur_grp, cur_nm)]
                            else:
                                for rule in wildcard_rules:
                                    if (rule["tag"] == tag or rule["tag"] == "*") and (rule["src_group"].lower() in cur_grp.lower()):
                                        final_tgt = rule["target"]
                                        break
                            
                            if final_tgt:
                                link_line = lines[i+1].strip() if i+1 < len(lines) and not lines[i+1].startswith("#") else ""
                                
                                if link_line and (final_tgt, cur_nm) not in added_ids:
                                    mod_line = re.sub(r'group-title="[^"]*"', f'group-title="{final_tgt}"', line)
                                    
                                    found_logo_url = find_smart_logo(cur_nm, logo_map)
                                    if found_logo_url:
                                        if 'tvg-logo="' in mod_line:
                                            mod_line = re.sub(r'tvg-logo="[^"]*"', f'tvg-logo="{found_logo_url}"', mod_line)
                                        else:
                                            mod_line = mod_line.replace("#EXTINF:-1", f'#EXTINF:-1 tvg-logo="{found_logo_url}"')
                                    
                                    # === লিংক মাস্কিং (Link Masking) ===
                                    encoded_link = base64.b64encode(link_line.encode('utf-8')).decode('utf-8')
                                    masked_link = f"{MY_SERVER_URL}?id={encoded_link}"
                                    
                                    all_channels.append({"group": final_tgt, "content": mod_line + "\n" + masked_link + "\n"})
                                    added_ids.add((final_tgt, cur_nm))
        except Exception as e: print(f"Error {tag}: {e}")

    all_
