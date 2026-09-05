import requests
import json
import os
import re

# === KONFIGURASI 2 FILE OUTPUT ===
API_URL = "https://boti.my.id/index.php?api=playlist&email=mbkidriss9%40gmail.com&password=12345678"
OUTPUT_LIVE = "live.m3u"
OUTPUT_UPCOMING = "upcoming.m3u"

DEFAULT_U = "mbkidriss9%40gmail.com"
DEFAULT_X = "644_SrZsWczYRmp5J7Xx"
DEFAULT_A = "eyJhbGciOiJIUzI1NiJ9.eyJkYXRhIjp7InR5cGUiOiJhY2Nlc3NfdG9rZW4iLCJ1aWQiOjIyMjMzNzE5NH0sImV4cCI6MTc4ODY3NzAzOH0.UHImVkHT2jujFUpPlo_vfULpyt1lZArjsLgw-CX7lVc"

def build_live_block(logo, group, name, u, x, a, ch_id):
    # DIBANGUN TANPA &api=video SEPERTI PERMINTAAN ANDA
    hls_url = f"https://boti.my.id/index.m3u8?u={u}&x={x}&a={a}&id={ch_id}&type=hls"
    dash_url = f"https://boti.my.id/index.mpd?u={u}&x={x}&a={a}&id={ch_id}&type=dash"
    drm_url = f"https://boti.my.id/index.php?u={u}&x={x}&a={a}&id={ch_id}&type=drm"
    
    block = f'#EXTINF:-1 tvg-logo="{logo}" group-title="{group}", {name} (HLS)\n{hls_url}\n'
    block += f'#EXTINF:-1 tvg-logo="{logo}" group-title="{group}", {name} (DASH)\n'
    block += '#KODIPROP:inputstream=inputstream.adaptive\n'
    block += '#KODIPROP:inputstream.adaptive.manifest_type=mpd\n'
    block += '#KODIPROP:inputstream.adaptive.license_type=com.widevine.alpha\n'
    block += f'#KODIPROP:inputstream.adaptive.license_key={drm_url}\n{dash_url}\n\n'
    return block

def generate_live_playlist():
    print(f"Mengambil data Live & Upcoming...\nURL: {API_URL}")
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        response = requests.get(API_URL, headers=headers, timeout=15)
        response.raise_for_status() 
        content = response.text.strip().lstrip('\ufeff')
        
        # =================================================================
        # JIKA M3U LANGSUNG
        # =================================================================
        if content.startswith("#EXTM3U"):
            print("Mendeteksi M3U. Memproses Live...")
            lines = content.splitlines()
            live_lines = ["#EXTM3U\n"]
            upcoming_lines = ["#EXTM3U\n"]
            
            current_block = []
            category_target = None
            
            for line in lines[1:]: 
                line_str = line.strip()
                if line_str == "": continue
                    
                if line_str.startswith("#EXTINF"):
                    if current_block and category_target:
                        full_text = "\n".join(current_block)
                        extinf = current_block[0]
                        
                        # Ekstrak data untuk rakit ulang
                        m_logo = re.search(r'tvg-logo="([^"]*)"', extinf, re.IGNORECASE)
                        logo = m_logo.group(1) if m_logo else ""
                        
                        m_group = re.search(r'group-title="([^"]+)"', extinf, re.IGNORECASE)
                        group = m_group.group(1).strip() if m_group else "Uncategorized"
                        
                        m_name = re.search(r',\s*(.+)$', extinf)
                        name = m_name.group(1).strip() if m_name else "Unknown"
                        
                        m_id = re.search(r'id=(\d+)', full_text)
                        if m_id:
                            ch_id = m_id.group(1)
                            m_u = re.search(r'u=([^&\s\n]+)', full_text)
                            m_x = re.search(r'x=([^&\s\n]+)', full_text)
                            m_a = re.search(r'a=([^&\s\n]+)', full_text)
                            
                            u = m_u.group(1) if m_u else DEFAULT_U
                            x = m_x.group(1) if m_x else DEFAULT_X
                            a = m_a.group(1) if m_a else DEFAULT_A
                            
                            block = build_live_block(logo, group, name, u, x, a, ch_id)
                            
                            if category_target == "live": live_lines.append(block)
                            elif category_target == "upcoming": upcoming_lines.append(block)

                    current_block = [line_str]
                    category_target = None
                    
                    match = re.search(r'group-title="([^"]+)"', line_str, re.IGNORECASE)
                    if match:
                        group_lower = match.group(1).lower()
                        if "upcoming" in group_lower: category_target = "upcoming"
                        elif "live" in group_lower or "tv" in group_lower or "nasional" in group_lower: category_target = "live"
                else:
                    if current_block: current_block.append(line_str)
            
            # Eksekusi sisa blok terakhir
            if current_block and category_target:
                full_text = "\n".join(current_block)
                extinf = current_block[0]
                m_id = re.search(r'id=(\d+)', full_text)
                if m_id:
                    m_logo = re.search(r'tvg-logo="([^"]*)"', extinf, re.IGNORECASE)
                    m_group = re.search(r'group-title="([^"]+)"', extinf, re.IGNORECASE)
                    m_name = re.search(r',\s*(.+)$', extinf)
                    
                    m_u = re.search(r'u=([^&\s\n]+)', full_text)
                    m_x = re.search(r'x=([^&\s\n]+)', full_text)
                    m_a = re.search(r'a=([^&\s\n]+)', full_text)
                    
                    block = build_live_block(
                        m_logo.group(1) if m_logo else "",
                        m_group.group(1).strip() if m_group else "Uncategorized",
                        m_name.group(1).strip() if m_name else "Unknown",
                        m_u.group(1) if m_u else DEFAULT_U,
                        m_x.group(1) if m_x else DEFAULT_X,
                        m_a.group(1) if m_a else DEFAULT_A,
                        m_id.group(1)
                    )
                    if category_target == "live": live_lines.append(block)
                    elif category_target == "upcoming": upcoming_lines.append(block)

            with open(OUTPUT_LIVE, "w", encoding="utf-8") as f: f.writelines(live_lines)
            with open(OUTPUT_UPCOMING, "w", encoding="utf-8") as f: f.writelines(upcoming_lines)
            print("Sukses memproses M3U Khusus Live!")
            return

        # =================================================================
        # JIKA JSON (Fallback System dari kode Anda)
        # =================================================================
        try:
            data = response.json()
            print("Mendeteksi format JSON. Memulai proses Live...")
            channels_to_process = []
            
            if isinstance(data, list):
                for item in data:
                    if "channels" in item and isinstance(item["channels"], list):
                        cat_name = item.get("category", item.get("group", item.get("name", "Uncategorized")))
                        for ch in item["channels"]:
                            if isinstance(ch, dict):
                                ch["_auto_group"] = cat_name
                                channels_to_process.append(ch)
                    elif isinstance(item, dict): channels_to_process.append(item)
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
            
            live_lines = ["#EXTM3U\n"]
            upcoming_lines = ["#EXTM3U\n"]
            
            for ch in channels_to_process:
                name = ch.get("name", ch.get("title", ch.get("channel", "Unknown")))
                logo = ch.get("logo", ch.get("image", ""))
                group = ch.get("group", ch.get("category", ch.get("category_name", ch.get("_auto_group", "Vidio"))))
                group_title_original = str(group).strip()
                group_lower = group_title_original.lower()
                
                stream_url = ch.get("url", ch.get("link", ""))
                if not stream_url and "id" in ch:
                    u = ch.get("u", ch.get("_global_u", "mbkidriss9@gmail.com"))
                    x = ch.get("x", ch.get("_global_x", ""))
                    a = ch.get("a", ch.get("_global_a", ""))
                    ch_id = ch['id']
                    
                    block = build_live_block(logo, group_title_original, name, u, x, a, ch_id)
                    
                    if "upcoming" in group_lower:
                        upcoming_lines.append(block)
                    elif "live" in group_lower or "tv" in group_lower or "nasional" in group_lower:
                        live_lines.append(block)

            with open(OUTPUT_LIVE, "w", encoding="utf-8") as f: f.writelines(live_lines)
            with open(OUTPUT_UPCOMING, "w", encoding="utf-8") as f: f.writelines(upcoming_lines)
            print("Sukses memproses JSON Khusus Live!")
            
        except json.JSONDecodeError:
            print("Error: Bukan JSON dan bukan M3U.")
            
    except requests.exceptions.RequestException as e:
        print(f"Koneksi gagal: {e}")

if __name__ == "__main__":
    generate_live_playlist()
