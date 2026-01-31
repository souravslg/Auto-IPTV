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
    {"tag": "link4", "url": "https://sonamul4545.vercel.app/siyam3535.m3u"}
]

group_priority = ["Live Event", "Bangla", "Sports", "India", "Hindi", "Others"]

def load_logos():
    """ logos.json ফাইল লোড করে এবং সব নাম ছোট হাতের অক্ষরে কনভার্ট করে """
    try:
        with open("logos.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            
            # === ফিক্স: সব কি-ওয়ার্ড লোয়ারকেস (ছোট হাতের) করা হচ্ছে ===
            clean_map = {}
            for k, v in data.items():
                # নাম থেকে অযথা স্পেস সরানো হচ্ছে এবং ছোট হাতের করা হচ্ছে
                clean_key = k.strip().lower()
                clean_map[clean_key] = v.strip()
            
            return clean_map
            
    except FileNotFoundError:
        print("⚠️ Warning: logos.json file not found! Logos will be empty.")
        return {}
    except json.JSONDecodeError:
        print("❌ Error: logos.json file has format error! Check for extra commas.")
        return {}

def generate_playlist():
    specific_rules = {} 
    wildcard_rules = []
    
    # লোগো লোড করা হচ্ছে (সব ছোট হাতের অক্ষরে কনভার্ট হয়ে আসবে)
    logo_map = load_logos()
    print(f"✅ Loaded {len(logo_map)} logos (Case Insensitive Mode)")

    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
    
    # my_channels.txt রিড করা
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
                    
    except FileNotFoundError:
        print("Error: 'my_channels.txt' not found!")
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
                            # সোর্স থেকে পাওয়া নামও ছোট হাতের করা হচ্ছে
                            cur_nm = name_raw.strip().lower()
                            final_tgt = None
                            
                            # রুলস চেকিং
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
                                    # === লোগো বসানোর অংশ ===
                                    mod_line = re.sub(r'group-title="[^"]*"', f'group-title="{final_tgt}"', line)
                                    
                                    # এখন cur_nm (ছোট হাতের) দিয়ে logo_map (ছোট হাতের) চেক করা হচ্ছে
                                    if cur_nm in logo_map:
                                        logo_url = logo_map[cur_nm]
                                        # যদি আগে লোগো থাকে সেটা রিপ্লেস করবে, না থাকলে যোগ করবে
                                        if 'tvg-logo="' in mod_line:
                                            mod_line = re.sub(r'tvg-logo="[^"]*"', f'tvg-logo="{logo_url}"', mod_line)
                                        else:
                                            mod_line = mod_line.replace("#EXTINF:-1", f'#EXTINF:-1 tvg-logo="{logo_url}"')
                                    
                                    all_channels.append({"group": final_tgt, "content": mod_line + "\n" + link_line + "\n"})
                                    added_ids.add((final_tgt, cur_nm))
        except Exception as e: print(f"Error {tag}: {e}")

    all_channels.sort(key=lambda x: group_priority.index(x["group"]) if x["group"] in group_priority else 999)

    with open("my_playlist.m3u", "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for ch in all_channels: f.write(ch["content"])
    
    print(f"Done! Channels: {len(all_channels)}")

if __name__ == "__main__":
    generate_playlist()
