import requests
import json
import os

# === KONFIGURASI ===
API_URL = "https://boti.my.id/index.php?api=playlist&email=mbkidriss9%40gmail.com&password=12345678"
OUTPUT_FILE = "playlist-vidio.m3u"

def generate_playlist():
    print(f"Mengambil data terbaru dari API...\nURL: {API_URL}")
    
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        response = requests.get(API_URL, headers=headers, timeout=15)
        response.raise_for_status() 
        content = response.text.strip()
        
        # Jika API langsung membalikkan M3U
        if content.startswith("#EXTM3U"):
            with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"Sukses! File M3U berhasil diperbarui.")
            return
            
        try:
            data = response.json()
            print("Membaca format JSON dan membedakan kategori bawaan...")
            
            channels_to_process = []
            
            # --- LOGIKA PENCARIAN KATEGORI OTOMATIS ---
            
            # SKENARIO A: JSON berupa List
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

            # SKENARIO B: JSON berupa Dictionary
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
            
            # --- PENULISAN FILE M3U ---
            count = 0
            with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
                f.write("#EXTM3U\n")
                
                for ch in channels_to_process:
                    name = ch.get("name", ch.get("title", ch.get("channel", "Unknown")))
                    logo = ch.get("logo", ch.get("image", ""))
                    group = ch.get("group", ch.get("category", ch.get("category_name", ch.get("_auto_group", "Vidio"))))
                    
                    stream_url = ch.get("url", ch.get("link", ""))
                    
                    if not stream_url and "id" in ch:
                        # Ambil parameter autentikasi
                        u = ch.get("u", ch.get("_global_u", "mbkidriss9@gmail.com"))
                        x = ch.get("x", ch.get("_global_x", ""))
                        a = ch.get("a", ch.get("_global_a", ""))
                        ch_id = ch['id']
                        
                        # Generate ke-3 link sesuai format
                        hls_url = f"https://boti.my.id/index.m3u8?u={u}&x={x}&a={a}&id={ch_id}&type=hls&api=video"
                        dash_url = f"https://boti.my.id/index.mpd?u={u}&x={x}&a={a}&id={ch_id}&type=dash&api=video"
                        drm_url = f"https://boti.my.id/index.php?u={u}&x={x}&a={a}&id={ch_id}&type=drm&api=video"
                        
                        # 1. Tulis versi HLS (Tanpa tag DRM)
                        f.write(f'#EXTINF:-1 tvg-logo="{logo}" group-title="{group}", {name} (HLS)\n')
                        f.write(f'{hls_url}\n')
                        
                        # 2. Tulis versi DASH dengan lisensi DRM
                        f.write(f'#EXTINF:-1 tvg-logo="{logo}" group-title="{group}", {name} (DASH)\n')
                        f.write('#KODIPROP:inputstream=inputstream.adaptive\n')
                        f.write('#KODIPROP:inputstream.adaptive.manifest_type=mpd\n')
                        # Untuk Vidio biasanya menggunakan Widevine
                        f.write('#KODIPROP:inputstream.adaptive.license_type=com.widevine.alpha\n') 
                        f.write(f'#KODIPROP:inputstream.adaptive.license_key={drm_url}\n')
                        f.write(f'{dash_url}\n')
                        
                        count += 1
                        
            print(f"Sukses! {count} channel berhasil di-generate. (Total {count*2} link karena HLS & DASH digabung).")
            
        except json.JSONDecodeError:
            print("Error: Output API tidak valid JSON.")
            
    except requests.exceptions.RequestException as e:
        print(f"Koneksi ke API gagal: {e}")

if __name__ == "__main__":
    generate_playlist()
