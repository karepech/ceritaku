import requests
import json
import os

API_URL = "https://boti.my.id/index.php?api=playlist&email=mbkidriss9%40gmail.com&password=12345678"
OUTPUT_FILE = "playlist-vidio.m3u"

def generate_playlist():
    print("Mengambil data terbaru dari API...")
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
            
            # Parsing struktur data dari API
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict):
                        if "channels" in item and isinstance(item["channels"], list):
                            cat = item.get("category", item.get("group", "Vidio"))
                            for ch in item["channels"]:
                                if isinstance(ch, dict):
                                    ch["_auto_group"] = cat
                                    channels_to_process.append(ch)
                        else:
                            channels_to_process.append(item)
                            
            elif isinstance(data, dict):
                # Ambil token global jika ada di level root JSON
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
            
            count = 0
            with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
                f.write("#EXTM3U\n")
                
                for ch in channels_to_process:
                    name = ch.get("name", ch.get("title", ch.get("channel", "Unknown")))
                    logo = ch.get("logo", ch.get("image", ""))
                    group = ch.get("group", ch.get("category", ch.get("_auto_group", "Vidio")))
                    
                    # Ambil parameter keamanan (u, x, a) secara spesifik dari channel atau global
                    u = ch.get("u", ch.get("_global_u", "mbkidriss9@gmail.com"))
                    x = ch.get("x", ch.get("_global_x", ""))
                    a = ch.get("a", ch.get("_global_a", ""))
                    ch_id = ch.get("id", "")
                    
                    if ch_id:
                        # Pastikan parameter token 'a' (signature JWT) dimasukkan secara utuh tanpa modifikasi string
                        url_hls = f"https://boti.my.id/index.m3u8?u={u}&x={x}&a={a}&id={ch_id}&type=hls&api=video"
                        f.write(f'#EXTINF:-1 tvg-logo="{logo}" group-title="{group}", {name}\n')
                        f.write(f'{url_hls}\n')
                        count += 1
                        
            print(f"Sukses! {count} channel berhasil di-generate ulang dengan token valid.")
            
        except json.JSONDecodeError:
            print("Error: Gagal membaca format JSON dari API.")
            
    except requests.exceptions.RequestException as e:
        print(f"Koneksi gagal: {e}")

if __name__ == "__main__":
    generate_playlist()
