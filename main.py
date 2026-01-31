import requests
import re

# ==========================================
# সোর্স লিংক এবং তাদের নাম (Tag)
# ==========================================
sources = [
    {"tag": "link1", "url": "https://raw.githubusercontent.com/Aftab071/AftabIPTV/refs/heads/main/SyncIT"},
    {"tag": "link2", "url": "https://raw.githubusercontent.com/sm-monirulislam/SM-Live-TV/refs/heads/main/Combined_Live_TV.m3u"},
    {"tag": "link3", "url": "https://raw.githubusercontent.com/DrSujonPaul/Sujon/refs/heads/main/iptv"},
    {"tag": "link4", "url": "https://sonamul4545.vercel.app/siyam3535.m3u"}
]
# ==========================================

group_priority = [
    "Live Event",
    "Bangla",
    "Sports",
    "India",
    "Hindi",
    "Others"
]

def generate_playlist():
    # রুলস স্টোর করার জায়গা
    # format: (source_tag, src_group, src_name) -> target_group
    specific_rules = {} 
    
    # format: (source_tag, src_group) -> target_group (Wildcards)
    wildcard_rules = []

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    # ১. my_channels.txt ফাইল পড়া
    try:
        with open("my_channels.txt", "r", encoding="utf-8") as file:
            for line in file:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                
                parts = [p.strip() for p in line.split("|")]
                
                # যদি ৩টা অংশ থাকে, তাহলে ধরে নেব সব সোর্স (*)
                if len(parts) == 3:
                    tag = "*"
                    src_group = parts[0]
                    src_name = parts[1].lower()
                    target_group = parts[2]
                # যদি ৪টা অংশ থাকে, তাহলে নির্দিষ্ট সোর্স
                elif len(parts) == 4:
                    tag = parts[0].lower() # link1, link2 etc.
                    src_group = parts[1]
                    src_name = parts[2].lower()
                    target_group = parts[3]
                else:
                    continue

                if src_name == "*":
                    wildcard_rules.append({"tag": tag, "src_group": src_group, "target": target_group})
                else:
                    specific_rules[(tag, src_group, src_name)] = target_group
                    
    except FileNotFoundError:
        print("Error: 'my_channels.txt' file not found!")
        return

    print(f"Rules Loaded: {len(specific_rules)} specific, {len(wildcard_rules)} wildcards.")

    all_channels = []
    # আমরা এখানে চ্যানেল নাম মনে রাখব যাতে ডুপ্লিকেট না হয়
    added_channel_names = set() 
    found_links = set()

    # ২. সোর্স থেকে খোঁজা
    for source in sources:
        current_tag = source["tag"]
        url = source["url"]
        
        try:
            print(f"Scanning [{current_tag}]: {url}")
            response = requests.get(url, headers=headers, timeout=20)
            if response.status_code == 200:
                lines = response.text.split('\n')
                
                for i in range(len(lines)):
                    line = lines[i].strip()
                    
                    if line.startswith("#EXTINF"):
                        group_match = re.search(r'group-title="([^"]*)"', line)
                        name_raw = line.split(',')[-1].strip()
                        
                        if group_match:
                            current_group = group_match.group(1).strip()
                            current_name = name_raw.strip().lower()
                            
                            final_target = None
                            
                            # === রুলস চেকিং ===
                            
                            # ১. একদম নির্দিষ্ট রুল আছে কিনা? (Link + Group + Name)
                            # উদাহরণ: link1 এর Jamuna TV
                            if (current_tag, current_group, current_name) in specific_rules:
                                final_target = specific_rules[(current_tag, current_group, current_name)]
                            
                            # ২. যদি নির্দিষ্ট রুল না থাকে, তাহলে গ্লোবাল রুল আছে কিনা? (* + Group + Name)
                            # উদাহরণ: * এর Jamuna TV
                            elif ("*", current_group, current_name) in specific_rules:
                                final_target = specific_rules[("*", current_group, current_name)]
                                
                            # ৩. ওয়াইল্ডকার্ড রুল (Link + Group + *)
                            else:
                                for rule in wildcard_rules:
                                    # ট্যাগ মিলতে হবে (অথবা * হতে হবে) AND গ্রুপ নামের অংশ মিলতে হবে
                                    if (rule["tag"] == current_tag or rule["tag"] == "*") and \
                                       (rule["src_group"].lower() in current_group.lower()):
                                        final_target = rule["target"]
                                        break
                            
                            if final_target:
                                # লিংক বের করা
                                link_line = ""
                                if i + 1 < len(lines) and not lines[i+1].startswith("#"):
                                    link_line = lines[i+1].strip()
                                
                                if link_line:
                                    # ডুপ্লিকেট চেকিং:
                                    # যদি আমরা স্পেসিফিক রুল দিয়ে চ্যানেলটি নিই, তাহলে সেটা নেবই।
                                    # কিন্তু যদি ওয়াইল্ডকার্ড দিয়ে আসে এবং এই নামের চ্যানেল অলরেডি নেওয়া হয়ে থাকে, তাহলে বাদ দেব।
                                    
                                    unique_id = (final_target, current_name)
                                    
                                    # যদি স্পেসিফিক লিংকের রুল হয়, তাহলে অগ্রাধিকার পাবে
                                    is_specific_request = (current_tag, current_group, current_name) in specific_rules
                                    
                                    if is_specific_request or unique_id not in added_channel_names:
                                        modified_line = re.sub(r'group-title="[^"]*"', f'group-title="{final_target}"', line)
                                        
                                        all_channels.append({
                                            "group": final_target,
                                            "content": modified_line + "\n" + link_line + "\n"
                                        })
                                        
                                        # তালিকায় যোগ করলাম যাতে পরে অন্য লিংক থেকে একই চ্যানেল ডুপ্লিকেট না হয়
                                        added_channel_names.add(unique_id)
                                    
        except Exception as e:
            print(f"Error checking {current_tag}: {e}")

    # ৩. সাজানো
    def sort_key(channel):
        grp = channel["group"]
        if grp in group_priority:
            return group_priority.index(grp)
        return 999 

    all_channels.sort(key=sort_key)

    with open("my_playlist.m3u", "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for ch in all_channels:
            f.write(ch["content"])
    
    print(f"Success! Total channels: {len(all_channels)}")

if __name__ == "__main__":
    generate_playlist()
