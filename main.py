import requests
import re

# আপনার সন্দেহভাজন লিংকটি (আমি বানান ঠিক করে দিয়েছি)
url = "https://raw.githubusercontent.com/DrSujonPaul/Sujon/refs/heads/main/iptv"

def doctor_check():
    print(f"Checking URL: {url}")
    print("-" * 40)
    
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
        response = requests.get(url, headers=headers, timeout=15)
        
        # ১. লিংক কাজ করছে কিনা?
        print(f"Status Code: {response.status_code}")
        if response.status_code != 200:
            print("❌ লিংক কাজ করছে না (Link Dead or Blocked)!")
            return

        print("✅ লিংক কানেক্ট হয়েছে!")
        content = response.text
        lines = content.split('\n')
        print(f"Total Lines Found: {len(lines)}")
        
        # ২. লিংকে আসলে কী গ্রুপ আছে?
        print("-" * 40)
        print("এই লিংকে পাওয়া গ্রুপগুলোর নাম নিচে দেওয়া হলো:")
        
        found_groups = set()
        count = 0
        
        for line in lines:
            if 'group-title="' in line:
                match = re.search(r'group-title="([^"]*)"', line)
                if match:
                    group_name = match.group(1)
                    if group_name not in found_groups:
                        print(f"👉 Found Group: '{group_name}'")
                        found_groups.add(group_name)
                        count += 1
                        if count >= 10: # প্রথম ১০টি গ্রুপ দেখাব
                            break
        
        if count == 0:
            print("⚠️ কোনো গ্রুপ খুঁজে পাওয়া যায়নি! লিংকের ফরম্যাট হয়তো ভিন্ন।")
            print("First 5 lines of content:")
            print(content[:500])
            
        print("-" * 40)
        
    except Exception as e:
        print(f"❌ মারাত্মক এরর: {e}")

if __name__ == "__main__":
    doctor_check()
