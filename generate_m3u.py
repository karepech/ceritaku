import requests
import json
import os
import re

# === KONFIGURASI 4 FILE OUTPUT ===
API_URL = "https://boti.my.id/index.php?api=playlist&email=mbkidriss9%40gmail.com&password=12345678"
OUTPUT_ALL = "playlist-vidio.m3u"      # File Master (Semua ada)
OUTPUT_SERIES = "all_series.m3u"       # Khusus Series (Limit 100 Judul)
OUTPUT_MOVIES = "movies.m3u"           # Khusus Film
OUTPUT_LIVE = "live_upcoming.m3u"      # Khusus Live & Upcoming

# === BATAS MAKSIMAL JUDUL UNTUK FILE SERIES ===
MAX_SERIES = 100 

def generate_playlist():
    print(f"Mengambil data terbaru dari API...\nURL: {API_URL}")
    
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        response = requests.get(API_URL, headers=headers, timeout=15)
        response.raise_for_status() 
        content = response.text.strip()
        
        # =================================================================
        # JIKA API MENGEMBALIKAN TEKS M3U LANGSUNG (Format Raw Blok)
        # =================================================================
        if content.startswith("#EXTM3U"):
            print("Mendeteksi format M3U langsung. Memulai proses generate 4 file...")
            lines = content.splitlines()
            
            all_lines = ["#EXTM3U"]
            series_lines = ["#EXTM3U"]
            movies_lines = ["#EXTM3U"]
            live_lines = ["#EXTM3U"]
            
            count_all = 0
            count_series = 0
            count_movies = 0
            count_live = 0
            
            current_block = []
            category_target = None
            seen_series = set()
            
            for line in lines[1:]: 
                line_str = line.strip()
                if line_str == "":
                    continue
                    
                if line_str.startswith("#EXTINF"):
                    # === SIMPAN BLOK SEBELUMNYA KE FILE YANG TEPAT ===
                    if current_block:
                        # 1. Selalu masukkan ke File Master (playlist-vidio.m3u)
                        all_lines.extend(current_block)
                        all_lines.append("")
                        count_all += 1
                        
                        # 2. Masukkan ke file pecahan sesuai kategorinya
                        if category_target == "series":
                            series_lines.extend(current_block)
                            series_lines.append("")
                            count_series += 1
                        elif category_target == "movie":
                            movies_lines.extend(current_block)
                            movies_lines.append("")
                            count_movies += 1
                        elif category_target == "live":
                            live_lines.extend(current_block)
                            live_lines.append("")
                            count_live += 1
                    
                    # === MULAI BLOK CHANNEL BARU ===
                    current_block = [line_str]
                    category_target = None
                    
                    match = re.search(r'group-title="([^"]+)"', line_str, re.IGNORECASE)
                    if match:
                        group_title = match.group(1).strip()
                        group_lower = group_title.lower()
                        
                        # LOGIKA FILTER KATEGORI:
                        if "series" in group_lower:
                            if group_title in seen_series:
                                category_target = "series"
                            elif len(seen_series) < MAX_SERIES:
                                seen_series.add(group_title)
                                category_target = "series"
                            # Jika limit 100 judul penuh, category_target tetap None 
                            # (Hanya masuk ke File Master, tidak masuk ke all_series.m3u)
                                
                        elif "film" in group_lower or "movie" in group_lower:
                            category_target = "movie"
                        elif "live" in group_lower or "upcoming" in group_lower:
                            category_target = "live"
                else:
                    if current_block:
                        current_block.append(line_str)
            
            # === EKSEKUSI BLOK TERAKHIR ===
            if current_block:
                all_lines.extend(current_block)
                all_lines.append("")
                count_all += 1
                
                if category_target == "series":
                    series_lines.extend(current_block)
                    series_lines.append("")
                    count_series += 1
                elif category_target == "movie":
                    movies_lines.extend(current_block)
                    movies_lines.append("")
                    count_movies += 1
                elif category_target == "live":
                    live_lines.extend(current_block)
                    live_lines.append("")
                    count_live += 1

            # --- SIMPAN KE 4 FILE ---
            with open(OUTPUT_ALL, "w", encoding="utf-8") as f:
                f.write("\n".join(all_lines))
            with open(OUTPUT_SERIES, "w", encoding="utf-8") as f:
                f.write("\n".join(series_lines))
            with open(OUTPUT_MOVIES, "w", encoding="utf-8") as f:
                f.write("\n".join(movies_lines))
            with open(OUTPUT_LIVE, "w", encoding="utf-8") as f:
                f.write("\n".join(live_lines))
                
            print("Sukses! 4 File M3U berhasil dibuat:")
            print(f"1. {OUTPUT_ALL} : {count_all} tayangan (Master)")
            print(f"2. {OUTPUT_SERIES} : {count_series} episode (dari {len(seen_series)} Judul Series Unik)")
            print(f"3. {OUTPUT_MOVIES} : {count_movies} tayangan")
            print(f"4. {OUTPUT_LIVE} : {count_live} tayangan")
            return

        # =================================================================
        # JIKA API MENGEMBALIKAN JSON (Fallback System)
        # =================================================================
        try:
            data = response.json()
            print("Mendeteksi format JSON. Memulai proses generate 4 file...")
            
            channels_to_process = []
            if isinstance(data, list):
                for item in data:
                    if "channels" in item and isinstance(item["channels"], list):
                        cat_name = item.get("category", item.get("group", item.get("name", "Uncategorized")))
                        for ch in item["channels"]:
                            if isinstance(ch, dict):
                                ch["_auto_group"] = cat_name
                                channels_to_process.append(ch)
                    elif isinstance(item, dict):
                        channels_to_process.append(item)

            elif isinstance(data, dict):
                global_u = data.get("u", "mbkidriss9@gmail.com")
                global_x = data.get("x", "")
                global_a = data.get("a", "")
                
                for key, value in data.items():
                    if isinstance(value, list):
                        cat_name = "Vidio" if key.lower() in ["data", "channels", "list"] else key
                        for item in value:
                            if isinstance(item, dict):
                                item["_auto_group"] = cat_name
                                item["_global_u"] = global_u
                                item["_global_x"] = global_x
                                item["_global_a"] = global_a
                                channels_to_process.append(item)
            
            # Siapkan penampung untuk 4 file
            all_lines = ["#EXTM3U\n"]
            series_lines = ["#EXTM3U\n"]
            movies_lines = ["#EXTM3U\n"]
            live_lines = ["#EXTM3U\n"]
            
            seen_series = set()
            c_all = c_series = c_movies = c_live = 0
            
            for ch in channels_to_process:
                name = ch.get("name", ch.get("title", ch.get("channel", "Unknown")))
                logo = ch.get("logo", ch.get("image", ""))
                group = ch.get("group", ch.get("category", ch.get("category_name", ch.get("_auto_group", "Vidio"))))
                
                group_title_original = str(group).strip()
                group_lower = group_title_original.lower()
                
                stream_url = ch.get("url", ch.get("link", ""))
                if not stream_url and "id" in ch:
                    u = ch.get("u", ch.get("_global_u", "mbkidriss9@gmail.com"))
                    x = ch.get("x", ch.get("_global_x", ""))
                    a = ch.get("a", ch.get("_global_a", ""))
                    ch_id = ch['id']
                    
                    hls_url = f"https://boti.my.id/index.m3u8?u={u}&x={x}&a={a}&id={ch_id}&type=hls&api=video"
                    dash_url = f"https://boti.my.id/index.mpd?u={u}&x={x}&a={a}&id={ch_id}&type=dash&api=video"
                    drm_url = f"https://boti.my.id/index.php?u={u}&x={x}&a={a}&id={ch_id}&type=drm&api=video"
                    
                    # Generate tag blok
                    block = f'#EXTINF:-1 tvg-logo="{logo}" group-title="{group_title_original}", {name} (HLS)\n{hls_url}\n'
                    block += f'#EXTINF:-1 tvg-logo="{logo}" group-title="{group_title_original}", {name} (DASH)\n'
                    block += '#KODIPROP:inputstream=inputstream.adaptive\n'
                    block += '#KODIPROP:inputstream.adaptive.manifest_type=mpd\n'
                    block += '#KODIPROP:inputstream.adaptive.license_type=com.widevine.alpha\n'
                    block += f'#KODIPROP:inputstream.adaptive.license_key={drm_url}\n{dash_url}\n\n'
                    
                    # 1. Selalu tambahkan ke file Master
                    all_lines.append(block)
                    c_all += 1
                    
                    # 2. Tambahkan ke kategori spesifik
                    if "series" in group_lower:
                        if group_title_original in seen_series:
                            series_lines.append(block)
                            c_series += 1
                        elif len(seen_series) < MAX_SERIES:
                            seen_series.add(group_title_original)
                            series_lines.append(block)
                            c_series += 1
                    elif "film" in group_lower or "movie" in group_lower:
                        movies_lines.append(block)
                        c_movies += 1
                    elif "live" in group_lower or "upcoming" in group_lower:
                        live_lines.append(block)
                        c_live += 1

            # --- SIMPAN KE 4 FILE ---
            with open(OUTPUT_ALL, "w", encoding="utf-8") as f:
                f.writelines(all_lines)
            with open(OUTPUT_SERIES, "w", encoding="utf-8") as f:
                f.writelines(series_lines)
            with open(OUTPUT_MOVIES, "w", encoding="utf-8") as f:
                f.writelines(movies_lines)
            with open(OUTPUT_LIVE, "w", encoding="utf-8") as f:
                f.writelines(live_lines)
                
            print("Sukses! 4 File M3U (JSON) berhasil dibuat:")
            print(f"1. {OUTPUT_ALL} : {c_all} tayangan (Master)")
            print(f"2. {OUTPUT_SERIES} : {c_series} episode (dari {len(seen_series)} Judul Series Unik)")
            print(f"3. {OUTPUT_MOVIES} : {c_movies} tayangan")
            print(f"4. {OUTPUT_LIVE} : {c_live} tayangan")
            
        except json.JSONDecodeError:
            print("Error: Output API bukan JSON dan bukan M3U yang valid.")
            
    except requests.exceptions.RequestException as e:
        print(f"Koneksi ke API gagal: {e}")

if __name__ == "__main__":
    generate_playlist()
