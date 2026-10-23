"""Instagram erişim anahtarı alma yardımcısı (Instagram Login — Facebook Sayfası gerekmez).

Bilgisayarınızda çalıştırın:
    python scripts/token.py

Sizden Instagram App ID, App Secret ve Redirect URI ister; sonra adım adım yönlendirir.
Sonunda GitHub'a gireceğiniz IG_ACCESS_TOKEN ve IG_USER_ID değerlerini yazar.
"""
import json
import sys
import urllib.parse
import urllib.request

SCOPES = "instagram_business_basic,instagram_business_content_publish"


def get(url):
    try:
        with urllib.request.urlopen(url, timeout=60) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        sys.exit(f"\nHATA: {e.read().decode(errors='replace')[:600]}")


def post(url, fields):
    data = urllib.parse.urlencode(fields).encode()
    try:
        with urllib.request.urlopen(urllib.request.Request(url, data=data), timeout=60) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        sys.exit(f"\nHATA: {e.read().decode(errors='replace')[:600]}")


def ask(label):
    while True:
        v = input(f"{label}: ").strip()
        if v:
            return v


def main():
    print("=" * 62)
    print(" BotZayba — Instagram erişim anahtarı alma sihirbazı")
    print("=" * 62)
    print("\nBu bilgiler Meta uygulamanızın Instagram > API setup with Instagram")
    print("login bölümündedir.\n")

    app_id = ask("1) Instagram App ID")
    app_secret = ask("2) Instagram App Secret")
    redirect = ask("3) Redirect URI (Meta'ya yazdığınızın AYNISI)").rstrip("/") + "/"

    auth = "https://www.instagram.com/oauth/authorize?" + urllib.parse.urlencode({
        "client_id": app_id, "redirect_uri": redirect,
        "response_type": "code", "scope": SCOPES})

    print("\n" + "-" * 62)
    print("4) Aşağıdaki adresi kopyalayıp tarayıcıda açın ve izin verin:\n")
    print(auth)
    print("\n5) İzin verince başka bir sayfaya yönlendirileceksiniz.")
    print("   O sayfanın ADRES ÇUBUĞUNDAKİ adresin tamamını kopyalayın.")
    print("-" * 62 + "\n")

    raw = ask("6) Yönlendirilen adresi buraya yapıştırın")
    qs = urllib.parse.parse_qs(urllib.parse.urlparse(raw).query)
    code = (qs.get("code", [raw])[0]).split("#")[0]
    if not code:
        sys.exit("Adreste 'code=' bulunamadı. Adresin tamamını kopyaladığınızdan emin olun.")

    print("\nAnahtar alınıyor...")
    short = post("https://api.instagram.com/oauth/access_token", {
        "client_id": app_id, "client_secret": app_secret,
        "grant_type": "authorization_code", "redirect_uri": redirect, "code": code})

    long_ = get("https://graph.instagram.com/access_token?" + urllib.parse.urlencode({
        "grant_type": "ig_exchange_token", "client_secret": app_secret,
        "access_token": short["access_token"]}))

    me = get("https://graph.instagram.com/v23.0/me?" + urllib.parse.urlencode({
        "fields": "user_id,username", "access_token": long_["access_token"]}))

    print("\n" + "=" * 62)
    print(" BAŞARILI — Hesap: @" + str(me.get("username", "?")))
    print("=" * 62)
    print("\nGitHub > Settings > Secrets and variables > Actions bölümüne ekleyin:\n")
    print("  IG_ACCESS_TOKEN =")
    print("  " + long_["access_token"])
    print("\n  IG_USER_ID =")
    print("  " + str(me.get("user_id", "")))
    print(f"\nBu anahtar {int(long_.get('expires_in', 0)) // 86400} gün geçerli;")
    print("program her gün otomatik olarak süresini uzatacak.")
    print("\nANAHTARI KİMSEYLE PAYLAŞMAYIN — Instagram hesabınızın şifresi gibidir.")


if __name__ == "__main__":
    main()
