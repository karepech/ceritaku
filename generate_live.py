import requests
import re

# === KONFIGURASI FILE OUTPUT ===
API_URL = "https://boti.my.id/index.php?api=playlist&email=mbkidriss9%40gmail.com&password=12345678"
OUTPUT_LIVE = "live.m3u"
OUTPUT_UPCOMING = "upcoming.m3u"

FALLBACK_MP4 = "http://127.0.0.1/dummy.mp4"
DEFAULT_U = "mbkidriss9%40gmail.com"
DEFAULT_X = "644_SrZsWczYRmp5J7Xx"
DEFAULT_A = "eyJhbGciOiJIUzI1NiJ9.eyJkYXRhIjp7InR5cGUiOiJhY2Nlc3NfdG9rZW4iLCJ1aWQiOjIyMjMzNzE5NH0sImV4cCI6MTc4ODY3NzAzOH0.UHImVkHT2jujFUpPlo_vfULpyt1lZArjsLgw-CX7lVc"

def generate_live_playlist():
    print(f"Mengambil data Live & Upcoming...\nURL: {API_URL}")
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)", "Accept": "*/*"}
        response = requests.get(API_URL, headers=headers, timeout=20)
        content = response.text.strip()
        
        if not content.startswith("#EXTM3U"):
            print("API tidak merespons dengan format M3U.")
            return

        live_lines = ["#EXTM3U\n"]
        upcoming_lines = ["#EXTM3U\n"]
        c_live = c_upcoming = 0
        
        # MENGUMPULKAN RAW BLOCKS
        lines = content.splitlines()
        blocks = []
        curr_block = []
        for line in lines[1:]:
            line = line.strip()
            if not line: continue
            if line.startswith("#EXTINF"):
                if curr_block: blocks.append(curr_block)
                curr_block = [line]
            elif curr_block:
                curr_block.append(line)
        if curr_block: blocks.append(curr_block)
            
        for block_lines in blocks:
            extinf = block_lines[0]
            full_text = "\n".join(block_lines)
            
            m_group = re.search(r'group-title=["\']?([^"\',]+)["\']?', extinf, re.IGNORECASE)
            group = m_group.group(1).strip() if m_group else "Uncategorized"
            group_lower = group.lower()
            
            is_upcoming = "upcoming" in group_lower or "mendatang" in group_lower
            is_live = any(x in group_lower for x in ["live", "tv", "nasional", "sport"])
            
            if not is_upcoming and not is_live:
                continue
                
            m_id = re.search(r'id=(\d+)', full_text)
            has_http = "http" in full_text.lower()
            output_blocks = []
            other_tags = [l for l in block_lines[1:] if l.startswith("#")]
            
            # Jika URL hilang khusus tayangan upcoming, terapkan fallback
            if is_upcoming and not has_http:
                fallback_block = [extinf] + other_tags + [FALLBACK_MP4]
                output_blocks.append("\n".join(fallback_block) + "\n\n")
            elif m_id:
                ch_id = m_id.group(1)
                m_u = re.search(r'u=([^&\s\n]+)', full_text)
                m_x = re.search(r'x=([^&\s\n]+)', full_text)
                m_a = re.search(r'a=([^&\s\n]+)', full_text)
                
                u = m_u.group(1) if m_u else DEFAULT_U
                x = m_x.group(1) if m_x else DEFAULT_X
                a = m_a.group(1) if m_a else DEFAULT_A
                
                hls_url = f"https://boti.my.id/index.m3u8?u={u}&x={x}&a={a}&id={ch_id}&type=hls&api=video"
                dash_url = f"https://boti.my.id/index.mpd?u={u}&x={x}&a={a}&id={ch_id}&type=dash&api=video"
                drm_url = f"https://boti.my.id/index.php?u={u}&x={x}&a={a}&id={ch_id}&type=drm&api=video"
                
                hls_block = [extinf] + other_tags + [hls_url]
                output_blocks.append("\n".join(hls_block) + "\n")
                
                dash_block = [extinf] + other_tags + [
                    "#KODIPROP:inputstream=inputstream.adaptive",
                    "#KODIPROP:inputstream.adaptive.manifest_type=mpd",
                    "#KODIPROP:inputstream.adaptive.license_type=com.widevine.alpha",
                    f"#KODIPROP:inputstream.adaptive.license_key={drm_url}",
                    dash_url
                ]
                output_blocks.append("\n".join(dash_block) + "\n")
            else:
                # Raw block utuh
                output_blocks.append(full_text + "\n\n")

            if is_upcoming:
                for b in output_blocks: upcoming_lines.append(b)
                c_upcoming += 1
            elif is_live:
                for b in output_blocks: live_lines.append(b)
                c_live += 1
                
        with open(OUTPUT_LIVE, "w", encoding="utf-8") as f: f.writelines(live_lines)
        with open(OUTPUT_UPCOMING, "w", encoding="utf-8") as f: f.writelines(upcoming_lines)
        print(f"Sukses! Live: {c_live} | Upcoming: {c_upcoming}")
        
    except Exception as e:
        print(f"Kesalahan: {e}")

if __name__ == "__main__":
    generate_live_playlist()
