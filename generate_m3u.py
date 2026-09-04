import requests
import json
import os
import re

# === KONFIGURASI ===
API_URL = "https://boti.my.id/index.php?api=playlist&email=mbkidriss9%40gmail.com&password=12345678"
OUTPUT_FILE = "playlist-vidio.m3u"
MAX_SERIES = 100 # Batas maksimal 100 JUDUL BERBEDA

def generate_playlist():
    print(f"Mengambil data terbaru dari API...\nURL: {API_URL}")
    
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        response = requests.get(API_URL, headers=headers, timeout=15)
        response.raise_for_status() 
        content = response.text.strip()
        
        # JIKA API MENGEMBALIKAN TEKS M3U LANGSUNG
        if content.startswith("#EXTM3U"):
            print(f"Mendeteksi format M3U langsung. Mengambil maksimal {MAX_SERIES} judul SERIES unik...")
            lines = content.splitlines()
            
            filtered_lines = ["#EXTM3U"]
            current_block = []
            
            seen_series = set() # Penyimpan daftar judul unik yang sudah diproses
            is_valid_series = False
            total_episodes = 0
            
            for line in lines[1:]: # Lewati baris pertama (#EXTM3U)
                line_str = line.strip()
                if line_str == "":
                    continue
                    
                if line_str.startswith("#EXTINF"):
                    # Jika sebelumnya ada blok channel SERIES, simpan
                    if current_block and is_valid_series:
                        filtered_lines.extend(current_block)
                        filtered_lines.append("") # Jarak antar channel
                        total_episodes += 1
                    
                    # Mulai blok channel baru
                    current_block = [line_str]
                    is_valid_series = False
                    
                    # Cek tag group-title dengan Regex
                    match = re.search(r'group-title="([^"]+)"', line_str, re.IGNORECASE)
                    if match:
                        group_title = match.group(1).strip()
                        
                        # Pastikan itu adalah "series"
                        if "series" in group_title.lower():
                            if group_title in seen_series:
                                # Jika judul sudah ada di daftar, boleh terus masuk (episode berikutnya)
                                is_valid_series = True
                            elif len(seen_series) < MAX_SERIES:
                                # Jika judul belum ada, dan slot 100 judul belum penuh, daftarkan!
                                seen_series.add(group_title)
                                is_valid_series = True
                else:
                    # Tambahkan baris URL atau atribut lain ke blok saat ini
                    if current_block:
                        current_block.append(line_str)
            
            # Masukkan blok channel terakhir yang sedang diproses
            if current_block and is_valid_series:
                filtered_lines.extend(current_block)
                filtered_lines.append("")
                total_episodes += 1

            # Tulis hasil filter ke file
            with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
                f.write("\n".join(filtered_lines))
                
            print(f"Sukses! Tersimpan {total_episodes} episode dari {len(seen_series)} judul SERIES berbeda.")
            return

        # JIKA API MENGEMBALIKAN JSON (Fallback)
        try:
            data = response.json()
            print("Mendeteksi format JSON. Memulai proses filter...")
            
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
            
            seen_series = set()
            total_episodes = 0
            
            with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
                f.write("#EXTM3U\n")
                
                for ch in channels_to_process:
                    name = ch.get("name", ch.get("title", ch.get("channel", "Unknown")))
                    logo = ch.get("logo", ch.get("image", ""))
                    group = ch.get("group", ch.get("category", ch.get("category_name", ch.get("_auto_group", "Vidio"))))
                    group_str = str(group)
                    
                    if "series" not in group_str.lower():
                        continue 

                    # Pengecekan limit Judul Unik
                    if group_str in seen_series:
                        pass # Sudah ada, lanjutkan (episode baru)
                    elif len(seen_series) < MAX_SERIES:
                        seen_series.add(group_str) # Daftarkan judul baru
                    else:
                        continue # Judul baru, tapi batasan 100 judul sudah penuh, abaikan.

                    stream_url = ch.get("url", ch.get("link", ""))
                    
                    if not stream_url and "id" in ch:
                        u = ch.get("u", ch.get("_global_u", "mbkidriss9@gmail.com"))
                        x = ch.get("x", ch.get("_global_x", ""))
                        a = ch.get("a", ch.get("_global_a", ""))
                        ch_id = ch['id']
                        
                        hls_url = f"https://boti.my.id/index.m3u8?u={u}&x={x}&a={a}&id={ch_id}&type=hls&api=video"
                        dash_url = f"https://boti.my.id/index.mpd?u={u}&x={x}&a={a}&id={ch_id}&type=dash&api=video"
                        drm_url = f"https://boti.my.id/index.php?u={u}&x={x}&a={a}&id={ch_id}&type=drm&api=video"
                        
                        f.write(f'#EXTINF:-1 tvg-logo="{logo}" group-title="{group_str}", {name} (HLS)\n')
                        f.write(f'{hls_url}\n')
                        
                        f.write(f'#EXTINF:-1 tvg-logo="{logo}" group-title="{group_str}", {name} (DASH)\n')
                        f.write('#KODIPROP:inputstream=inputstream.adaptive\n')
                        f.write('#KODIPROP:inputstream.adaptive.manifest_type=mpd\n')
                        f.write('#KODIPROP:inputstream.adaptive.license_type=com.widevine.alpha\n') 
                        f.write(f'#KODIPROP:inputstream.adaptive.license_key={drm_url}\n')
                        f.write(f'{dash_url}\n')
                        
                        total_episodes += 1
                        
            print(f"Sukses! Tersimpan {total_episodes} episode dari {len(seen_series)} judul SERIES berbeda (JSON).")
            
        except json.JSONDecodeError:
            print("Error: Output API bukan JSON dan bukan M3U yang valid.")
            
    except requests.exceptions.RequestException as e:
        print(f"Koneksi ke API gagal: {e}")

if __name__ == "__main__":
    generate_playlist()
