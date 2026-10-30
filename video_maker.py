import json
import re
import time
import subprocess
# EDGE_TTS_AMHARIC
import urllib.parse
import urllib.request
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output"
SCENE_DIR = BASE_DIR / "assets" / "scenes"


def fetch_images(topic):
    SCENE_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # ቀድሞ የተቀመጡ ምስሎችን አስቀድመን እንይ
    cached = sorted(
        p for p in SCENE_DIR.iterdir()
        if p.is_file() and p.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}
        and p.stat().st_size > 5000
    )
    if cached:
        print(f"Using {min(len(cached), 3)} cached image(s).", flush=True)
        return cached[:3]

    try:
        query = re.sub(r"[^A-Za-z0-9 ]", " ", topic)
        query = " ".join(query.split()[:5]).strip() or "nature landscape"

        params = {
            "action": "query",
            "generator": "search",
            "gsrsearch": "filetype:bitmap " + query,
            "gsrnamespace": "6",
            "gsrlimit": "4",
            "prop": "imageinfo",
            "iiprop": "url|extmetadata",
            "iiurlwidth": "1280",
            "format": "json",
        }
        url = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode(params)
        request = urllib.request.Request(
            url,
            headers={
                "User-Agent": "KBRealBnbitBot/1.0 (educational video project)",
                "Accept": "application/json",
            },
        )

        with urllib.request.urlopen(request, timeout=15) as response:
            data = json.loads(response.read().decode("utf-8"))

        pages = data.get("query", {}).get("pages", {})
        images = []
        sources = []

        for page in pages.values():
            info = page.get("imageinfo", [{}])[0]
            image_url = info.get("thumburl") or info.get("url")
            if not image_url:
                continue

            try:
                req = urllib.request.Request(
                    image_url,
                    headers={"User-Agent": "KBRealBnbitBot/1.0 (educational video project)"},
                )
                with urllib.request.urlopen(req, timeout=15) as response:
                    content = response.read()

                if len(content) < 5000:
                    continue

                path = SCENE_DIR / f"scene_{len(images) + 1}.jpg"
                path.write_bytes(content)
                images.append(path)

                meta = info.get("extmetadata", {})
                artist = meta.get("Artist", {}).get("value", "Unknown")
                license_name = meta.get("LicenseShortName", {}).get("value", "Check source")
                page_url = info.get("descriptionurl", "")
                sources.append(
                    f"Image: {page.get('title', 'Unknown')}\\n"
                    f"Author: {artist}\\n"
                    f"License: {license_name}\\n"
                    f"Source: {page_url}\\n"
                )

                if len(images) >= 3:
                    break
            except Exception as exc:
                print("Image download failed:", str(exc), flush=True)

        (OUTPUT_DIR / "image_sources.txt").write_text(
            "\\n---\\n".join(sources), encoding="utf-8"
        )
        if images:
            return images

    except Exception as exc:
        print("Wikimedia unavailable:", str(exc), flush=True)

    # ምስሎች ካልተገኙ ከዚህ በፊት የተቀመጡ ምስሎችን እንደገና ፈልግ
    cached = sorted(
        p for p in SCENE_DIR.iterdir()
        if p.is_file() and p.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}
        and p.stat().st_size > 5000
    )
    if cached:
        return cached[:3]

    raise RuntimeError(
        "ምስሎችን ማውረድ አልተቻለም፤ የኢንተርኔት ግንኙነትን ፈትሽ ወይም assets/scenes ውስጥ ምስል አስቀምጥ።"
    )

def run_ffmpeg(command):
    result = subprocess.run(
        command, capture_output=True, text=True
    )
    if result.returncode != 0:
        raise RuntimeError(
            "FFmpeg error:\n" + result.stderr[-2500:]
        )


def make_video(topic: str, voice: str = 'am-ET-MekdesNeural') -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    spoken_text = topic.strip()
    text = topic.strip()[:65] or "KBReal Creator"

    voice_file = OUTPUT_DIR / f"narration_{time.time_ns()}.mp3"

    # ረዘም ያለ የአማርኛ ትረካ
    voice_script = f"""
ዛሬ ስለ {spoken_text} በዝርዝር እንነጋገራለን።
ወደዚህ ርዕስ ከመግባታችን በፊት ለምን አስፈላጊ እንደሆነ እንመልከት።
አንድን ርዕስ በትክክል ለመረዳት መረጃን መፈለግ፣
ማንበብ፣ መጠየቅ እና የተማርነውን በተግባር መጠቀም ያስፈልጋል።

በመጀመሪያ፣ ስለዚህ ርዕስ መሠረታዊ ግንዛቤ ማግኘት አስፈላጊ ነው።
ሰዎች አንድን ነገር በተለያየ መንገድ ሊያዩት ይችላሉ።
ስለዚህ የተለያዩ አስተያየቶችን ማዳመጥ እና እውነታዎችን
ከግምቶች መለየት ጠቃሚ ነው።

ሁለተኛ፣ የምናገኘውን መረጃ በጥንቃቄ መመርመር አለብን።
ምንጩ ማን እንደሆነ፣ መረጃው መቼ እንደተዘጋጀ
እና ከሌሎች አስተማማኝ ምንጮች ጋር የሚስማማ መሆኑን
ማረጋገጥ ይገባል።

ሦስተኛ፣ በትምህርትና በልምድ መማር ያስፈልጋል።
አንድ ነገር በአንድ ጊዜ ላይገባን ይችላል።
ግን በትዕግሥት መሞከር፣ ጥያቄዎችን መጠየቅ
እና የተሳሳትንበትን ቦታ ማስተካከል እድገት ያመጣል።

አራተኛ፣ ጊዜን በጥሩ ሁኔታ መጠቀም ጠቃሚ ነው።
ትልቅ ዓላማን ወደ ትንንሽ ደረጃዎች መክፈል
ሥራውን የበለጠ ቀላል ያደርገዋል።
በየቀኑ ትንሽ ጊዜ በመመደብ በቀስታ ወደ ዓላማችን
መቅረብ እንችላለን።

አምስተኛ፣ ከሌሎች ጋር መስራት እና ልምድን መጋራት
ብዙ ጊዜ አዳዲስ ሀሳቦችን ያመጣል።
ሌሎችን በአክብሮት ማዳመጥ፣ በግልጽ መናገር
እና በጋራ መፍትሔ መፈለግ ይረዳል።

እንዲሁም በኢንተርኔት የምናየውን ሁሉ ወዲያውኑ
እውነት ብለን መቀበል የለብንም።
የመረጃውን ምንጭ እና ትክክለኛነት ማረጋገጥ
እና የግል መረጃችንን መጠበቅ አስፈላጊ ነው።

አሁን ዋና ዋና ነጥቦችን እንደገና እናስታውስ።
መሠረታዊ ግንዛቤ ይኑረን፣ አስተማማኝ መረጃ እንፈልግ፣
በትዕግሥት እንማር፣ ጊዜያችንን በጥሩ ሁኔታ እንጠቀም
እና ከሌሎች ጋር በአክብሮት እንስራ።

ይህ ቪዲዮ ጠቃሚ ከሆነላችሁ ለሌሎችም አጋሩት።
ለተጨማሪ ቪዲዮዎች የKBReal Creator ይዘቶችን መከታተል ትችላላችሁ።
ስለተመለከታችሁ እናመሰግናለን።
"""


    result = subprocess.run(
        [
            "edge-tts",
            "--voice", voice,
            "--text", voice_script,
            "--write-media", str(voice_file),
        ],
        capture_output=True,
        text=True,
        timeout=120,
    )
    if result.returncode != 0 or not voice_file.exists():
        raise RuntimeError(
            "የአማርኛ ድምፅ ማመንጨት አልተሳካም: "
            + result.stderr[-1000:]
        )

    text_file = OUTPUT_DIR / f"video_text_{time.time_ns()}.txt"
    text_file.write_text(text.replace("\\", "\\\\").replace("%", "\\%").replace(":", "\\:"), encoding="utf-8")

    image_topic = re.sub(r"[^A-Za-z0-9 ]", " ", topic).strip() or "Ethiopia landscape"
    images = fetch_images(image_topic)

    if not images:
        raise RuntimeError(
            "ምስሎችን ማውረድ አልተቻለም። "
            "Internet እና የWikimedia Commons ግንኙነትን ፈትሽ።"
        )

    output_file = OUTPUT_DIR / f"video_{time.time_ns()}.mp4"
    clips = []

    for index, image_path in enumerate(images, start=1):
        clip_path = OUTPUT_DIR / f"scene_clip_{index}.mp4"
        clips.append(clip_path)

        video_filter = (
            "scale=720:1280:force_original_aspect_ratio=increase,"
            "crop=720:1280,"
            "zoompan=z='min(zoom+0.0015,1.12)':"
            "x='iw/2-(iw/zoom/2)':"
            "y='ih/2-(ih/zoom/2)':"
            "d=90:s=720x1280:fps=30,"
            "drawbox=x=0:y=ih-250:w=iw:h=250:"
            "color=black@0.55:t=fill,"
            f"drawtext=fontfile='{(BASE_DIR / 'assets/fonts/NotoSansEthiopic-VF.ttf').as_posix()}':"
            f"textfile='{text_file}':"
            "fontcolor=white:fontsize=40:"
            "x=(w-text_w)/2:y=h-190,"
            "drawtext=text='KBREAL CREATOR':"
            "fontcolor=0x00D9FF:fontsize=27:"
            "x=(w-text_w)/2:y=70,"
            "format=yuv420p"
        )

        run_ffmpeg([
            "ffmpeg", "-y",
            "-loop", "1", "-framerate", "30",
            "-i", str(image_path),
            "-vf", video_filter,
            "-frames:v", "90",
            "-an",
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-pix_fmt", "yuv420p",
            "-r", "30",
            str(clip_path),
        ])

    duration = 300
    total_clips = 100
    repeated_clips = [clips[i % len(clips)] for i in range(total_clips)]

    concat_file = OUTPUT_DIR / "concat_list.txt"
    concat_file.write_text(
        "".join(f"file '{clip.resolve()}'\n" for clip in repeated_clips),
        encoding="utf-8"
    )

    audio_filter = (
        "[1:a]volume=1.5[voice];"
        "[2:a]volume=0.08[a1];"
        "[3:a]volume=0.06[a2];"
        "[4:a]volume=0.05[a3];"
        "[voice][a1][a2][a3]amix=inputs=4:duration=longest:"
        "normalize=0,"
        "alimiter=limit=0.95,"
        f"afade=t=out:st={max(0, duration - 1)}:d=1[a]"
    )

    run_ffmpeg([
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", str(concat_file),
        "-i", str(voice_file),
        "-f", "lavfi", "-i",
        f"sine=frequency=220:sample_rate=44100:duration={duration}",
        "-f", "lavfi", "-i",
        f"sine=frequency=277:sample_rate=44100:duration={duration}",
        "-f", "lavfi", "-i",
        f"sine=frequency=330:sample_rate=44100:duration={duration}",
        "-filter_complex", audio_filter,
        "-map", "0:v",
        "-map", "[a]",
        "-t", str(duration),
        "-c:v", "copy",
        "-c:a", "aac",
        "-b:a", "128k",
        "-movflags", "+faststart",
        str(output_file),
    ])

    print(
        f"Video created: {output_file} "
        f"({output_file.stat().st_size} bytes)",
        flush=True
    )

    return output_file
