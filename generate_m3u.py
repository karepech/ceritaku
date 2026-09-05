import requests
import re

# === KONFIGURASI FILE OUTPUT ===
API_URL = "https://boti.my.id/index.php?api=playlist&email=mbkidriss9%40gmail.com&password=12345678"
OUTPUT_ALL_SERIES = "all_series.m3u"
OUTPUT_SERIES_100 = "series_100.m3u"
OUTPUT_MOVIES = "movies.m3u"

MAX_SERIES = 100 
DEFAULT_U = "mbkidriss9%40gmail.com"
DEFAULT_X = "644_SrZsWczYRmp5J7Xx"
DEFAULT_A = "eyJhbGciOiJIUzI1NiJ9.eyJkYXRhIjp7InR5cGUiOiJhY2Nlc3NfdG9rZW4iLCJ1aWQiOjIyMjMzNzE5NH0sImV4cCI6MTc4ODY3NzAzOH0.UHImVkHT2jujFUpPlo_vfULpyt1lZArjsLgw-CX7lVc"

def generate_playlist():
    print(f"Mengambil data Series & Movies...\nURL: {API_URL}")
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)", "Accept": "*/*"}
        response = requests.get(API_URL, headers=headers, timeout=20)
        content = response.text.strip()
        
        if not content.startswith("#EXTM3U"):
            print("API tidak merespons dengan format M3U.")
            return

        all_series_lines = ["#EXTM3U\n"]
        series_100_lines = ["#EXTM3U\n"]
        movies_lines = ["#EXTM3U\n"]
        
        seen_series = set()
        c_all_series = c_series_100 = c_movies = 0
        
        # MENGUMPULKAN RAW BLOCKS
        lines = content.splitlines()
        blocks = []
        curr_block = []
        for line in lines[1:]:
            line = line.strip()
            if not line: continue
            if line.startswith("#EXTINF"):
                if curr_block: blocks.append(curr_block)
                curr_block = [line]
            elif curr_block:
                curr_block.append(line)
        if curr_block: blocks.append(curr_block)
            
        for block_lines in blocks:
            extinf = block_lines[0]
            full_text = "\n".join(block_lines)
            
            m_group = re.search(r'group-title=["\']?([^"\',]+)["\']?', extinf, re.IGNORECASE)
            group = m_group.group(1).strip() if m_group else "Uncategorized"
            group_lower = group.lower()
            
            # Abaikan Live/Upcoming
            if any(x in group_lower for x in ["live", "tv", "nasional", "sport", "upcoming", "mendatang"]):
                continue
                
            m_id = re.search(r'id=(\d+)', full_text)
            output_blocks = []
            
            # Mempertahankan raw block format tanpa memodifikasi judul channel
            other_tags = [l for l in block_lines[1:] if l.startswith("#")]
            
            if m_id:
                ch_id = m_id.group(1)
                m_u = re.search(r'u=([^&\s\n]+)', full_text)
                m_x = re.search(r'x=([^&\s\n]+)', full_text)
                m_a = re.search(r'a=([^&\s\n]+)', full_text)
                
                u = m_u.group(1) if m_u else DEFAULT_U
                x = m_x.group(1) if m_x else DEFAULT_X
                a = m_a.group(1) if m_a else DEFAULT_A
                
                hls_url = f"https://boti.my.id/index.m3u8?u={u}&x={x}&a={a}&id={ch_id}&type=hls&api=video"
                dash_url = f"https://boti.my.id/index.mpd?u={u}&x={x}&a={a}&id={ch_id}&type=dash&api=video"
                drm_url = f"https://boti.my.id/index.php?u={u}&x={x}&a={a}&id={ch_id}&type=drm&api=video"
                
                # Varian HLS
                hls_block = [extinf] + other_tags + [hls_url]
                output_blocks.append("\n".join(hls_block) + "\n")
                
                # Varian DASH (KodiProp)
                dash_block = [extinf] + other_tags + [
                    "#KODIPROP:inputstream=inputstream.adaptive",
                    "#KODIPROP:inputstream.adaptive.manifest_type=mpd",
                    "#KODIPROP:inputstream.adaptive.license_type=com.widevine.alpha",
                    f"#KODIPROP:inputstream.adaptive.license_key={drm_url}",
                    dash_url
                ]
                output_blocks.append("\n".join(dash_block) + "\n")
            else:
                # Jika tidak ada ID, tulis raw block secara utuh agar tayangan tidak hilang
                output_blocks.append(full_text + "\n\n")

            # DISTRIBUSI KATEGORI
            if any(x in group_lower for x in ["series", "sinetron", "drama", "episode"]):
                for b in output_blocks:
                    all_series_lines.append(b)
                c_all_series += 1
                
                if group in seen_series:
                    for b in output_blocks: series_100_lines.append(b)
                    c_series_100 += 1
                elif len(seen_series) < MAX_SERIES:
                    seen_series.add(group)
                    for b in output_blocks: series_100_lines.append(b)
                    c_series_100 += 1
                    
            elif any(x in group_lower for x in ["film", "movie", "bioskop"]):
                for b in output_blocks:
                    movies_lines.append(b)
                c_movies += 1
                
        with open(OUTPUT_ALL_SERIES, "w", encoding="utf-8") as f: f.writelines(all_series_lines)
        with open(OUTPUT_SERIES_100, "w", encoding="utf-8") as f: f.writelines(series_100_lines)
        with open(OUTPUT_MOVIES, "w", encoding="utf-8") as f: f.writelines(movies_lines)
        print(f"Sukses! All Series: {c_all_series} | Series 100: {c_series_100} | Movies: {c_movies}")
        
    except Exception as e:
        print(f"Kesalahan: {e}")

if __name__ == "__main__":
    generate_playlist()
