import requests
import json
import os

# === KONFIGURASI ===
API_URL = "https://boti.my.id/index.php?api=playlist&email=mbkidriss9%40gmail.com&password=12345678"
OUTPUT_FILE = "playlist-vidio.m3u"
MAX_SERIES = 100 # Batas maksimal series yang diambil

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
            print(f"Mendeteksi format M3U langsung. Mengambil maksimal {MAX_SERIES} SERIES teratas...")
            lines = content.splitlines()
            
            filtered_lines = ["#EXTM3U"]
            
            current_block = []
            is_series = False
            count = 0
            
            for line in lines[1:]: # Lewati baris pertama (#EXTM3U)
                if count >= MAX_SERIES:
                    break # Hentikan pencarian jika sudah 100
                    
                line_str = line.strip()
                if line_str == "":
                    continue
                    
                if line_str.startswith("#EXTINF"):
                    # Jika sebelumnya ada blok channel SERIES, simpan
                    if current_block and is_series:
                        filtered_lines.extend(current_block)
                        filtered_lines.append("") # Jarak antar channel
                        count += 1
                        
                        # Cek lagi setelah menambah, apakah sudah mencapai limit
                        if count >= MAX_SERIES:
                            break
                    
                    # Mulai blok channel baru
                    current_block = [line_str]
                    
                    # Cek apakah tag group-title mengandung kata "series"
                    if "group-title" in line_str.lower() and "series" in line_str.lower():
                        is_series = True
                    else:
                        is_series = False
                else:
                    # Tambahkan baris URL atau atribut lain ke blok saat ini
                    if current_block:
                        current_block.append(line_str)
            
            # Masukkan blok channel terakhir (jika file habis tepat sebelum limit)
            if current_block and is_series and count < MAX_SERIES:
                filtered_lines.extend(current_block)
                filtered_lines.append("")
                count += 1

            # Tulis hasil filter ke file
            with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
                f.write("\n".join(filtered_lines))
                
            print(f"Sukses! File M3U berhasil diperbarui. Total diambil: {count} SERIES.")
            return

        # JIKA API MENGEMBALIKAN JSON (Fallback)
        try:
            data = response.json()
            print("Mendeteksi format JSON. Memulai proses filter...")
            
            # ... (Logika ekstraksi JSON tetap dipertahankan sebagai cadangan jika API berubah) ...
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
            
            count = 0
            with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
                f.write("#EXTM3U\n")
                
                for ch in channels_to_process:
                    if count >= MAX_SERIES:
                        break

                    name = ch.get("name", ch.get("title", ch.get("channel", "Unknown")))
                    logo = ch.get("logo", ch.get("image", ""))
                    group = ch.get("group", ch.get("category", ch.get("category_name", ch.get("_auto_group", "Vidio"))))
                    
                    if "series" not in str(group).lower():
                        continue 

                    stream_url = ch.get("url", ch.get("link", ""))
                    
                    if not stream_url and "id" in ch:
                        u = ch.get("u", ch.get("_global_u", "mbkidriss9@gmail.com"))
                        x = ch.get("x", ch.get("_global_x", ""))
                        a = ch.get("a", ch.get("_global_a", ""))
                        ch_id = ch['id']
                        
                        hls_url = f"https://boti.my.id/index.m3u8?u={u}&x={x}&a={a}&id={ch_id}&type=hls&api=video"
                        dash_url = f"https://boti.my.id/index.mpd?u={u}&x={x}&a={a}&id={ch_id}&type=dash&api=video"
                        drm_url = f"https://boti.my.id/index.php?u={u}&x={x}&a={a}&id={ch_id}&type=drm&api=video"
                        
                        f.write(f'#EXTINF:-1 tvg-logo="{logo}" group-title="{group}", {name} (HLS)\n')
                        f.write(f'{hls_url}\n')
                        
                        f.write(f'#EXTINF:-1 tvg-logo="{logo}" group-title="{group}", {name} (DASH)\n')
                        f.write('#KODIPROP:inputstream=inputstream.adaptive\n')
                        f.write('#KODIPROP:inputstream.adaptive.manifest_type=mpd\n')
                        f.write('#KODIPROP:inputstream.adaptive.license_type=com.widevine.alpha\n') 
                        f.write(f'#KODIPROP:inputstream.adaptive.license_key={drm_url}\n')
                        f.write(f'{dash_url}\n')
                        
                        count += 1
                        
            print(f"Sukses! {count} channel SERIES berhasil di-generate dari JSON.")
            
        except json.JSONDecodeError:
            print("Error: Output API bukan JSON dan bukan M3U yang valid.")
            
    except requests.exceptions.RequestException as e:
        print(f"Koneksi ke API gagal: {e}")

if __name__ == "__main__":
    generate_playlist()
