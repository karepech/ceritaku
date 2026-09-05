import requests
import re

# === KONFIGURASI FILE OUTPUT ===
API_URL = "https://boti.my.id/index.php?api=playlist&email=mbkidriss9%40gmail.com&password=12345678"
OUTPUT_ALL_SERIES = "all_series.m3u"
OUTPUT_SERIES_100 = "series_100.m3u"
OUTPUT_MOVIES = "movies.m3u"

MAX_SERIES = 100 # Batas judul untuk series_100.m3u

# Token Default (Fallback)
DEFAULT_U = "mbkidriss9%40gmail.com"
DEFAULT_X = "644_SrZsWczYRmp5J7Xx"
DEFAULT_A = "eyJhbGciOiJIUzI1NiJ9.eyJkYXRhIjp7InR5cGUiOiJhY2Nlc3NfdG9rZW4iLCJ1aWQiOjIyMjMzNzE5NH0sImV4cCI6MTc4ODY3NzAzOH0.UHImVkHT2jujFUpPlo_vfULpyt1lZArjsLgw-CX7lVc"

def generate_playlist():
    print(f"Mengambil data Series & Movies...\nURL: {API_URL}")
    
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        response = requests.get(API_URL, headers=headers, timeout=20)
        response.raise_for_status() 
        content = response.text.strip()
        
        if not content.startswith("#EXTM3U"):
            print("Error: Output dari API kosong atau bukan format M3U.")
            return

        all_series_lines = ["#EXTM3U\n"]
        series_100_lines = ["#EXTM3U\n"]
        movies_lines = ["#EXTM3U\n"]
        
        c_all_series = c_series_100 = c_movies = 0
        seen_series = set()
        
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
            # 1. Ekstrak Info Channel
            m_group = re.search(r'group-title="([^"]+)"', block, re.IGNORECASE)
            group = m_group.group(1).strip() if m_group else "Uncategorized"
            group_lower = group.lower()
            
            # Abaikan Live & Upcoming di script ini
            if "live" in group_lower or "tv" in group_lower or "nasional" in group_lower or "upcoming" in group_lower:
                continue
                
            m_name = re.search(r'#EXTINF.*?,(.*)', block)
            name = m_name.group(1).strip() if m_name else "Unknown"
            
            m_logo = re.search(r'tvg-logo="([^"]+)"', block, re.IGNORECASE)
            logo = m_logo.group(1) if m_logo else ""
            
            # 2. Ekstrak Token
            m_id = re.search(r'id=(\d+)', block)
            m_u = re.search(r'u=([^&\s\n]+)', block)
            m_x = re.search(r'x=([^&\s\n]+)', block)
            m_a = re.search(r'a=([^&\s\n]+)', block)
            
            if m_id:
                ch_id = m_id.group(1)
                u = m_u.group(1) if m_u else DEFAULT_U
                x = m_x.group(1) if m_x else DEFAULT_X
                a = m_a.group(1) if m_a else DEFAULT_A
                
                # 3. Rakit URL
                hls_url = f"https://boti.my.id/index.m3u8?u={u}&x={x}&a={a}&id={ch_id}&type=hls&api=video"
                dash_url = f"https://boti.my.id/index.mpd?u={u}&x={x}&a={a}&id={ch_id}&type=dash&api=video"
                drm_url = f"https://boti.my.id/index.php?u={u}&x={x}&a={a}&id={ch_id}&type=drm&api=video"
                
                output_block = f'#EXTINF:-1 tvg-logo="{logo}" group-title="{group}", {name} (HLS)\n{hls_url}\n'
                output_block += f'#EXTINF:-1 tvg-logo="{logo}" group-title="{group}", {name} (DASH)\n'
                output_block += '#KODIPROP:inputstream=inputstream.adaptive\n'
                output_block += '#KODIPROP:inputstream.adaptive.manifest_type=mpd\n'
                output_block += '#KODIPROP:inputstream.adaptive.license_type=com.widevine.alpha\n'
                output_block += f'#KODIPROP:inputstream.adaptive.license_key={drm_url}\n{dash_url}\n\n'
                
                # 4. Distribusi ke File
                if "series" in group_lower:
                    # Masuk ke All Series
                    all_series_lines.append(output_block)
                    c_all_series += 1
                    
                    # Masuk ke Series 100
                    if group in seen_series:
                        series_100_lines.append(output_block)
                        c_series_100 += 1
                    elif len(seen_series) < MAX_SERIES:
                        seen_series.add(group)
                        series_100_lines.append(output_block)
                        c_series_100 += 1
                        
                elif "film" in group_lower or "movie" in group_lower:
                    movies_lines.append(output_block)
                    c_movies += 1
                    
        # Simpan file
        with open(OUTPUT_ALL_SERIES, "w", encoding="utf-8") as f: f.writelines(all_series_lines)
        with open(OUTPUT_SERIES_100, "w", encoding="utf-8") as f: f.writelines(series_100_lines)
        with open(OUTPUT_MOVIES, "w", encoding="utf-8") as f: f.writelines(movies_lines)
            
        print(f"Sukses! All Series: {c_all_series} | Series 100: {c_series_100} | Movies: {c_movies}")
        
    except Exception as e:
        print(f"Terjadi kesalahan: {e}")

if __name__ == "__main__":
    generate_playlist()
