import requests
import re

# === KONFIGURASI FILE OUTPUT ===
API_URL = "https://boti.my.id/index.php?api=playlist&email=mbkidriss9%40gmail.com&password=12345678"
OUTPUT_LIVE = "live.m3u"
OUTPUT_UPCOMING = "upcoming.m3u"

# Token Default (Fallback)
DEFAULT_U = "mbkidriss9%40gmail.com"
DEFAULT_X = "644_SrZsWczYRmp5J7Xx"
DEFAULT_A = "eyJhbGciOiJIUzI1NiJ9.eyJkYXRhIjp7InR5cGUiOiJhY2Nlc3NfdG9rZW4iLCJ1aWQiOjIyMjMzNzE5NH0sImV4cCI6MTc4ODY3NzAzOH0.UHImVkHT2jujFUpPlo_vfULpyt1lZArjsLgw-CX7lVc"

def generate_live_playlist():
    print(f"Mengambil data Live & Upcoming...\nURL: {API_URL}")
    
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        response = requests.get(API_URL, headers=headers, timeout=20)
        response.raise_for_status() 
        content = response.text.strip()
        
        if not content.startswith("#EXTM3U"):
            print("Error: Output dari API kosong atau bukan format M3U.")
            return

        live_lines = ["#EXTM3U\n"]
        upcoming_lines = ["#EXTM3U\n"]
        
        c_live = c_upcoming = 0
        
        # --- METODE BARU: MENGUMPULKAN BLOK DENGAN AMAN ---
        lines = content.splitlines()
        blocks = []
        curr_block = []
        
        for line in lines[1:]:
            line = line.strip()
            if not line: continue
            
            if line.startswith("#EXTINF"):
                if curr_block:
                    blocks.append("\n".join(curr_block))
                curr_block = [line]
            else:
                if curr_block:
                    curr_block.append(line)
        if curr_block:
            blocks.append("\n".join(curr_block))
            
        # --- MEMPROSES SETIAP BLOK ---
        for block in blocks:
            m_group = re.search(r'group-title="([^"]+)"', block, re.IGNORECASE)
            group = m_group.group(1).strip() if m_group else "Uncategorized"
            group_lower = group.lower()
            
            # Hanya proses kategori Live dan Upcoming
            is_upcoming = "upcoming" in group_lower
            is_live = "live" in group_lower or "tv" in group_lower or "nasional" in group_lower
            
            if not is_upcoming and not is_live:
                continue
                
            m_name = re.search(r'#EXTINF.*?,(.*)', block)
            name = m_name.group(1).strip() if m_name else "Unknown"
            
            m_logo = re.search(r'tvg-logo="([^"]+)"', block, re.IGNORECASE)
            logo = m_logo.group(1) if m_logo else ""
            
            m_id = re.search(r'id=(\d+)', block)
            m_u = re.search(r'u=([^&\s\n]+)', block)
            m_x = re.search(r'x=([^&\s\n]+)', block)
            m_a = re.search(r'a=([^&\s\n]+)', block)
            
            if m_id:
                ch_id = m_id.group(1)
                u = m_u.group(1) if m_u else DEFAULT_U
                x = m_x.group(1) if m_x else DEFAULT_X
                a = m_a.group(1) if m_a else DEFAULT_A
                
                hls_url = f"https://boti.my.id/index.m3u8?u={u}&x={x}&a={a}&id={ch_id}&type=hls&api=video"
                dash_url = f"https://boti.my.id/index.mpd?u={u}&x={x}&a={a}&id={ch_id}&type=dash&api=video"
                drm_url = f"https://boti.my.id/index.php?u={u}&x={x}&a={a}&id={ch_id}&type=drm&api=video"
                
                output_block = f'#EXTINF:-1 tvg-logo="{logo}" group-title="{group}", {name} (HLS)\n{hls_url}\n'
                output_block += f'#EXTINF:-1 tvg-logo="{logo}" group-title="{group}", {name} (DASH)\n'
                output_block += '#KODIPROP:inputstream=inputstream.adaptive\n'
                output_block += '#KODIPROP:inputstream.adaptive.manifest_type=mpd\n'
                output_block += '#KODIPROP:inputstream.adaptive.license_type=com.widevine.alpha\n'
                output_block += f'#KODIPROP:inputstream.adaptive.license_key={drm_url}\n{dash_url}\n\n'
                
                # Distribusi ke File
                if is_upcoming:
                    upcoming_lines.append(output_block)
                    c_upcoming += 1
                elif is_live:
                    live_lines.append(output_block)
                    c_live += 1
                    
        # Simpan file
        with open(OUTPUT_LIVE, "w", encoding="utf-8") as f: f.writelines(live_lines)
        with open(OUTPUT_UPCOMING, "w", encoding="utf-8") as f: f.writelines(upcoming_lines)
            
        print(f"Sukses! Live: {c_live} | Upcoming: {c_upcoming}")
        
    except Exception as e:
        print(f"Terjadi kesalahan: {e}")

if __name__ == "__main__":
    generate_live_playlist()
