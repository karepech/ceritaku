import requests
import json
import os

# === KONFIGURASI ===
API_URL = "https://boti.my.id/index.php?api=playlist&email=mbkidriss9%40gmail.com&password=12345678"
OUTPUT_INDO = "indo.m3u"
OUTPUT_LUAR = "luar.m3u"

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
            print("Mendeteksi format M3U langsung. Memulai proses filter dan pemisahan teks...")
            lines = content.splitlines()
            
            indo_lines = ["#EXTM3U"]
            luar_lines = ["#EXTM3U"]
            
            current_block = []
            is_series = False
            is_indo = False
            
            count_indo = 0
            count_luar = 0
            
            for line in lines[1:]: # Lewati baris pertama (#EXTM3U)
                line_str = line.strip()
                if line_str == "":
                    continue
                    
                if line_str.startswith("#EXTINF"):
                    # Masukkan blok sebelumnya ke kategori yang sesuai
                    if current_block and is_series:
                        if is_indo:
                            indo_lines.extend(current_block)
                            indo_lines.append("") # Jarak antar channel
                            count_indo += 1
                        else:
                            luar_lines.extend(current_block)
                            luar_lines.append("")
                            count_luar += 1
                    
                    # Mulai blok channel baru
                    current_block = [line_str]
                    
                    # Cek kategori
                    line_lower = line_str.lower()
                    if "group-title" in line_lower and "series" in line_lower:
                        is_series = True
                        # Jika ada kata "indo" (misal "Indonesia"), masuk ke indo.m3u
                        if "indo" in line_lower:
                            is_indo = True
                        else:
                            is_indo = False
                    else:
                        is_series = False
                else:
                    # Tambahkan baris URL atau atribut lain (seperti #EXTVLCOPT) ke blok saat ini
                    if current_block:
                        current_block.append(line_str)
            
            # Jangan lupa masukkan blok channel terakhir jika lolos filter
            if current_block and is_series:
                if is_indo:
                    indo_lines.extend(current_block)
                    indo_lines.append("")
                    count_indo += 1
                else:
                    luar_lines.extend(current_block)
                    luar_lines.append("")
                    count_luar += 1

            # Tulis hasil ke 2 file yang berbeda
            with open(OUTPUT_INDO, "w", encoding="utf-8") as f:
                f.write("\n".join(indo_lines))
                
            with open(OUTPUT_LUAR, "w", encoding="utf-8") as f:
                f.write("\n".join(luar_lines))
                
            print(f"Sukses! Pemisahan selesai:\n- {OUTPUT_INDO}: {count_indo} channel\n- {OUTPUT_LUAR}: {count_luar} channel")
            return

        # JIKA API MENGEMBALIKAN JSON (Fallback jika sewaktu-waktu format berubah)
        try:
            data = response.json()
            print("Mendeteksi format JSON. Memulai proses konversi dan pemisahan...")
            
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
            
            indo_lines = ["#EXTM3U"]
            luar_lines = ["#EXTM3U"]
            count_indo = 0
            count_luar = 0
            
            for ch in channels_to_process:
                name = ch.get("name", ch.get("title", ch.get("channel", "Unknown")))
                logo = ch.get("logo", ch.get("image", ""))
                group = ch.get("group", ch.get("category", ch.get("category_name", ch.get("_auto_group", "Vidio"))))
                group_lower = str(group).lower()
                
                if "series" not in group_lower:
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
                    
                    block = []
                    block.append(f'#EXTINF:-1 tvg-logo="{logo}" group-title="{group}", {name} (HLS)')
                    block.append(f'{hls_url}')
                    block.append(f'#EXTINF:-1 tvg-logo="{logo}" group-title="{group}", {name} (DASH)')
                    block.append('#KODIPROP:inputstream=inputstream.adaptive')
                    block.append('#KODIPROP:inputstream.adaptive.manifest_type=mpd')
                    block.append('#KODIPROP:inputstream.adaptive.license_type=com.widevine.alpha') 
                    block.append(f'#KODIPROP:inputstream.adaptive.license_key={drm_url}')
                    block.append(f'{dash_url}')
                    
                    if "indo" in group_lower:
                        indo_lines.extend(block)
                        count_indo += 1
                    else:
                        luar_lines.extend(block)
                        count_luar += 1
                        
            with open(OUTPUT_INDO, "w", encoding="utf-8") as f:
                f.write("\n".join(indo_lines))
                
            with open(OUTPUT_LUAR, "w", encoding="utf-8") as f:
                f.write("\n".join(luar_lines))
                
            print(f"Sukses (JSON)! Pemisahan selesai:\n- {OUTPUT_INDO}: {count_indo} channel\n- {OUTPUT_LUAR}: {count_luar} channel")
            
        except json.JSONDecodeError:
            print("Error: Output API bukan JSON dan bukan M3U yang valid.")
            
    except requests.exceptions.RequestException as e:
        print(f"Koneksi ke API gagal: {e}")

if __name__ == "__main__":
    generate_playlist()
