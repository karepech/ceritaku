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
                    # Model 1: [{"category_name": "Sports", "channels": [...]}]
                    if "channels" in item and isinstance(item["channels"], list):
                        cat_name = item.get("category", item.get("group", item.get("name", "Uncategorized")))
                        for ch in item["channels"]:
                            if isinstance(ch, dict):
                                ch["_auto_group"] = cat_name
                                channels_to_process.append(ch)
                    # Model 2: Flat List [{"name": "Trans TV", "category": "Nasional"}]
                    elif isinstance(item, dict):
                        channels_to_process.append(item)

            # SKENARIO B: JSON berupa Dictionary
            elif isinstance(data, dict):
                # Ambil global auth keys jika ada di root JSON
                global_u = data.get("u", "mbkidriss9@gmail.com")
                global_x = data.get("x", "")
                global_a = data.get("a", "")
                
                for key, value in data.items():
                    if isinstance(value, list):
                        # Jika nama key bukan sekadar "data" atau "channels", jadikan nama Kategori
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
                    # Pertahankan huruf kapital/kecil aslinya
                    name = ch.get("name", ch.get("title", ch.get("channel", "Unknown")))
                    logo = ch.get("logo", ch.get("image", ""))
                    
                    # Prioritas Kategori: Ambil dari dalam object dulu, jika kosong pakai auto_group
                    group = ch.get("group", ch.get("category", ch.get("category_name", ch.get("_auto_group", "Vidio"))))
                    
                    stream_url = ch.get("url", ch.get("link", ""))
                    
                    if not stream_url and "id" in ch:
                        u = ch.get("u", ch.get("_global_u", "mbkidriss9@gmail.com"))
                        x = ch.get("x", ch.get("_global_x", ""))
                        a = ch.get("a", ch.get("_global_a", ""))
                        
                        stream_url = f"https://boti.my.id/index.m3u8?u={u}&x={x}&a={a}&id={ch['id']}&type=hls&api=video"
                            
                    if stream_url:
                        f.write(f'#EXTINF:-1 tvg-logo="{logo}" group-title="{group}", {name}\n')
                        f.write(f'{stream_url}\n')
                        count += 1
                        
            print(f"Sukses! {count} channel berhasil di-generate beserta kategorinya.")
            
        except json.JSONDecodeError:
            print("Error: Output API tidak valid.")
            
    except requests.exceptions.RequestException as e:
        print(f"Koneksi ke API gagal: {e}")

if __name__ == "__main__":
    generate_playlist()
