import requests
import re
import json

# ==========================================
# ১. সোর্স লিংকস
# ==========================================
sources = [
    {"tag": "link1", "url": "https://raw.githubusercontent.com/Aftab071/AftabIPTV/refs/heads/main/SyncIT"},
    {"tag": "link2", "url": "https://raw.githubusercontent.com/sm-monirulislam/SM-Live-TV/refs/heads/main/Combined_Live_TV.m3u"},
    {"tag": "link3", "url": "https://raw.githubusercontent.com/DrSujonPaul/Sujon/refs/heads/main/iptv"},
    {"tag": "link4", "url": "https://sonamul4545.vercel.app/siyam3535.m3u"},
    {"tag": "link5", "url": "https://raw.githubusercontent.com/sm-monirulislam/AynaOTT-auto-update-playlist/refs/heads/main/AynaOTT.m3u"}
]

# ==========================================
# ২. ম্যানুয়াল চ্যানেল (ভিডিও এবং টেলিগ্রাম)
# ==========================================
manual_channels = [
    # আপনার আপলোড করা ভিডিও
    {
        "name": "Justice For Hadi",
        "group": "My Uploads",
        "logo": "https://i.ibb.co/hRvpjD8/telegram-logo.png",
        "link": "https://archive.org/download/osman-hadi-kazi-nazrul-is-4/%E0%A6%86%E0%A6%97%E0%A7%81%E0%A6%A8%20%E0%A6%9D%E0%A7%9C%E0%A6%BE%20%E0%A6%86%E0%A6%AC%E0%A7%83%E0%A6%A4%E0%A7%8D%E0%A6%A4%E0%A6%BF%E0%A5%A4%20%E0%A6%95%E0%A6%AC%E0%A6%BF%E0%A6%A4%E0%A6%BE%E0%A6%9F%E0%A6%BE%20%E0%A6%AF%E0%A7%87%E0%A6%A8%20%E0%A6%8F%E0%A6%AC%E0%A6%BE%E0%A6%B0%20%E0%A6%AA%E0%A7%82%E0%A6%B0%E0%A7%8D%E0%A6%A3%E0%A6%A4%E0%A6%BE%20%E0%A6%AA%E0%A7%87%E0%A6%B2%E0%A5%A4%20Osman%20Hadi%20_%20Kazi%20Nazrul%20Is%284.mp4"
    },
    # আপনার নতুন টেলিগ্রাম চ্যানেল লিংক
    {
        "name": "Join Telegram: Aftaahi IPTV",
        "group": "Admin Info",
        "logo": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/82/Telegram_logo.svg/1024px-Telegram_logo.svg.png",
        "link": "https://t.me/aftaahi_iptv"
    }
]
# ==========================================

# ==========================================
# ৩. গ্রুপ সিরিয়াল
# ==========================================
group_priority = [
    "Admin Info",    # টেলিগ্রাম লিংক এখানে থাকবে
    "My Uploads",    # আপনার ভিডিও এখানে থাকবে
    "Live Event",
    "Bangla",
    "Kolkata",
    "Sports",
    "India",
    "Hindi",
    "Others"
]

# অ্যাডমিন ওনার প্রোফাইল (সবার উপরে থাকবে)
ADMIN_NAME = "OWNER: Aftab071"
ADMIN_LOGO = "https://i.ibb.co/hRvpjD8/telegram-logo.png"
TELEGRAM_LINK = "https://t.me/aftab071"

def load_logos():
    try:
        with open("logos.json", "r", encoding="utf-8", errors="ignore") as f:
            data = json.load(f)
            return {k.strip().lower(): v.strip() for k, v in data.items()}
    except: return {}

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
    
    all_channels = []
    
    # 1. Admin Info (Owner Card)
    admin_content = f'#EXTINF:-1 group-title="Admin Info" tvg-logo="{ADMIN_LOGO}", {ADMIN_NAME}\n{TELEGRAM_LINK}\n'
    all_channels.append({"group": "Admin Info", "content": admin_content})

    # 2. Manual Channels (Video + New Telegram) যোগ করা হচ্ছে
    for manual in manual_channels:
        m_name = manual["name"]
        m_group = manual["group"]
        m_logo = manual["logo"]
        m_link = manual["link"]
        
        # যদি লোগো খালি থাকে, স্মার্ট লোগো খুঁজবে
        if not m_logo:
            found = find_smart_logo(m_name.lower(), logo_map)
            if found: m_logo = found

        content = f'#EXTINF:-1 group-title="{m_group}" tvg-logo="{m_logo}", {m_name}\n{m_link}\n'
        all_channels.append({"group": m_group, "content": content})

    # 3. Scraped Channels
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
                if src_nm == "*": wildcard_rules.append({"tag": tag, "src_group": src_grp, "target": tgt_grp})
                else: specific_rules[(tag, src_grp, src_nm)] = tgt_grp
    except: pass

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
                                    all_channels.append({"group": final_tgt, "content": mod_line + "\n" + link_line + "\n"})
                                    added_ids.add((final_tgt, cur_nm))
        except Exception as e: print(f"Error {tag}: {e}")

    all_channels.sort(key=lambda x: group_priority.index(x["group"]) if x["group"] in group_priority else 999)

    with open("my_playlist.m3u", "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for ch in all_channels: f.write(ch["content"])
    
    print(f"✅ Done! Added Telegram Channel & Video.")

if __name__ == "__main__":
    generate_playlist()
