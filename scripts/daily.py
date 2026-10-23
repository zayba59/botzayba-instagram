"""Günlük BotZayba paylaşımı.

  python scripts/daily.py prepare   # günün içeriğini seçer/üretir, görseli posts/ altına kaydeder
  python scripts/daily.py publish   # hazırlanan görseli Instagram'a paylaşır

Ortam değişkenleri:
  GEMINI_API_KEY   (isteğe bağlı) varsa her gün yapay zekâ ile yeni reklam yazılır
  GEMINI_MODEL     (isteğe bağlı) varsayılan: gemini-2.5-flash
  IG_USER_ID       Instagram profesyonel hesap kimliği
  IG_ACCESS_TOKEN  Facebook sayfa erişim anahtarı
  GRAPH_VERSION    (isteğe bağlı) varsayılan: v23.0
  IMAGE_BASE_URL   görselin herkese açık adresi için önek (GitHub Actions'ta otomatik)
"""
import datetime as dt
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from generate import ROOT, load_content, render  # noqa: E402

POSTS = ROOT / "posts"
STATE = POSTS / "state.json"
TODAY = dt.datetime.now(dt.timezone(dt.timedelta(hours=3))).date().isoformat()  # Türkiye saati

# Yapay zekânın yazdığı metinde görmek istemediğimiz vaatler
FORBIDDEN = [r"garanti", r"kesin kazan", r"\d+\s*%", r"%\s*\d+", r"zengin", r"pasif gelir", r"risksiz"]


def load_state():
    if STATE.exists():
        return json.loads(STATE.read_text(encoding="utf-8"))
    return {"next_index": 0, "history": []}


def http_json(url, data=None, method=None):
    body = None
    headers = {}
    if data is not None:
        body = json.dumps(data).encode()
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"HTTP {e.code}: {e.read().decode(errors='replace')[:500]}") from None


# ---------- yapay zekâ ile içerik ----------

def gemini_post(data, history):
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        return None
    model = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
    examples = json.dumps(data["posts"][:6], ensure_ascii=False, indent=1)
    recent = "\n".join(f"- {h['title']}" for h in history[-40:])
    prompt = f"""Sen BotZayba'nın Instagram içerik yazarısın. BotZayba, Binance'te grid stratejisiyle
çalışan algoritmik bir kripto trading botudur. Şu an satışta değildir; amaç marka bilinirliği ve
takipçi kazanmaktır. Türkçe, samimi, öğretici ve güven veren bir dil kullan.

KESİN KURALLAR:
- Kazanç, getiri, kâr garantisi veya yüzde/rakam ile getiri vaadi YOK.
- "zengin ol", "pasif gelir", "risksiz" gibi ifadeler YOK.
- Fiyat tahmini veya "şu coin'i al" tavsiyesi YOK.
- Uygunsa risklerden dürüstçe bahset.

Daha önce paylaşılan başlıklar (bunları tekrar etme, farklı bir konu seç):
{recent or '- (yok)'}

Örnek gönderiler (aynı JSON biçimini kullan):
{examples}

Tek bir yeni gönderi üret. JSON alanları:
layout: "statement" | "tips" | "steps"
kicker: en fazla 22 karakter, büyük harf
title: en fazla 40 karakter, gerekiyorsa tek bir \\n ile iki satıra böl
body: (sadece statement) en fazla 140 karakter
items: (sadece tips/steps) tam 4 madde, her biri en fazla 42 karakter
caption: Instagram açıklaması, 300-700 karakter, hashtag içermesin"""
    url = (f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key="
           + urllib.parse.quote(key))
    resp = http_json(url, {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseMimeType": "application/json", "temperature": 1.0},
    })
    text = resp["candidates"][0]["content"]["parts"][0]["text"]
    post = json.loads(text)
    if isinstance(post, list):
        post = post[0]
    return validate(post)


def validate(post):
    layout = post.get("layout")
    if layout not in ("statement", "tips", "steps"):
        raise ValueError(f"geçersiz layout: {layout}")
    for k in ("kicker", "title", "caption"):
        if not isinstance(post.get(k), str) or not post[k].strip():
            raise ValueError(f"eksik alan: {k}")
    if layout == "statement" and not post.get("body"):
        raise ValueError("statement için body yok")
    if layout != "statement":
        items = post.get("items")
        if not isinstance(items, list) or not 3 <= len(items) <= 5:
            raise ValueError("items 3-5 madde olmalı")
    if len(post["title"]) > 60 or len(post["kicker"]) > 30:
        raise ValueError("başlık çok uzun")
    blob = " ".join([post["title"], post.get("body", ""), " ".join(post.get("items", [])), post["caption"]]).lower()
    for pat in FORBIDDEN:
        if re.search(pat, blob):
            raise ValueError(f"yasaklı ifade: {pat}")
    return {k: post[k] for k in ("layout", "kicker", "title", "body", "items", "caption") if k in post}


# ---------- komutlar ----------

def prepare():
    data = load_content()
    state = load_state()
    if any(h["date"] == TODAY for h in state["history"]):
        print(f"{TODAY} için içerik zaten hazır.")
        return

    post, source = None, "bank"
    try:
        post = gemini_post(data, state["history"])
        if post:
            source = "gemini"
    except Exception as e:  # yapay zekâ başarısız olursa içerik bankasına düş
        print(f"Gemini kullanılamadı, içerik bankası kullanılıyor: {e}")
    if not post:
        idx = state["next_index"] % len(data["posts"])
        post = data["posts"][idx]
        state["next_index"] = idx + 1

    POSTS.mkdir(exist_ok=True)
    seed = len(state["history"])
    render(post, data["brand"], seed=seed).save(POSTS / f"{TODAY}.jpg", quality=92)
    caption = f"{post['caption'].strip()}\n\n⚠️ {data['brand']['footer']}\n\n{data['brand']['hashtags']}"
    (POSTS / f"{TODAY}.json").write_text(
        json.dumps({**post, "full_caption": caption, "source": source}, ensure_ascii=False, indent=2),
        encoding="utf-8")
    state["history"].append({"date": TODAY, "title": post["title"].replace("\n", " "), "source": source})
    STATE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Hazır: posts/{TODAY}.jpg ({source}) — {post['title']!r}")


def publish():
    uid = os.environ.get("IG_USER_ID")
    token = os.environ.get("IG_ACCESS_TOKEN")
    base = os.environ.get("IMAGE_BASE_URL", "").rstrip("/")
    if not (uid and token and base):
        print("IG_USER_ID / IG_ACCESS_TOKEN / IMAGE_BASE_URL eksik — paylaşım atlandı (deneme modu).")
        return
    meta = json.loads((POSTS / f"{TODAY}.json").read_text(encoding="utf-8"))
    state = load_state()
    entry = next(h for h in state["history"] if h["date"] == TODAY)
    if entry.get("media_id"):
        print("Bugünün gönderisi zaten paylaşılmış.")
        return

    graph = f"https://graph.facebook.com/{os.environ.get('GRAPH_VERSION', 'v23.0')}"
    image_url = f"{base}/posts/{TODAY}.jpg"
    print("Görsel adresi:", image_url)

    q = urllib.parse.urlencode({"image_url": image_url, "caption": meta["full_caption"], "access_token": token})
    container = http_json(f"{graph}/{uid}/media?{q}", method="POST")["id"]

    for _ in range(30):  # Instagram görseli işlerken bekle
        st = http_json(f"{graph}/{container}?fields=status_code&access_token={urllib.parse.quote(token)}")
        if st.get("status_code") == "FINISHED":
            break
        if st.get("status_code") == "ERROR":
            raise RuntimeError(f"Instagram görseli işleyemedi: {st}")
        time.sleep(5)

    q = urllib.parse.urlencode({"creation_id": container, "access_token": token})
    media_id = http_json(f"{graph}/{uid}/media_publish?{q}", method="POST")["id"]
    entry["media_id"] = media_id
    STATE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Paylaşıldı! media_id={media_id}")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    {"prepare": prepare, "publish": publish}.get(cmd, lambda: sys.exit(__doc__))()
