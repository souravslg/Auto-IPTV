import requests
import re

# ==========================================
# আপনার সোর্স লিংকগুলো নিচে বসান
# ==========================================
source_urls = [
    "https://raw.githubusercontent.com/Aftab071/AftabIPTV/refs/heads/main/SyncIT",
    "https://raw.githubusercontent.com/sm-monirulislam/SM-Live-TV/refs/heads/main/Combined_Live_TV.m3u",
    "https://raw.githubusercontent.com/DrSujonPaul/Sujon/refs/heads/main/iptv"
    "https://sonamul4545.vercel.app/siyam3535.m3u"

]
# ==========================================

def generate_playlist():
    specific_map = {}
    wildcard_map = {}
    
    # my_channels.txt ফাইল পড়া
    try:
        with open("my_channels.txt", "r", encoding="utf-8") as file:
            for line in file:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                
                parts = line.split("|")
                if len(parts) == 3:
                    src_group = parts[0].strip().lower()
                    src_name = parts[1].strip().lower()
                    target_group = parts[2].strip()

                    if src_name == "*":
                        wildcard_map[src_group] = target_group
                    else:
                        specific_map[(src_group, src_name)] = target_group
                    
    except FileNotFoundError:
        print("Error: 'my_channels.txt' file not found!")
        return

    print(f"Tracking {len(specific_map)} specific channels and {len(wildcard_map)} dynamic groups.")

    final_playlist = "#EXTM3U\n"
    found_channels = set()

    # সোর্স থেকে খোঁজা
    for url in source_urls:
        try:
            print(f"Scanning: {url}")
            response = requests.get(url)
            if response.status_code == 200:
                lines = response.text.split('\n')
                
                for i in range(len(lines)):
                    line = lines[i].strip()
                    
                    if line.startswith("#EXTINF"):
                        group_match = re.search(r'group-title="([^"]*)"', line)
                        name_raw = line.split(',')[-1].strip()
                        
                        if group_match and name_raw:
                            current_group = group_match.group(1).strip().lower()
                            current_name = name_raw.strip().lower()
                            
                            new_target_group = None
                            
                            # চেক: নির্দিষ্ট চ্যানেল নাকি ওয়াইল্ডকার্ড?
                            if (current_group, current_name) in specific_map:
                                new_target_group = specific_map[(current_group, current_name)]
                            elif current_group in wildcard_map:
                                new_target_group = wildcard_map[current_group]
                            
                            if new_target_group:
                                unique_key = (current_group, current_name, new_target_group)
                                
                                if unique_key not in found_channels:
                                    # গ্রুপ নাম পরিবর্তন
                                    modified_line = re.sub(r'group-title="[^"]*"', f'group-title="{new_target_group}"', line)
                                    
                                    final_playlist += modified_line + "\n"
                                    if i + 1 < len(lines) and not lines[i+1].startswith("#"):
                                        final_playlist += lines[i+1].strip() + "\n"
                                        
                                    found_channels.add(unique_key)
                                    
        except Exception as e:
            print(f"Error checking source {url}: {e}")

    # ফাইল সেভ করা
    with open("my_playlist.m3u", "w", encoding="utf-8") as f:
        f.write(final_playlist)
    
    print(f"Success! Updated with {len(found_channels)} channels.")

if __name__ == "__main__":
    generate_playlist()
