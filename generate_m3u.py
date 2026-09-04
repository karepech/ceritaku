import requests
import json
import traceback

API_URL = "https://boti.my.id/index.php?api=playlist&email=mbkidriss9%40gmail.com&password=12345678"
OUTPUT_FILE = "playlist-vidio.m3u"

def generate_playlist():
    print("Mengecek API...")
    try:
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
