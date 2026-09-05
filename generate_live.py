import requests
import json

# === KONFIGURASI ===
API_URL = "https://boti.my.id/index.php?api=playlist&email=mbkidriss9%40gmail.com&password=12345678"
OUTPUT_FILE = "live_only.m3u"

# Default Token (Fallback jika diperlukan)
DEFAULT_U = "mbkidriss9%40gmail.com"
DEFAULT_X = "644_SrZsWczYRmp5J7Xx"
DEFAULT_A = "eyJhbGciOiJIUzI1NiJ9.eyJkYXRhIjp7InR5cGUiOiJhY2Nlc3NfdG9rZW4iLCJ1aWQiOjIyMjMzNzE5NH0sImV4cCI6MTc4ODY3NzAzOH0.UHImVkHT2jujFUpPlo_vfULpyt1lZArjsLgw-CX7lVc"

def generate_live_playlist():
    print(f"Mengambil data API Khusus LIVE...\nURL: {API_URL}")
    
    try:
        # KUNCI UTAMA DARI GAMBAR ANDA: Tambahkan Accept application/json
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Accept": "application/json" 
        }
        
        response = requests.get(API_URL, headers=headers, timeout=15)
        response.raise_for_status() 
        
        try:
            data = response.json()
            print("Sukses membaca format JSON dari server. Memulai filter kategori Live...")
            
            channels = []
            
            # --- 1. MENYUSUN DATA JSON (Apapun bentuk dari servernya) ---
            if isinstance(data, list):
                for item in data:
                    if "channels" in item and isinstance(item["channels"], list):
                        cat = item.get("category", item.get("group", item.get("name", "Uncategorized")))
                        for ch in item["channels"]:
                            if isinstance(ch, dict):
                                ch["_auto_group"] = cat
                                channels.append(ch)
                    elif isinstance(item, dict):
                        channels.append(item)
            elif isinstance(data, dict):
                # Ekstrak token global (opsional jika ada di root JSON)
                global_u = data.get("u", DEFAULT_U)
                global_x = data.get("x", DEFAULT_X)
                global_a = data.get("a", DEFAULT_A)
                
                for key, value in data.items():
                    if isinstance(value, list):
                        cat = "Vidio" if key.lower() in ["data", "channels", "list"] else key
                        for item in value:
                            if isinstance(item, dict):
                                item["_auto_group"] = cat
                                item["_global_u"] = global_u
                                item["_global_x"] = global_x
                                item["_global_a"] = global_a
                                channels.append(item)
            
            # --- 2. PENYARINGAN & PEMBUATAN M3U ---
            out_lines = ["#EXTM3U\n"]
            count = 0
            
            for ch in channels:
                name = ch.get("name", ch.get("title", ch.get("channel", "Unknown")))
                logo = ch.get("logo", ch.get("image", ""))
                group = ch.get("group", ch.get("category", ch.get("category_name", ch.get("_auto_group", "Vidio"))))
                group_lower = str(group).lower()
                
                # Filter khusus untuk Live / TV
                if "live" in group_lower or "tv" in group_lower or "nasional" in group_lower or "upcoming" in group_lower:
                    
                    if "id" in ch:
                        ch_id = ch['id']
                        # Ambil parameter token (Prioritas: Data Channel > Data Global > Fallback)
                        u = ch.get("u", ch.get("_global_u", DEFAULT_U))
                        x = ch.get("x", ch.get("_global_x", DEFAULT_X))
                        a = ch.get("a", ch.get("_global_a", DEFAULT_A))
                        
                        # RAKIT URL SESUAI STANDAR DOKUMENTASI DEVELOPER
                        hls_url = f"https://boti.my.id/index.m3u8?u={u}&x={x}&a={a}&id={ch_id}&type=hls"
                        dash_url = f"https://boti.my.id/index.mpd?u={u}&x={x}&a={a}&id={ch_id}&type=dash"
                        drm_url = f"https://boti.my.id/index.php?u={u}&x={x}&a={a}&id={ch_id}&type=drm"
                        
                        # Susun blok M3U (HLS dan DASH DRM)
                        block = f'#EXTINF:-1 tvg-logo="{logo}" group-title="{group}", {name} (HLS)\n{hls_url}\n'
                        block += f'#EXTINF:-1 tvg-logo="{logo}" group-title="{group}", {name} (DASH)\n'
                        block += '#KODIPROP:inputstream=inputstream.adaptive\n'
                        block += '#KODIPROP:inputstream.adaptive.manifest_type=mpd\n'
                        block += '#KODIPROP:inputstream.adaptive.license_type=com.widevine.alpha\n'
                        block += f'#KODIPROP:inputstream.adaptive.license_key={drm_url}\n{dash_url}\n\n'
                        
                        out_lines.append(block)
                        count += 1
                        
            # Simpan hasil akhir
            with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
                f.writelines(out_lines)
                
            print(f"Sempurna! {count} channel Live berhasil dirakit dari JSON dengan akurat.")
            
        except json.JSONDecodeError:
            print("Error: Meskipun sudah memakai header JSON, server masih menolak. Pastikan email & password di API_URL benar.")
            
    except requests.exceptions.RequestException as e:
        print(f"Koneksi ke API gagal: {e}")

if __name__ == "__main__":
    generate_live_playlist()
