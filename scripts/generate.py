"""BotZayba Instagram reklam görseli üretici.

Kullanım:
  python scripts/generate.py --preview          # tüm içerikler için örnek görsel üretir (preview/)
  python scripts/generate.py --index 3 --out x.jpg
"""
import argparse
import json
import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
FONTS = ASSETS / "fonts"

W, H = 1080, 1350  # Instagram 4:5 dikey gönderi
PAD = 84

NAVY_TOP = (5, 17, 43)
NAVY_BOTTOM = (9, 42, 102)
CYAN = (24, 200, 255)
BLUE = (30, 120, 255)
WHITE = (255, 255, 255)
MUTED = (170, 190, 225)


def font(weight, size):
    return ImageFont.truetype(str(FONTS / f"Inter-{weight}.otf"), size)


def load_content():
    return json.loads((ROOT / "content.json").read_text(encoding="utf-8"))


# ---------- arka plan ----------

def background(seed):
    rnd = random.Random(seed)
    img = Image.new("RGB", (W, H))
    px = img.load()
    for y in range(H):
        t = y / (H - 1)
        row = tuple(int(NAVY_TOP[i] + (NAVY_BOTTOM[i] - NAVY_TOP[i]) * t) for i in range(3))
        for x in range(W):
            px[x, y] = row

    # sağ üstte yumuşak parıltı
    glow = Image.new("L", (W, H), 0)
    ImageDraw.Draw(glow).ellipse((W - 520, -320, W + 320, 420), fill=110)
    glow = glow.filter(ImageFilter.GaussianBlur(160))
    img = Image.composite(Image.new("RGB", (W, H), BLUE), img, glow)

    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)

    # ince ızgara
    for x in range(0, W, 54):
        d.line([(x, 0), (x, H)], fill=(120, 170, 255, 14))
    for y in range(0, H, 54):
        d.line([(0, y), (W, y)], fill=(120, 170, 255, 14))

    # grid seviyeleri + seviyeler arasında gidip gelen fiyat çizgisi (alt bölüm)
    top, bottom = H - 340, H - 150
    levels = 6
    ys = [top + i * (bottom - top) / (levels - 1) for i in range(levels)]
    for y in ys:
        for x in range(0, W, 28):
            d.line([(x, y), (x + 14, y)], fill=(90, 160, 255, 45), width=2)

    pts = []
    x = -20
    lvl = rnd.randint(1, levels - 2)
    while x < W + 40:
        pts.append((x, ys[lvl]))
        step = rnd.choice([-1, 1])
        if not 0 <= lvl + step < levels:
            step = -step
        lvl += step
        x += rnd.randint(70, 120)
    d.line(pts, fill=(24, 200, 255, 90), width=4, joint="curve")
    for i in range(1, len(pts) - 1):
        px_, py_ = pts[i]
        buy = pts[i][1] > pts[i - 1][1]  # aşağı inince alım
        col = (24, 200, 255, 150) if buy else (90, 140, 255, 150)
        d.ellipse((px_ - 9, py_ - 9, px_ + 9, py_ + 9), fill=col)

    # metin alanını okunur tutmak için alt bölümü hafifçe karart
    shade = Image.new("L", (W, H), 0)
    sd = ImageDraw.Draw(shade)
    for y in range(H):
        sd.line([(0, y), (W, y)], fill=int(70 * max(0, (y - H * 0.55) / (H * 0.45))))
    img = img.convert("RGBA")
    img.alpha_composite(layer)
    img = Image.composite(Image.new("RGBA", (W, H), NAVY_TOP + (255,)), img, shade)
    return img


# ---------- yazı yardımcıları ----------

def wrap(draw, text, fnt, max_w):
    lines = []
    for para in text.split("\n"):
        cur = ""
        for word in para.split():
            test = f"{cur} {word}".strip()
            if draw.textlength(test, font=fnt) <= max_w:
                cur = test
            else:
                if cur:
                    lines.append(cur)
                cur = word
        lines.append(cur)
    return lines


def fit_title(draw, text, max_w, max_h, start=104, minimum=56):
    # önce iki satıra sığdırmayı dene, olmazsa alana sığana kadar küçült
    for size in range(start, 75, -4):
        f = font("ExtraBold", size)
        lines = wrap(draw, text, f, max_w)
        if len(lines) <= 2:
            return f, lines, int(size * 1.12)
    size = start
    while size >= minimum:
        f = font("ExtraBold", size)
        lines = wrap(draw, text, f, max_w)
        lh = int(size * 1.12)
        if len(lines) * lh <= max_h and all(draw.textlength(l, font=f) <= max_w for l in lines):
            return f, lines, lh
        size -= 4
    f = font("ExtraBold", minimum)
    return f, wrap(draw, text, f, max_w), int(minimum * 1.12)


def draw_lines(draw, lines, fnt, x, y, lh, fill):
    for line in lines:
        draw.text((x, y), line, font=fnt, fill=fill)
        y += lh
    return y


def tracked(draw, xy, text, fnt, fill, tracking):
    x, y = xy
    for ch in text:
        draw.text((x, y), ch, font=fnt, fill=fill)
        x += draw.textlength(ch, font=fnt) + tracking
    return x


# ---------- ana çizim ----------

def render(post, brand, seed=0):
    img = background(seed)
    d = ImageDraw.Draw(img)
    content_w = W - 2 * PAD

    # logo
    logo = Image.open(ASSETS / "logo_white.png")
    lh_ = 150
    logo = logo.resize((int(logo.width * lh_ / logo.height), lh_), Image.LANCZOS)
    img.alpha_composite(logo, (PAD, 70))

    # üst etiket (kicker)
    y = 70 + lh_ + 70
    kf = font("Bold", 26)
    kicker = post.get("kicker", "").upper()
    kw = sum(d.textlength(c, font=kf) + 4 for c in kicker) - 4
    d.rounded_rectangle((PAD, y, PAD + kw + 44, y + 52), radius=26, outline=CYAN, width=2)
    tracked(d, (PAD + 22, y + 11), kicker, kf, CYAN, 4)
    y += 52 + 40

    # başlık
    tf, tlines, tlh = fit_title(d, post["title"], content_w, 360)
    y = draw_lines(d, tlines, tf, PAD, y, tlh, WHITE)
    y += 18
    d.rectangle((PAD, y, PAD + 110, y + 8), fill=CYAN)
    y += 8 + 48

    layout = post.get("layout", "statement")
    if layout == "statement":
        bf = font("Medium", 40)
        y = draw_lines(d, wrap(d, post.get("body", ""), bf, content_w), bf, PAD, y, 56, MUTED)
    else:
        items = post.get("items", [])
        nf = font("ExtraBold", 30)
        itf = font("SemiBold", 36)
        for i, item in enumerate(items, 1):
            lines = wrap(d, item, itf, content_w - 90)
            cy = y + 24
            if layout == "steps":
                d.ellipse((PAD, cy - 26, PAD + 52, cy + 26), fill=CYAN)
                num = str(i)
                d.text((PAD + 26 - d.textlength(num, font=nf) / 2, cy - 19), num, font=nf, fill=NAVY_TOP)
            else:
                d.rounded_rectangle((PAD + 8, cy - 18, PAD + 44, cy + 18), radius=8, outline=CYAN, width=3)
                d.line([(PAD + 16, cy), (PAD + 24, cy + 9), (PAD + 37, cy - 9)], fill=CYAN, width=4)
            y = draw_lines(d, lines, itf, PAD + 80, y + 2, 46, WHITE) + 26

    if y > H - 360:
        print(f"UYARI: metin alt bölüme taşıyor ({post['title'][:30]!r}, y={int(y)})")

    # alt bilgi
    ff = font("Bold", 30)
    sf = font("Regular", 22)
    d.line([(PAD, H - 118), (W - PAD, H - 118)], fill=(120, 170, 255, 70), width=2)
    d.text((PAD, H - 96), brand["handle"], font=ff, fill=WHITE)
    tag = "Grid Trading Bot"
    d.text((W - PAD - d.textlength(tag, font=ff), H - 96), tag, font=ff, fill=CYAN)
    d.text((PAD, H - 52), brand["footer"], font=sf, fill=(140, 160, 200))
    return img.convert("RGB")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview", action="store_true")
    ap.add_argument("--index", type=int, default=0)
    ap.add_argument("--out", default="out.jpg")
    a = ap.parse_args()
    data = load_content()
    if a.preview:
        out = ROOT / "preview"
        out.mkdir(exist_ok=True)
        for i, p in enumerate(data["posts"]):
            render(p, data["brand"], seed=i).save(out / f"{i:02d}.jpg", quality=92)
        print(f"{len(data['posts'])} görsel -> {out}")
    else:
        render(data["posts"][a.index], data["brand"], seed=a.index).save(a.out, quality=92)


if __name__ == "__main__":
    main()
