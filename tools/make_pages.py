"""產生線上版（GitHub Pages，docs/）用到的資料與素材。

* docs/img/：程式圖示（PWA 192／512、apple-touch-icon 180）、計算尺知識的圖片
* docs/voice/<課程>.mp3：語音動態教學旁白（從 assets/voice 複製）
* docs/voice/demo/*.mp3＋docs/app/data.js：常用算式示範每一步的語音（微軟神經語音 曉臻，免費）、
  課程文字、計算尺知識內容 → 線上版不必連任何伺服器；沒有預錄的算式改用瀏覽器內建語音

用法：.venv\\Scripts\\python tools\\make_pages.py   （產生示範語音需要網路；已存在的檔案會略過）
"""
import asyncio
import hashlib
import json
import os
import shutil
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)

from PIL import Image  # noqa: E402

from sr import APP_VERSION  # noqa: E402
from sr.demo import PRESETS, plan  # noqa: E402
from sr.help_text import LESSONS  # noqa: E402
from sr.voice import VOICE  # noqa: E402

DOCS = os.path.join(HERE, "docs")


def icons():
    out = os.path.join(DOCS, "img")
    os.makedirs(out, exist_ok=True)
    src = Image.open(os.path.join(HERE, "assets", "icon.png")).convert("RGBA")
    for name, size in (("icon-512.png", 512), ("icon-192.png", 192), ("favicon-64.png", 64)):
        src.resize((size, size), Image.LANCZOS).save(os.path.join(out, name))
    # apple-touch-icon 不能透明：鋪上系列的深藍底
    bg = Image.new("RGBA", src.size, (15, 60, 110, 255))
    Image.alpha_composite(bg, src).convert("RGB").resize((180, 180), Image.LANCZOS).save(
        os.path.join(out, "apple-touch-icon.png"))
    src.resize((256, 256), Image.LANCZOS).save(os.path.join(DOCS, "icon.png"))
    learn = os.path.join(DOCS, "img", "learn")
    os.makedirs(learn, exist_ok=True)
    for f in os.listdir(os.path.join(HERE, "assets", "learn")):
        shutil.copy2(os.path.join(HERE, "assets", "learn", f), os.path.join(learn, f))


def lesson_voice():
    out = os.path.join(DOCS, "voice")
    os.makedirs(out, exist_ok=True)
    for s in LESSONS:
        shutil.copy2(os.path.join(HERE, "assets", "voice", s["key"] + ".mp3"), os.path.join(out, s["key"] + ".mp3"))


async def demo_voice():
    out = os.path.join(DOCS, "voice", "demo")
    os.makedirs(out, exist_ok=True)
    import edge_tts
    exprs = list(PRESETS) + [s["demo"] for s in LESSONS if s.get("demo") and s["demo"] not in PRESETS]
    index = {}
    for e in exprs:
        for st in plan(e)["steps"]:
            text = st["text"]
            name = hashlib.sha1((VOICE + text).encode("utf-8")).hexdigest()[:20] + ".mp3"
            path = os.path.join(out, name)
            index[text] = name
            if os.path.isfile(path) and os.path.getsize(path) > 0:
                continue
            for n in range(5):
                try:
                    await edge_tts.Communicate(text, VOICE, rate="+5%").save(path)
                    break
                except Exception as ex:                    # edge-tts 偶爾回 503，稍等再試
                    print("retry", text[:20], ex)
                    await asyncio.sleep(3 + n * 3)
    keep = set(index.values())
    for f in os.listdir(out):
        if f not in keep:
            os.remove(os.path.join(out, f))
    return index


def data_js(index):
    from sr.ui.learnview import SECTIONS, SOURCE
    lessons = [dict(key=s["key"], title=s["title"], demo=s.get("demo") or "", voice=s["voice"],
                    steps=[[icon, tone, text, sid] for icon, tone, text, sid in s["steps"]]) for s in LESSONS]
    learn = [dict(title=t, img=img, cap=cap, paras=paras) for t, img, cap, paras in SECTIONS]
    data = dict(version=APP_VERSION, voice=index, lessons=lessons, learn=learn, learn_source=SOURCE)
    with open(os.path.join(DOCS, "app", "data.js"), "w", encoding="utf-8", newline="\n") as f:
        f.write("/* 由 tools/make_pages.py 產生，請勿手動修改 */\nwindow.SR_DATA = ")
        json.dump(data, f, ensure_ascii=False, indent=1)
        f.write(";\n")


def main():
    icons()
    lesson_voice()
    index = asyncio.run(demo_voice())
    data_js(index)
    print("ok：示範語音 %d 段" % len(index))


if __name__ == "__main__":
    main()
