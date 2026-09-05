import requests
import re
import os

# === KONFIGURASI 2 FILE OUTPUT ===
API_URL = "https://boti.my.id/index.php?api=playlist&email=mbkidriss9%40gmail.com&password=12345678"
OUTPUT_LIVE = "live.m3u"
OUTPUT_UPCOMING = "upcoming.m3u"

FALLBACK_MP4 = "http://127.0.0.1/dummy.mp4"
DEFAULT_U = "mbkidriss9%40gmail.com"
DEFAULT_X = "644_SrZsWczYRmp5J7Xx"
DEFAULT_A = "eyJhbGciOiJIUzI1NiJ9.eyJkYXRhIjp7InR5cGUiOiJhY2Nlc3NfdG9rZW4iLCJ1aWQiOjIyMjMzNzE5NH0sImV4cCI6MTc4ODY3NzAzOH0.UHImVkHT2jujFUpPlo_vfULpyt1lZArjsLgw-CX7lVc"

def process_block(current_block):
    extinf = current_block[0]
    full_text = "\n".join(current_block)
    
    m_group = re.search(r'group-title="([^"]+)"', extinf, re.IGNORECASE)
    group = m_group.group(1).strip() if m_group else "Uncategorized"
    
    m_name = re.search(r',\s*(.+)$', extinf)
    name = m_name.group(1).strip() if m_name else "Unknown"
    
    m_logo = re.search(r'tvg-logo="([^"]*)"', extinf, re.IGNORECASE)
    logo = m_logo.group(1) if m_logo else ""
    
    m_id = re.search(r'id=(\d+)', full_text)
    has_http = "http" in full_text.lower()
    
    # Deteksi Upcoming
    if "upcoming" in group.lower() and not has_http:
        return group, f'{extinf}\n{FALLBACK_MP4}\n'
        
    if m_id:
        ch_id = m_id.group(1)
        m_u = re.search(r'u=([^&\s\n]+)', full_text)
        m_x = re.search(r'x=([^&\s\n]+)', full_text)
        m_a = re.search(r'a=([^&\s\n]+)', full_text)
        
        u = m_u.group(1) if m_u else DEFAULT_U
        x = m_x.group(1) if m_x else DEFAULT_X
        a = m_a.group(1) if m_a else DEFAULT_A
        
        # Link LIVE Persis seperti yang Anda kirim (Tanpa &api=video)
        hls_url = f"https://boti.my.id/index.m3u8?u={u}&x={x}&a={a}&id={ch_id}&type=hls"
        dash_url = f"https://boti.my.id/index.mpd?u={u}&x={x}&a={a}&id={ch_id}&type=dash"
        drm_url = f"https://boti.my.id/index.php?u={u}&x={x}&a={a}&id={ch_id}&type=drm"
        
        out_block = f'#EXTINF:-1 tvg-logo="{logo}" group-title="{group}", {name} (HLS)\n{hls_url}\n'
        out_block += f'#EXTINF:-1 tvg-logo="{logo}" group-title="{group}", {name} (DASH)\n'
        out_block += '#KODIPROP:inputstream=inputstream.adaptive\n'
        out_block += '#KODIPROP:inputstream.adaptive.manifest_type=mpd\n'
        out_block += '#KODIPROP:inputstream.adaptive.license_type=com.widevine.alpha\n'
        out_block += f'#KODIPROP:inputstream.adaptive.license_key={drm_url}\n{dash_url}\n'
        return group, out_block
    else:
        # Kembalikan utuh jika bukan format standar API
        return group, full_text + "\n"

def generate_live_playlist():
    print(f"Mengambil data Live & Upcoming...\nURL: {API_URL}")
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        response = requests.get(API_URL, headers=headers, timeout=15)
        response.raise_for_status() 
        content = response.text.strip()
        
        if content.startswith("#EXTM3U"):
            lines = content.splitlines()
            
            live_lines = ["#EXTM3U"]
            upcoming_lines = ["#EXTM3U"]
            
            current_block = []
            
            for line in lines[1:]: 
                line_str = line.strip()
                if not line_str: continue
                    
                if line_str.startswith("#EXTINF"):
                    if current_block:
                        group, out_block = process_block(current_block)
                        group_lower = group.lower()
                        
                        if "upcoming" in group_lower:
                            upcoming_lines.extend([out_block, ""])
                        elif "live" in group_lower or "tv" in group_lower or "nasional" in group_lower:
                            live_lines.extend([out_block, ""])
                            
                    current_block = [line_str]
                else:
                    if current_block:
                        current_block.append(line_str)
            
            # Blok terakhir
            if current_block:
                group, out_block = process_block(current_block)
                group_lower = group.lower()
                if "upcoming" in group_lower:
                    upcoming_lines.extend([out_block, ""])
                elif "live" in group_lower or "tv" in group_lower or "nasional" in group_lower:
                    live_lines.extend([out_block, ""])

            with open(OUTPUT_LIVE, "w", encoding="utf-8") as f: f.write("\n".join(live_lines))
            with open(OUTPUT_UPCOMING, "w", encoding="utf-8") as f: f.write("\n".join(upcoming_lines))
            
            print(f"Sukses generate Live & Upcoming!")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    generate_live_playlist()
