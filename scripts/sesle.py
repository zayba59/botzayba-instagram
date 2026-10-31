"""Yazılan metni Microsoft'un Türkçe sinirsel sesiyle okur → seslendirme/

Actions sekmesindeki "Metni seslendir" düğmesi bunu çalıştırır; bilgisayar
açık olmak zorunda değil, telefondan da tetiklenebilir.

Metin boş satırla ayrılmışsa her bölüm ayrı dosya olur (01.mp3, 02.mp3 ...)
ve hepsi birleştirilip tam.mp3 yazılır. Videoda sahne sahne yerleştirmek
gerektiğinde bölümler ayrı ayrı lazım oluyor.

Kullanım:
    python scripts/sesle.py --metin "Merhaba" --ses tr-TR-AhmetNeural
    python scripts/sesle.py --dosya metin.txt --hiz -5%
"""
import argparse
import asyncio
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

KOK = Path(__file__).resolve().parent.parent
CIKTI = KOK / "seslendirme"

# Okunurken bozulan kısaltmalar. Seslendirmeden önce yazıyla değiştirilir.
KISALTMALAR = {
    "BotZayba": "Bot Zayba", "BOTZAYBA": "Bot Zayba",
    "API": "A P I", "7/24": "yedi gün yirmi dört saat",
    "K/Z": "kâr zarar", "TL": "lira", "USDT": "u s d t",
}


def bildir(seviye, baslik, mesaj):
    """Actions arayüzünde görünen not. Günlükler indirilemediğinde tek kanal bu."""
    tek_satir = str(mesaj).replace("\n", " ")[:800]
    print(f"::{seviye} title={baslik}::{tek_satir}")


def hazirla(metin: str) -> str:
    for eski, yeni in KISALTMALAR.items():
        metin = metin.replace(eski, yeni)
    # yüzdeleri ve emojileri sesli okumaya uygun hale getir
    metin = re.sub(r"%\s*(\d+)", r"yüzde \1", metin)
    metin = re.sub(r"[*_#`•▪]", "", metin)
    return re.sub(r"[ \t]+", " ", metin).strip()


async def _uret(metin: str, ses: str, hiz: str, hedef: Path) -> None:
    import edge_tts
    await edge_tts.Communicate(metin, ses, rate=hiz).save(str(hedef))


def seslendir(metin: str, ses: str, hiz: str, hedef: Path) -> bool:
    """Resmî olmayan uç yoğunlukta 429 dönebiliyor; artan beklemeyle 3 kez dener."""
    for deneme, bekle in enumerate((0, 5, 15), start=1):
        if bekle:
            time.sleep(bekle)
        try:
            asyncio.run(_uret(metin, ses, hiz, hedef))
        except Exception as e:
            bildir("notice", "Ses", f"{deneme}. deneme olmadı: {str(e)[:120]}")
            continue
        if hedef.exists() and hedef.stat().st_size > 2000:
            return True
        bildir("notice", "Ses", f"{deneme}. deneme boş dosya verdi")
    return False


def sure(yol: Path) -> float:
    try:
        r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                            "-of", "csv=p=0", str(yol)], capture_output=True, text=True)
        return float(r.stdout.strip() or 0)
    except FileNotFoundError:
        return 0.0          # ffprobe yoksa süre bilinmez, iş yine de sürsün
    except Exception:
        return 0.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--metin", default="")
    ap.add_argument("--dosya", default="")
    ap.add_argument("--ses", default="tr-TR-AhmetNeural")
    ap.add_argument("--hiz", default="+0%")
    ap.add_argument("--ad", default="", help="çıktı klasörünün adı")
    args = ap.parse_args()

    ham = Path(args.dosya).read_text(encoding="utf-8") if args.dosya else args.metin
    if not ham.strip():
        bildir("error", "Ses", "Metin boş")
        sys.exit(1)

    # Boş satır = yeni bölüm. Sahne sahne yerleştirmek için ayrı dosyalar gerekiyor.
    bolumler = [hazirla(b) for b in re.split(r"\n\s*\n", ham) if b.strip()]

    tr = datetime.now(timezone.utc).astimezone(timezone(timedelta(hours=3)))
    klasor = CIKTI / (args.ad.strip() or tr.strftime("%Y-%m-%d_%H%M"))
    klasor.mkdir(parents=True, exist_ok=True)

    hiz = args.hiz if args.hiz.strip().endswith("%") else "+0%"
    uretilen, toplam = [], 0.0

    for i, bolum in enumerate(bolumler, start=1):
        hedef = klasor / f"{i:02d}.mp3"
        if not seslendir(bolum, args.ses, hiz, hedef):
            # Boş dosya ve boş klasör geride kalmasın; depoya sızıyor.
            hedef.unlink(missing_ok=True)
            for p in sorted(klasor.glob("*")):
                p.unlink(missing_ok=True)
            klasor.rmdir()
            bildir("error", "Ses", f"{i}. bölüm üretilemedi — üç deneme de başarısız")
            sys.exit(1)
        s = sure(hedef)
        toplam += s
        uretilen.append(hedef)
        bildir("notice", f"Bölüm {i}", f"{s:.1f} saniye · {len(bolum)} karakter · {bolum[:90]}")

    if len(uretilen) > 1:
        liste = klasor / "liste.txt"
        liste.write_text("".join(f"file '{p.name}'\n" for p in uretilen), encoding="utf-8")
        tam = klasor / "tam.mp3"
        try:
            subprocess.run(["ffmpeg", "-nostdin", "-y", "-loglevel", "error", "-f", "concat",
                            "-safe", "0", "-i", str(liste), "-c", "copy", str(tam)], check=False)
        except FileNotFoundError:
            # ffmpeg yoksa bölümler yine kullanılabilir; birleştirme şart değil.
            bildir("warning", "Birleştirme", "ffmpeg bulunamadı, bölümler ayrı kaldı")
        liste.unlink(missing_ok=True)
        if tam.exists():
            bildir("notice", "Birleştirildi", f"tam.mp3 · {sure(tam):.1f} saniye")

    bildir("notice", "Bitti",
           f"{len(uretilen)} bölüm · toplam {toplam:.1f} saniye · ses {args.ses} · hız {hiz}")

    ozet = os.environ.get("GITHUB_STEP_SUMMARY")
    if ozet:
        depo = os.environ.get("GITHUB_REPOSITORY", "")
        dal = os.environ.get("GITHUB_REF_NAME", "main")
        with open(ozet, "a", encoding="utf-8") as f:
            f.write(f"## Seslendirme hazır\n\n")
            f.write(f"**{len(uretilen)} bölüm · {toplam:.1f} saniye · {args.ses}**\n\n")
            f.write("| Dosya | Süre | İndir |\n|---|---|---|\n")
            for p in uretilen + ([klasor / "tam.mp3"] if (klasor / "tam.mp3").exists() else []):
                bag = f"https://github.com/{depo}/raw/{dal}/seslendirme/{klasor.name}/{p.name}"
                f.write(f"| {p.name} | {sure(p):.1f} sn | [indir]({bag}) |\n")


main()
