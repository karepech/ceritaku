import requests
import json
import traceback

API_URL = "https://boti.my.id/index.php?api=playlist&email=mbkidriss9%40gmail.com&password=12345678"
OUTPUT_FILE = "playlist-vidio.m3u"

def generate_playlist():
    print("Mengecek API...")
    try:import requests
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
            print("Sukses! File M3U utuh.")
            return
            
        try:
            data = response.json()
            channels_to_process = []
            
            # --- PARSING STRUKTUR JSON ---
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict):
                        if "channels" in item and isinstance(item["channels"], list):
                            cat = item.get("category", item.get("group", item.get("name", "Vidio")))
                            for ch in item["channels"]:
                                if isinstance(ch, dict):
                                    ch["_auto_group"] = cat
                                    channels_to_process.append(ch)
                        else:
                            channels_to_process.append(item)
                            
            elif isinstance(data, dict):
                global_u = data.get("u", "mbkidriss9@gmail.com")
                global_x = data.get("x", "")
                global_a = data.get("a", "")
                
                for key, value in data.items():
                    if isinstance(value, list):
                        cat = "Vidio" if key.lower() in ["data", "channels", "list"] else key
                        for item in value:
                            if isinstance(item, dict):
                                item["_auto_group"] = cat
                                item["_global_u"] = global_u
                                item["_global_x"] = global_x
                                item["_global_a"] = global_a
                                channels_to_process.append(item)
            
            # --- PENULISAN M3U DENGAN 3 FORMAT (HLS, DASH, DRM) ---
            count = 0
            with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
                f.write("#EXTM3U\n")
                
                for ch in channels_to_process:
                    name = ch.get("name", ch.get("title", ch.get("channel", "Unknown")))
                    logo = ch.get("logo", ch.get("image", ""))
                    group = ch.get("group", ch.get("category", ch.get("category_name", ch.get("_auto_group", "Vidio"))))
                    
                    # Ambil token parameter
                    u = ch.get("u", ch.get("_global_u", "mbkidriss9@gmail.com"))
                    x = ch.get("x", ch.get("_global_x", ""))
                    a = ch.get("a", ch.get("_global_a", ""))
                    ch_id = ch.get("id", "")
                    
                    license_key = ch.get("license", ch.get("clearkey", ch.get("drm_key", "")))
                    
                    if ch_id:
                        # 1. FORMAT HLS (.m3u8)
                        url_hls = f"https://boti.my.id/index.m3u8?u={u}&x={x}&a={a}&id={ch_id}&type=hls&api=video"
                        f.write(f'#EXTINF:-1 tvg-logo="{logo}" group-title="{group}", {name} [HLS]\n')
                        f.write(f'{url_hls}\n')
                        
                        # 2. FORMAT DASH (.mpd)
                        url_dash = f"https://boti.my.id/index.mpd?u={u}&x={x}&a={a}&id={ch_id}&type=dash&api=video"
                        f.write(f'#EXTINF:-1 tvg-logo="{logo}" group-title="{group}", {name} [DASH]\n')
                        f.write(f'{url_dash}\n')
                        
                        # 3. FORMAT DRM (index.php)
                        url_drm = f"https://boti.my.id/index.php?u={u}&x={x}&a={a}&id={ch_id}&type=drm&api=video"
                        if license_key:
                            f.write(f'#KODIPROP:inputstream.adaptive.license_type=clearkey\n')
                            f.write(f'#KODIPROP:inputstream.adaptive.license_key={license_key}\n')
                        f.write(f'#EXTINF:-1 tvg-logo="{logo}" group-title="{group}", {name} [DRM]\n')
                        f.write(f'{url_drm}\n')
                        
                        count += 3
                    
                    elif "url" in ch or "link" in ch:
                        # Fallback jika API langsung memberikan direct link
                        direct_url = ch.get("url", ch.get("link", ""))
                        f.write(f'#EXTINF:-1 tvg-logo="{logo}" group-title="{group}", {name}\n')
                        f.write(f'{direct_url}\n')
                        count += 1
                        
            print(f"Sukses! Total {count} baris stream (HLS, DASH, DRM) berhasil di-generate.")
            
        except json.JSONDecodeError:
            print("Error: Output API tidak valid.")
            
    except requests.exceptions.RequestException as e:
        print(f"Koneksi ke API gagal: {e}")

if __name__ == "__main__":
    generate_playlist()
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(API_URL, headers=headers, timeout=15)
        content = response.text.strip()
        
        if content.startswith("#EXTM3U"):
            with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
                f.write(content)
            print("Sukses! File M3U utuh.")
            return
            
        try:
            data = response.json()
            # TAMPILKAN 500 KARAKTER PERTAMA DARI JSON UNTUK DEBUG
            print("=== BENTUK DATA API ===")
            print(str(data)[:500]) 
            print("=======================\n")
            
            channels_to_process = []
            
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict):
                        if "channels" in item and isinstance(item["channels"], list):
                            cat = item.get("category", item.get("group", item.get("name", "Vidio")))
                            for ch in item["channels"]:
                                if isinstance(ch, dict):
                                    ch["_auto_group"] = cat
                                    channels_to_process.append(ch)
                        else:
                            channels_to_process.append(item)
                            
            elif isinstance(data, dict):
                global_u = data.get("u", "mbkidriss9@gmail.com")
                global_x = data.get("x", "")
                global_a = data.get("a", "")
                
                for key, value in data.items():
                    if isinstance(value, list):
                        cat = "Vidio" if key.lower() in ["data", "channels", "list"] else key
                        for item in value:
                            if isinstance(item, dict):
                                item["_auto_group"] = cat
                                item["_global_u"] = global_u
                                item["_global_x"] = global_x
                                item["_global_a"] = global_a
                                channels_to_process.append(item)

            if not channels_to_process:
                print("GAGAL: Tidak ada channel yang ditemukan. Struktur JSON tidak cocok.")
                return

            count = 0
            with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
                f.write("#EXTM3U\n")
                for ch in channels_to_process:
                    name = ch.get("name", ch.get("title", ch.get("channel", "Unknown")))
                    logo = ch.get("logo", ch.get("image", ""))
                    group = ch.get("group", ch.get("category", ch.get("category_name", ch.get("_auto_group", "Vidio"))))
                    
                    stream_url = ch.get("url", ch.get("link", ""))
                    is_drm = ch.get("drm", False) or ch.get("is_drm", False) or ("drm" in str(ch).lower())
                    license_key = ch.get("license", ch.get("clearkey", ch.get("drm_key", "")))
                    
                    if not stream_url and "id" in ch:
                        u = ch.get("u", ch.get("_global_u", "mbkidriss9@gmail.com"))
                        x = ch.get("x", ch.get("_global_x", ""))
                        a = ch.get("a", ch.get("_global_a", ""))
                        
                        tipe = "dash" if is_drm else "hls"
                        ext = "mpd" if is_drm else "m3u8"
                        stream_url = f"https://boti.my.id/index.{ext}?u={u}&x={x}&a={a}&id={ch['id']}&type={tipe}&api=video"
                            
                    if stream_url:
                        if is_drm and license_key:
                            f.write(f'#KODIPROP:inputstream.adaptive.license_type=clearkey\n')
                            f.write(f'#KODIPROP:inputstream.adaptive.license_key={license_key}\n')
                        f.write(f'#EXTINF:-1 tvg-logo="{logo}" group-title="{group}", {name}\n')
                        f.write(f'{stream_url}\n')
                        count += 1
                        
            print(f"SUKSES! {count} channel berhasil di-generate.")
            
        except json.JSONDecodeError:
            print("GAGAL: Output bukan JSON/M3U.")
            print("Response:", content[:300])
        except Exception as e:
            print(f"ERROR SAAT PARSING DATA:\n{traceback.format_exc()}")
            
    except requests.exceptions.RequestException as e:
        print(f"GAGAL KONEKSI KE API:\n{e}")

if __name__ == "__main__":
    generate_playlist()
