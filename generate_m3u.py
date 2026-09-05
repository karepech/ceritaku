import requests
import json
import os
import re

# === KONFIGURASI NAMA FILE OUTPUT ===
API_URL = "https://boti.my.id/index.php?api=playlist&email=mbkidriss9%40gmail.com&password=12345678"
OUTPUT_SERIES = "all_series.m3u"
OUTPUT_MOVIES = "movies.m3u"
OUTPUT_LIVE = "live_upcoming.m3u"

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
            print("Mendeteksi format M3U langsung. Memulai pemisahan kategori...")
            lines = content.splitlines()
            
            series_lines = ["#EXTM3U"]
            movies_lines = ["#EXTM3U"]
            live_lines = ["#EXTM3U"]
            
            series_count = 0
            movies_count = 0
            live_count = 0
            
            current_block = []
            category_target = None # Penanda file tujuan: 'series', 'movie', 'live', atau None
            
            for line in lines[1:]: # Lewati baris pertama (#EXTM3U)
                line_str = line.strip()
                if line_str == "":
                    continue
                    
                if line_str.startswith("#EXTINF"):
                    # Simpan blok channel sebelumnya ke file yang tepat
                    if current_block and category_target:
                        if category_target == "series":
                            series_lines.extend(current_block)
                            series_lines.append("")
                            series_count += 1
                        elif category_target == "movie":
                            movies_lines.extend(current_block)
                            movies_lines.append("")
                            movies_count += 1
                        elif category_target == "live":
                            live_lines.extend(current_block)
                            live_lines.append("")
                            live_count += 1
                    
                    # Mulai blok channel baru
                    current_block = [line_str]
                    category_target = None
                    
                    # Ekstrak tag group-title dengan Regex
                    match = re.search(r'group-title="([^"]+)"', line_str, re.IGNORECASE)
                    if match:
                        group_title = match.group(1).lower()
                        
                        # LOGIKA FILTER KATEGORI:
                        if "series" in group_title:
                            category_target = "series"
                        elif "film" in group_title or "movie" in group_title:
                            category_target = "movie"
                        elif "live" in group_title or "upcoming" in group_title:
                            category_target = "live"
                else:
                    # Tambahkan baris URL atau atribut (KODIPROP, dll) ke blok saat ini
                    if current_block:
                        current_block.append(line_str)
            
            # Masukkan blok channel paling terakhir
            if current_block and category_target:
                if category_target == "series":
                    series_lines.extend(current_block)
                    series_lines.append("")
                    series_count += 1
                elif category_target == "movie":
                    movies_lines.extend(current_block)
                    movies_lines.append("")
                    movies_count += 1
                elif category_target == "live":
                    live_lines.extend(current_block)
                    live_lines.append("")
                    live_count += 1

            # --- SIMPAN KE MASING-MASING FILE ---
            with open(OUTPUT_SERIES, "w", encoding="utf-8") as f:
                f.write("\n".join(series_lines))
            with open(OUTPUT_MOVIES, "w", encoding="utf-8") as f:
                f.write("\n".join(movies_lines))
            with open(OUTPUT_LIVE, "w", encoding="utf-8") as f:
                f.write("\n".join(live_lines))
                
            print("Sukses memproses dan memisahkan file M3U!")
            print(f"- {OUTPUT_SERIES} : {series_count} channel")
            print(f"- {OUTPUT_MOVIES} : {movies_count} channel")
            print(f"- {OUTPUT_LIVE} : {live_count} channel")
            return

        # =================================================================
        # JIKA API MENGEMBALIKAN JSON (Fallback System)
        # =================================================================
        try:
            data = response.json()
            print("Mendeteksi format JSON. Memulai pemisahan kategori...")
            
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
            
            # Siapkan penampung
            series_lines = ["#EXTM3U\n"]
            movies_lines = ["#EXTM3U\n"]
            live_lines = ["#EXTM3U\n"]
            
            c_series = c_movies = c_live = 0
            
            for ch in channels_to_process:
                name = ch.get("name", ch.get("title", ch.get("channel", "Unknown")))
                logo = ch.get("logo", ch.get("image", ""))
                group = ch.get("group", ch.get("category", ch.get("category_name", ch.get("_auto_group", "Vidio"))))
                group_lower = str(group).lower()
                
                # Tentukan kategori
                target_list = None
                if "series" in group_lower:
                    target_list = series_lines
                    c_series += 1
                elif "film" in group_lower or "movie" in group_lower:
                    target_list = movies_lines
                    c_movies += 1
                elif "live" in group_lower or "upcoming" in group_lower:
                    target_list = live_lines
                    c_live += 1
                else:
                    continue # Abaikan jika tidak masuk 3 kategori ini

                stream_url = ch.get("url", ch.get("link", ""))
                
                if not stream_url and "id" in ch:
                    u = ch.get("u", ch.get("_global_u", "mbkidriss9@gmail.com"))
                    x = ch.get("x", ch.get("_global_x", ""))
                    a = ch.get("a", ch.get("_global_a", ""))
                    ch_id = ch['id']
                    
                    hls_url = f"https://boti.my.id/index.m3u8?u={u}&x={x}&a={a}&id={ch_id}&type=hls&api=video"
                    dash_url = f"https://boti.my.id/index.mpd?u={u}&x={x}&a={a}&id={ch_id}&type=dash&api=video"
                    drm_url = f"https://boti.my.id/index.php?u={u}&x={x}&a={a}&id={ch_id}&type=drm&api=video"
                    
                    # Generate tag
                    block = f'#EXTINF:-1 tvg-logo="{logo}" group-title="{group}", {name} (HLS)\n{hls_url}\n'
                    block += f'#EXTINF:-1 tvg-logo="{logo}" group-title="{group}", {name} (DASH)\n'
                    block += '#KODIPROP:inputstream=inputstream.adaptive\n'
                    block += '#KODIPROP:inputstream.adaptive.manifest_type=mpd\n'
                    block += '#KODIPROP:inputstream.adaptive.license_type=com.widevine.alpha\n'
                    block += f'#KODIPROP:inputstream.adaptive.license_key={drm_url}\n{dash_url}\n\n'
                    
                    target_list.append(block)

            # Simpan JSON parsing
            with open(OUTPUT_SERIES, "w", encoding="utf-8") as f:
                f.writelines(series_lines)
            with open(OUTPUT_MOVIES, "w", encoding="utf-8") as f:
                f.writelines(movies_lines)
            with open(OUTPUT_LIVE, "w", encoding="utf-8") as f:
                f.writelines(live_lines)
                
            print("Sukses memproses dan memisahkan file JSON!")
            print(f"- {OUTPUT_SERIES} : {c_series} channel")
            print(f"- {OUTPUT_MOVIES} : {c_movies} channel")
            print(f"- {OUTPUT_LIVE} : {c_live} channel")
            
        except json.JSONDecodeError:
            print("Error: Output API bukan JSON dan bukan M3U yang valid.")
            
    except requests.exceptions.RequestException as e:
        print(f"Koneksi ke API gagal: {e}")

if __name__ == "__main__":
    generate_playlist()
