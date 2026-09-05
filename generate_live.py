import requests
import json
import re

# === KONFIGURASI ===
API_URL = "https://boti.my.id/index.php?api=playlist&email=mbkidriss9%40gmail.com&password=12345678"
OUTPUT_FILE = "live_only.m3u"

# Token cadangan (Fallback) sesuai contoh dari Anda jika seandainya API tidak menampilkannya
DEFAULT_U = "mbkidriss9%40gmail.com"
DEFAULT_X = "644_SrZsWczYRmp5J7Xx"
DEFAULT_A = "eyJhbGciOiJIUzI1NiJ9.eyJkYXRhIjp7InR5cGUiOiJhY2Nlc3NfdG9rZW4iLCJ1aWQiOjIyMjMzNzE5NH0sImV4cCI6MTc4ODY3NzAzOH0.UHImVkHT2jujFUpPlo_vfULpyt1lZArjsLgw-CX7lVc"

def generate_live_playlist():
    print(f"Mengambil data API Khusus LIVE...\nURL: {API_URL}")
    
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        response = requests.get(API_URL, headers=headers, timeout=15)
        response.raise_for_status() 
        content = response.text.strip()
        
        out_lines = ["#EXTM3U\n"]
        count = 0
        
        # =================================================================
        # SKENARIO 1: API MENGEMBALIKAN M3U LANGSUNG
        # Kita bedah barisnya, ambil ID-nya, lalu rakit ulang HLS & DASH-nya
        # =================================================================
        if content.startswith("#EXTM3U"):
            print("Mendeteksi format M3U mentah. Membedah & merakit ulang link Live...")
            lines = content.splitlines()
            
            current_logo = ""
            current_group = ""
            current_name = ""
            is_live = False
            
            for line in lines:
                line = line.strip()
                if not line: continue
                
                # Menangkap informasi channel
                if line.startswith("#EXTINF"):
                    current_logo = ""
                    current_group = "Uncategorized"
                    current_name = "Unknown"
                    is_live = False
                    
                    m_logo = re.search(r'tvg-logo="([^"]+)"', line, re.IGNORECASE)
                    if m_logo: current_logo = m_logo.group(1)
                    
                    m_group = re.search(r'group-title="([^"]+)"', line, re.IGNORECASE)
                    if m_group: current_group = m_group.group(1).strip()
                    
                    m_name = re.search(r',\s*(.+)$', line)
                    if m_name: current_name = m_name.group(1).strip()
                    
                    group_lower = current_group.lower()
                    # Filter khusus Live / TV
                    if "live" in group_lower or "tv" in group_lower or "nasional" in group_lower or "upcoming" in group_lower:
                        is_live = True
                        
                # Menangkap URL, mengambil parameter, dan merakit ulang
                elif line.startswith("http") and is_live:
                    # Coba ambil ID dan Token dari URL bawaan API
                    m_id = re.search(r'id=(\d+)', line)
                    m_u = re.search(r'u=([^&]+)', line)
                    m_x = re.search(r'x=([^&]+)', line)
                    m_a = re.search(r'a=([^&]+)', line)
                    
                    # Ekstrak atau gunakan fallback dari Anda
                    ch_id = m_id.group(1) if m_id else None
                    u = m_u.group(1) if m_u else DEFAULT_U
                    x = m_x.group(1) if m_x else DEFAULT_X
                    a = m_a.group(1) if m_a else DEFAULT_A
                    
                    if ch_id:
                        # RAKIT URL BARU
                        hls_url = f"https://boti.my.id/index.m3u8?u={u}&x={x}&a={a}&id={ch_id}&type=hls&api=video"
                        dash_url = f"https://boti.my.id/index.mpd?u={u}&x={x}&a={a}&id={ch_id}&type=dash&api=video"
                        drm_url = f"https://boti.my.id/index.php?u={u}&x={x}&a={a}&id={ch_id}&type=drm&api=video"
                        
                        # BUILD BLOK M3U
                        block = f'#EXTINF:-1 tvg-logo="{current_logo}" group-title="{current_group}", {current_name} (HLS)\n{hls_url}\n'
                        block += f'#EXTINF:-1 tvg-logo="{current_logo}" group-title="{current_group}", {current_name} (DASH)\n'
                        block += '#KODIPROP:inputstream=inputstream.adaptive\n'
                        block += '#KODIPROP:inputstream.adaptive.manifest_type=mpd\n'
                        block += '#KODIPROP:inputstream.adaptive.license_type=com.widevine.alpha\n'
                        block += f'#KODIPROP:inputstream.adaptive.license_key={drm_url}\n{dash_url}\n\n'
                        
                        out_lines.append(block)
                        count += 1
                        
                    is_live = False # Reset untuk baris selanjutnya
                    
            with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
                f.writelines(out_lines)
            print(f"Sukses! {count} channel Live berhasil dirakit ulang ke dalam {OUTPUT_FILE}.")
            return

        # =================================================================
        # SKENARIO 2: API MENGEMBALIKAN JSON
        # =================================================================
        try:
            data = response.json()
            print("Mendeteksi format JSON. Memulai proses filter Live...")
            
            channels = []
            if isinstance(data, list):
                for item in data:
                    if "channels" in item and isinstance(item["channels"], list):
                        cat = item.get("category", item.get("group", item.get("name", "Uncategorized")))
                        for ch in item["channels"]:
                            if isinstance(ch, dict):
                                ch["_auto_group"] = cat
                                channels.append(ch)
                    elif isinstance(item, dict):
                        channels.append(item)
            elif isinstance(data, dict):
                for key, value in data.items():
                    if isinstance(value, list):
                        cat = "Vidio" if key.lower() in ["data", "channels", "list"] else key
                        for item in value:
                            if isinstance(item, dict):
                                item["_auto_group"] = cat
                                channels.append(item)
            
            for ch in channels:
                name = ch.get("name", ch.get("title", ch.get("channel", "Unknown")))
                logo = ch.get("logo", ch.get("image", ""))
                group = ch.get("group", ch.get("category", ch.get("category_name", ch.get("_auto_group", "Vidio"))))
                group_lower = str(group).lower()
                
                # Filter khusus Live / TV
                if "live" in group_lower or "tv" in group_lower or "nasional" in group_lower or "upcoming" in group_lower:
                    if "id" in ch:
                        ch_id = ch['id']
                        u = ch.get("u", DEFAULT_U)
                        x = ch.get("x", DEFAULT_X)
                        a = ch.get("a", DEFAULT_A)
                        
                        hls_url = f"https://boti.my.id/index.m3u8?u={u}&x={x}&a={a}&id={ch_id}&type=hls&api=video"
                        dash_url = f"https://boti.my.id/index.mpd?u={u}&x={x}&a={a}&id={ch_id}&type=dash&api=video"
                        drm_url = f"https://boti.my.id/index.php?u={u}&x={x}&a={a}&id={ch_id}&type=drm&api=video"
                        
                        block = f'#EXTINF:-1 tvg-logo="{logo}" group-title="{group}", {name} (HLS)\n{hls_url}\n'
                        block += f'#EXTINF:-1 tvg-logo="{logo}" group-title="{group}", {name} (DASH)\n'
                        block += '#KODIPROP:inputstream=inputstream.adaptive\n'
                        block += '#KODIPROP:inputstream.adaptive.manifest_type=mpd\n'
                        block += '#KODIPROP:inputstream.adaptive.license_type=com.widevine.alpha\n'
                        block += f'#KODIPROP:inputstream.adaptive.license_key={drm_url}\n{dash_url}\n\n'
                        
                        out_lines.append(block)
                        count += 1
                        
            with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
                f.writelines(out_lines)
            print(f"Sukses! {count} channel Live berhasil di-generate dari JSON.")
            
        except json.JSONDecodeError:
            print("Error: Output API bukan JSON dan bukan M3U yang valid.")
            
    except requests.exceptions.RequestException as e:
        print(f"Koneksi ke API gagal: {e}")

if __name__ == "__main__":
    generate_live_playlist()
