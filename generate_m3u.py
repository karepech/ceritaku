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
        
        if content.startswith("#EXTM3U"):
            with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
                f.write(content)
            print("Sukses! File M3U (Direct) berhasil diperbarui.")
            return
            
        try:
            data = response.json()
            channels_to_process = []
            
            # --- DETEKSI KATEGORI (List / Dict) ---
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
            
            # --- PENULISAN FILE M3U & LOGIKA DRM ---
            count = 0
            with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
                f.write("#EXTM3U\n")
                
                for ch in channels_to_process:
                    name = ch.get("name", ch.get("title", ch.get("channel", "Unknown")))
                    logo = ch.get("logo", ch.get("image", ""))
                    group = ch.get("group", ch.get("category", ch.get("category_name", ch.get("_auto_group", "Vidio"))))
                    
                    stream_url = ch.get("url", ch.get("link", ""))
                    
                    # Cek apakah channel ini butuh DRM dari data JSON-nya
                    is_drm = ch.get("drm", False) or ch.get("is_drm", False) or ("drm" in str(ch).lower())
                    license_key = ch.get("license", ch.get("clearkey", ch.get("drm_key", "")))
                    
                    if not stream_url and "id" in ch:
                        u = ch.get("u", ch.get("_global_u", "mbkidriss9@gmail.com"))
                        x = ch.get("x", ch.get("_global_x", ""))
                        a = ch.get("a", ch.get("_global_a", ""))
                        
                        if is_drm:
                            # Merakit link DRM/DASH untuk channel Live yang dienkripsi
                            stream_url = f"https://boti.my.id/index.mpd?u={u}&x={x}&a={a}&id={ch['id']}&type=dash&api=video"
                            # Jika API murni butuh endpoint drm, Anda bisa mengubah type=dash di atas menjadi type=drm
                        else:
                            # Merakit link HLS standar
                            stream_url = f"https://boti.my.id/index.m3u8?u={u}&x={x}&a={a}&id={ch['id']}&type=hls&api=video"
                            
                    if stream_url:
                        # Jika ada license key (ClearKey/Widevine), tambahkan tag KODIPROP agar dibaca OTT Navigator/TiviMate
                        if is_drm and license_key:
                            f.write(f'#KODIPROP:inputstream.adaptive.license_type=clearkey\n')
                            f.write(f'#KODIPROP:inputstream.adaptive.license_key={license_key}\n')
                            
                        f.write(f'#EXTINF:-1 tvg-logo="{logo}" group-title="{group}", {name}\n')
                        f.write(f'{stream_url}\n')
                        count += 1
                        
            print(f"Sukses! {count} channel berhasil di-generate beserta kategorinya (Termasuk dukungan DRM).")
            
        except json.JSONDecodeError:
            print("Error: Output API tidak valid.")
            
    except requests.exceptions.RequestException as e:
        print(f"Koneksi ke API gagal: {e}")

if __name__ == "__main__":
    generate_playlist()
