import requests
import json
import os
import re

# === KONFIGURASI 3 FILE OUTPUT ===
API_URL = "https://boti.my.id/index.php?api=playlist&email=mbkidriss9%40gmail.com&password=12345678"
OUTPUT_ALL_SERIES = "all_series.m3u"
OUTPUT_SERIES_100 = "series_100.m3u"
OUTPUT_MOVIES = "movies.m3u"
MAX_SERIES = 100 

def generate_playlist():
    print(f"Mengambil data Series & Movies...\nURL: {API_URL}")
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        response = requests.get(API_URL, headers=headers, timeout=15)
        response.raise_for_status() 
        # lstrip('\ufeff') mencegah error pembacaan jika ada karakter tak terlihat (BOM) dari server
        content = response.text.strip().lstrip('\ufeff') 
        
        # =================================================================
        # JIKA M3U LANGSUNG (Format Raw Blok dipertahankan)
        # =================================================================
        if content.startswith("#EXTM3U"):
            print("Mendeteksi format M3U langsung. Memulai proses generate...")
            lines = content.splitlines()
            
            all_series_lines = ["#EXTM3U"]
            series_100_lines = ["#EXTM3U"]
            movies_lines = ["#EXTM3U"]
            
            current_block = []
            category_target = None
            seen_series = set()
            
            for line in lines[1:]: 
                line_str = line.strip()
                if line_str == "": continue
                    
                if line_str.startswith("#EXTINF"):
                    # Simpan blok sebelumnya
                    if current_block and category_target:
                        if category_target == "series":
                            all_series_lines.extend(current_block)
                            all_series_lines.append("")
                            
                            # Ekstrak nama grup untuk limit 100 series
                            group_title = ""
                            m_g = re.search(r'group-title="([^"]+)"', current_block[0], re.IGNORECASE)
                            if m_g: group_title = m_g.group(1).strip()
                            
                            if group_title in seen_series:
                                series_100_lines.extend(current_block)
                                series_100_lines.append("")
                            elif len(seen_series) < MAX_SERIES:
                                seen_series.add(group_title)
                                series_100_lines.extend(current_block)
                                series_100_lines.append("")
                                
                        elif category_target == "movie":
                            movies_lines.extend(current_block)
                            movies_lines.append("")
                    
                    # Mulai blok baru
                    current_block = [line_str]
                    category_target = None
                    
                    match = re.search(r'group-title="([^"]+)"', line_str, re.IGNORECASE)
                    if match:
                        group_lower = match.group(1).lower()
                        if "series" in group_lower: category_target = "series"
                        elif "film" in group_lower or "movie" in group_lower: category_target = "movie"
                else:
                    if current_block: current_block.append(line_str)
            
            # Blok Terakhir
            if current_block and category_target:
                if category_target == "series":
                    all_series_lines.extend(current_block)
                    all_series_lines.append("")
                    group_title = ""
                    m_g = re.search(r'group-title="([^"]+)"', current_block[0], re.IGNORECASE)
                    if m_g: group_title = m_g.group(1).strip()
                    
                    if group_title in seen_series:
                        series_100_lines.extend(current_block)
                        series_100_lines.append("")
                    elif len(seen_series) < MAX_SERIES:
                        seen_series.add(group_title)
                        series_100_lines.extend(current_block)
                        series_100_lines.append("")
                elif category_target == "movie":
                    movies_lines.extend(current_block)
                    movies_lines.append("")

            with open(OUTPUT_ALL_SERIES, "w", encoding="utf-8") as f: f.write("\n".join(all_series_lines))
            with open(OUTPUT_SERIES_100, "w", encoding="utf-8") as f: f.write("\n".join(series_100_lines))
            with open(OUTPUT_MOVIES, "w", encoding="utf-8") as f: f.write("\n".join(movies_lines))
            print("Sukses memproses M3U!")
            return

        # =================================================================
        # JIKA JSON (Fallback System dari kode Anda)
        # =================================================================
        try:
            data = response.json()
            print("Mendeteksi format JSON. Memulai proses generate...")
            channels_to_process = []
            
            if isinstance(data, list):
                for item in data:
                    if "channels" in item and isinstance(item["channels"], list):
                        cat_name = item.get("category", item.get("group", item.get("name", "Uncategorized")))
                        for ch in item["channels"]:
                            if isinstance(ch, dict):
                                ch["_auto_group"] = cat_name
                                channels_to_process.append(ch)
                    elif isinstance(item, dict): channels_to_process.append(item)
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
            
            all_series_lines = ["#EXTM3U\n"]
            series_100_lines = ["#EXTM3U\n"]
            movies_lines = ["#EXTM3U\n"]
            seen_series = set()
            
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
                    
                    block = f'#EXTINF:-1 tvg-logo="{logo}" group-title="{group_title_original}", {name} (HLS)\n{hls_url}\n'
                    block += f'#EXTINF:-1 tvg-logo="{logo}" group-title="{group_title_original}", {name} (DASH)\n'
                    block += '#KODIPROP:inputstream=inputstream.adaptive\n'
                    block += '#KODIPROP:inputstream.adaptive.manifest_type=mpd\n'
                    block += '#KODIPROP:inputstream.adaptive.license_type=com.widevine.alpha\n'
                    block += f'#KODIPROP:inputstream.adaptive.license_key={drm_url}\n{dash_url}\n\n'
                    
                    if "series" in group_lower:
                        all_series_lines.append(block)
                        if group_title_original in seen_series:
                            series_100_lines.append(block)
                        elif len(seen_series) < MAX_SERIES:
                            seen_series.add(group_title_original)
                            series_100_lines.append(block)
                    elif "film" in group_lower or "movie" in group_lower:
                        movies_lines.append(block)

            with open(OUTPUT_ALL_SERIES, "w", encoding="utf-8") as f: f.writelines(all_series_lines)
            with open(OUTPUT_SERIES_100, "w", encoding="utf-8") as f: f.writelines(series_100_lines)
            with open(OUTPUT_MOVIES, "w", encoding="utf-8") as f: f.writelines(movies_lines)
            print("Sukses memproses JSON!")
            
        except json.JSONDecodeError:
            print("Error: Bukan JSON dan bukan M3U.")
            
    except requests.exceptions.RequestException as e:
        print(f"Koneksi gagal: {e}")

if __name__ == "__main__":
    generate_playlist()
