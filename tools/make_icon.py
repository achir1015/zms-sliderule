"""產生程式圖示：assets/icon.png（1024）、packaging/icon.ico、assets/icon.ico。

資料助秘系列的深藍到青綠圓角方塊；上方「計算尺」標題列，中間是一把傾斜的計算尺
（上下定尺、錯開的滑尺、紅色髮線游標），右上角金幣寫「算」，左下角「資料助秘」標籤。
"""
import os

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S = 1024


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def shadow(img, shape_fn, blur=18, offset=(10, 20), alpha=100):
    sh = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    shape_fn(ImageDraw.Draw(sh), offset, (0, 0, 0, alpha))
    return Image.alpha_composite(img, sh.filter(ImageFilter.GaussianBlur(blur)))


def font(size):
    try:
        f = ImageFont.truetype(os.path.join(HERE, "assets", "fonts", "NotoSansTC-VF.ttf"), size)
        try:
            f.set_variation_by_name("Black")
        except Exception:
            pass
        return f
    except Exception:
        return ImageFont.load_default()


def main():
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    grad = Image.new("RGBA", (S, S))
    gd = ImageDraw.Draw(grad)
    c1, c2 = (15, 60, 110), (14, 150, 120)
    for y in range(S):
        gd.line([(0, y), (S, y)], fill=lerp(c1, c2, y / S) + (255,))
    mask = Image.new("L", (S, S), 0)
    ImageDraw.Draw(mask).rounded_rectangle([40, 40, S - 40, S - 40], radius=220, fill=255)
    img.paste(grad, (0, 0), mask)
    gloss = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    ImageDraw.Draw(gloss).ellipse([-200, -520, S + 200, 420], fill=(255, 255, 255, 34))
    img = Image.alpha_composite(img, Image.composite(gloss, Image.new("RGBA", (S, S)), mask))

    # 標題列「計算尺」
    img = shadow(img, lambda d, o, f: d.rounded_rectangle([150 + o[0], 150 + o[1], 690 + o[0], 300 + o[1]], radius=50,
                                                          fill=f), blur=16, offset=(8, 16), alpha=90)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([150, 150, 690, 300], radius=50, fill=(30, 77, 140, 255), outline=(120, 170, 230, 255), width=6)
    d.text((420, 222), "計算尺", font=font(98), fill=(255, 255, 255, 255), anchor="mm")

    # 計算尺本體（稍微傾斜）：上定尺、滑尺（往右錯開）、下定尺、游標
    rule = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    r = ImageDraw.Draw(rule)
    x0, x1 = 90, 934
    top, s0, s1, bot = 400, 500, 610, 710
    r.rounded_rectangle([x0, top, x1, bot], radius=26, fill=(247, 236, 205, 255), outline=(176, 150, 96, 255), width=6)
    off = 70
    r.rectangle([x0 - 10 + off, s0, x1 + off - 20, s1], fill=(255, 251, 236, 255), outline=(176, 150, 96, 255),
                width=5)
    import math
    L = x1 - x0 - 60

    def ticks(y, down, shift, color, nums):
        for k in range(10, 101):
            v = k / 10
            x = x0 + 30 + shift + L * math.log10(v)
            if x > x1 - 30 + shift or x > x1 + off - 30:
                continue
            big = k % 10 == 0
            mid = k % 5 == 0
            ln = 44 if big else (30 if mid else 18)
            r.line([(x, y), (x, y + ln if down else y - ln)], fill=color, width=6 if big else 3)
            if big and nums and k // 10 in (1, 2, 3, 4, 5, 7):
                r.text((x, (y + ln + 26) if down else (y - ln - 26)), str(k // 10), font=font(40), fill=color,
                       anchor="mm")
    ticks(s0, False, 0, (31, 41, 55, 255), True)          # 上定尺（刻度朝下緣）
    ticks(s0, True, off, (31, 41, 55, 255), False)        # 滑尺上緣
    ticks(s1, False, off, (192, 57, 43, 255), False)      # 滑尺下緣（紅色倒數）
    ticks(s1, True, 0, (31, 41, 55, 255), True)           # 下定尺
    # 游標：透明玻璃＋紅色髮線
    cx = x0 + 30 + off + L * math.log10(2)
    glass = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    g = ImageDraw.Draw(glass)
    g.rounded_rectangle([cx - 62, top - 40, cx + 62, bot + 40], radius=18, fill=(150, 195, 245, 60),
                        outline=(60, 110, 190, 230), width=6)
    g.line([(cx, top - 40), (cx, bot + 40)], fill=(214, 40, 40, 255), width=8)
    rule = Image.alpha_composite(rule, glass)
    rule = rule.rotate(8, center=(512, 560), resample=Image.BICUBIC)
    sh = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    sh.paste((0, 0, 0, 100), (12, 22), rule.getchannel("A"))
    img = Image.alpha_composite(img, sh.filter(ImageFilter.GaussianBlur(18)))
    img = Image.alpha_composite(img, rule)

    # 金幣「算」
    cx, cy, rr = 810, 225, 135
    img = shadow(img, lambda d, o, f: d.ellipse([cx - rr + o[0], cy - rr + o[1], cx + rr + o[0], cy + rr + o[1]],
                                                fill=f), blur=16, offset=(10, 18), alpha=110)
    d = ImageDraw.Draw(img)
    d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], fill=(240, 180, 40, 255), outline=(255, 226, 140, 255), width=14)
    d.ellipse([cx - rr + 30, cy - rr + 30, cx + rr - 30, cy + rr - 30], outline=(201, 138, 20, 255), width=6)
    d.text((cx, cy - 6), "算", font=font(136), fill=(20, 50, 92, 255), anchor="mm")
    # 左下角「資料助秘」小標籤
    d.rounded_rectangle([140, 800, 470, 880], radius=40, fill=(255, 255, 255, 235))
    d.text((305, 838), "資料助秘", font=font(52), fill=(30, 77, 140, 255), anchor="mm")
    img.putalpha(Image.composite(img.getchannel("A"), Image.new("L", (S, S), 0), mask))
    out = os.path.join(HERE, "assets", "icon.png")
    img.save(out)
    sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    for p in (os.path.join(HERE, "packaging", "icon.ico"), os.path.join(HERE, "assets", "icon.ico")):
        img.save(p, sizes=sizes)
    print("ok", out)


if __name__ == "__main__":
    main()
