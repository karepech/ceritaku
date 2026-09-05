import requests
import re

# === KONFIGURASI 4 FILE OUTPUT ===
API_URL = "https://boti.my.id/index.php?api=playlist&email=mbkidriss9%40gmail.com&password=12345678"
OUTPUT_ALL = "playlist-vidio.m3u"      # File Master (Semua ada)
OUTPUT_SERIES = "all_series.m3u"       # Khusus Series (Limit 100 Judul)
OUTPUT_MOVIES = "movies.m3u"           # Khusus Film
OUTPUT_LIVE = "live_upcoming.m3u"      # Khusus Live & Upcoming

MAX_SERIES = 100 # Batas maksimal Judul Series Unik

# Token Default (Fallback jika API tiba-tiba kehilangan token)
DEFAULT_U = "mbkidriss9%40gmail.com"
DEFAULT_X = "644_SrZsWczYRmp5J7Xx"
DEFAULT_A = "eyJhbGciOiJIUzI1NiJ9.eyJkYXRhIjp7InR5cGUiOiJhY2Nlc3NfdG9rZW4iLCJ1aWQiOjIyMjMzNzE5NH0sImV4cCI6MTc4ODY3NzAzOH0.UHImVkHT2jujFUpPlo_vfULpyt1lZArjsLgw-CX7lVc"

def generate_playlist():
    print(f"Mengambil data API...\nURL: {API_URL}")
    
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            # Header JSON dihapus agar API tidak merespons kosong!
        }
        
        response = requests.get(API_URL, headers=headers, timeout=20)
        response.raise_for_status() 
        content = response.text.strip()
        
        if not content.startswith("#EXTM3U"):
            print("Error: Output dari API bukan M3U yang valid.")
            return

        print("Data M3U diterima! Membedah blok channel untuk mengatasi URL terpotong...")
        
        all_lines = ["#EXTM3U\n"]
        series_lines = ["#EXTM3U\n"]
        movies_lines = ["#EXTM3U\n"]
        live_lines = ["#EXTM3U\n"]
        
        count_all = count_series = count_movies = count_live = 0
        seen_series = set()
        
        # MEMOTONG DATA PER CHANNEL (#EXTINF)
        # Ini mengabaikan baris baru/enter yang bikin rusak
        blocks = content.split("#EXTINF")
        
        for block in blocks[1:]: # Skip bagian pertama karena itu cuma header #EXTM3U
            # 1. Ekstrak Info Channel
            m_name = re.search(r',([^\n]+)', block)
            name = m_name.group(1).strip() if m_name else "Unknown"
            
            m_group = re.search(r'group-title="([^"]+)"', block, re.IGNORECASE)
            group = m_group.group(1).strip() if m_group else "Uncategorized"
            group_lower = group.lower()
            
            m_logo = re.search(r'tvg-logo="([^"]+)"', block, re.IGNORECASE)
            logo = m_logo.group(1) if m_logo else ""
            
            # 2. Ekstrak Parameter Autentikasi (Mengambil dari blok secara paksa meskipun terpotong spasi/enter)
            m_id = re.search(r'id=(\d+)', block)
            m_u = re.search(r'u=([^&\s\n]+)', block)
            m_x = re.search(r'x=([^&\s\n]+)', block)
            m_a = re.search(r'a=([^&\s\n]+)', block)
            
            if m_id:
                ch_id = m_id.group(1)
                u = m_u.group(1) if m_u else DEFAULT_U
                x = m_x.group(1) if m_x else DEFAULT_X
                a = m_a.group(1) if m_a else DEFAULT_A
                
                # 3. Rakit ulang URL menjadi sempurna
                hls_url = f"https://boti.my.id/index.m3u8?u={u}&x={x}&a={a}&id={ch_id}&type=hls&api=video"
                dash_url = f"https://boti.my.id/index.mpd?u={u}&x={x}&a={a}&id={ch_id}&type=dash&api=video"
                drm_url = f"https://boti.my.id/index.php?u={u}&x={x}&a={a}&id={ch_id}&type=drm&api=video"
                
                # 4. Susun format akhir
                output_block = f'#EXTINF:-1 tvg-logo="{logo}" group-title="{group}", {name} (HLS)\n{hls_url}\n'
                output_block += f'#EXTINF:-1 tvg-logo="{logo}" group-title="{group}", {name} (DASH)\n'
                output_block += '#KODIPROP:inputstream=inputstream.adaptive\n'
                output_block += '#KODIPROP:inputstream.adaptive.manifest_type=mpd\n'
                output_block += '#KODIPROP:inputstream.adaptive.license_type=com.widevine.alpha\n'
                output_block += f'#KODIPROP:inputstream.adaptive.license_key={drm_url}\n{dash_url}\n\n'
                
                # === PEMBAGIAN FILE ===
                # Masuk ke Master
                all_lines.append(output_block)
                count_all += 1
                
                # Filter ke Kategori
                if "series" in group_lower:
                    if group in seen_series:
                        series_lines.append(output_block)
                        count_series += 1
                    elif len(seen_series) < MAX_SERIES:
                        seen_series.add(group)
                        series_lines.append(output_block)
                        count_series += 1
                elif "film" in group_lower or "movie" in group_lower:
                    movies_lines.append(output_block)
                    count_movies += 1
                elif "live" in group_lower or "tv" in group_lower or "nasional" in group_lower or "upcoming" in group_lower:
                    live_lines.append(output_block)
                    count_live += 1
                    
        # Simpan semua ke 4 file
        with open(OUTPUT_ALL, "w", encoding="utf-8") as f:
            f.writelines(all_lines)
        with open(OUTPUT_SERIES, "w", encoding="utf-8") as f:
            f.writelines(series_lines)
        with open(OUTPUT_MOVIES, "w", encoding="utf-8") as f:
            f.writelines(movies_lines)
        with open(OUTPUT_LIVE, "w", encoding="utf-8") as f:
            f.writelines(live_lines)
            
        print("Selesai! File berhasil dibuat dengan metode bedah blok.")
        print(f"Master: {count_all} | Series: {count_series} | Movie: {count_movies} | Live: {count_live}")
        
    except Exception as e:
        print(f"Terjadi kesalahan saat memproses: {e}")

if __name__ == "__main__":
    generate_playlist()
