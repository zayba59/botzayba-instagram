# BotZayba – Otomatik Günlük Instagram Paylaşımı

Her gün saat **18:00'de (Türkiye saati)**:
1. O günün BotZayba reklamını hazırlar (Gemini yapay zekâsı ile yeni metin, yoksa hazır 30 içerikten sıradaki),
2. Logolu 1080×1350 reklam görselini tasarlar,
3. Instagram'a paylaşır.

Tamamen **ücretsiz** çalışır (GitHub Actions + Instagram resmi API + Gemini ücretsiz kotası).

---

## Kurulum (tek seferlik, ~30 dakika)

### 1) Instagram ve Facebook hazırlığı
1. Instagram → Ayarlar → **Hesap türü ve araçlar** → **Profesyonel hesaba geç** (İşletme veya İçerik Üreticisi).
2. Bir **Facebook Sayfası** oluştur (ör. "BotZayba") ve Instagram hesabını bu sayfaya bağla
   (Facebook Sayfası → Ayarlar → Bağlı hesaplar → Instagram).

### 2) Meta geliştirici uygulaması ve erişim anahtarı
1. https://developers.facebook.com → giriş yap → **Uygulamalarım → Uygulama oluştur**.
   Tür olarak **İşletme (Business)** seç.
2. Uygulamaya **Instagram** ürününü ekle.
3. **Araçlar → Graph API Explorer** sayfasını aç:
   - Sağ üstte uygulamanı seç.
   - "İzin ekle" kısmından şunları ekle:
     `instagram_basic`, `instagram_content_publish`, `pages_show_list`, `pages_read_engagement`, `business_management`
   - **Generate Access Token** → Facebook ile onayla.
4. Çıkan anahtarı **Access Token Debugger** (https://developers.facebook.com/tools/debug/accesstoken/)
   sayfasına yapıştır → en altta **Extend Access Token** → uzun süreli anahtarı kopyala.
5. Graph API Explorer'a bu uzun süreli anahtarı yapıştır ve şu sorguyu çalıştır:
   `me/accounts`
   → Sayfanın altındaki `access_token` değeri **süresi dolmayan sayfa anahtarındır** → bu `IG_ACCESS_TOKEN`.
   → Aynı yerdeki `id` sayfa kimliğidir.
6. Şu sorguyu çalıştır (SAYFA_ID yerine yukarıdaki id):
   `SAYFA_ID?fields=instagram_business_account`
   → Çıkan `id` → bu `IG_USER_ID`.

### 3) Gemini anahtarı (isteğe bağlı ama önerilir)
https://aistudio.google.com → **Get API key** → **Create API key** → kopyala.
Bu anahtar olursa program her gün yeni, benzersiz bir reklam yazar.
Olmazsa hazır 30 içeriği sırayla paylaşır (30 günde bir başa döner).

### 4) GitHub
1. https://github.com → **New repository** → ad: `botzayba-instagram` → **Public** seç
   (Instagram görseli herkese açık bir adresten çekmek zorunda; zaten Instagram'da yayınlanacak içerikler).
2. Bu klasördeki tüm dosyaları depoya yükle (**Add file → Upload files**; `.github` klasörü dahil).
3. Depoda **Settings → Secrets and variables → Actions → New repository secret** ile şunları ekle:

   | Ad | Değer |
   |---|---|
   | `IG_USER_ID` | 2. adımdaki Instagram hesap kimliği |
   | `IG_ACCESS_TOKEN` | 2. adımdaki sayfa anahtarı |
   | `GEMINI_API_KEY` | 3. adımdaki anahtar (isteğe bağlı) |

4. **Actions** sekmesi → "Günlük Instagram paylaşımı" → **Run workflow** ile hemen bir deneme yap.
   Yeşil tik çıkarsa Instagram'ı kontrol et. Bundan sonra her gün kendiliğinden paylaşır.

---

## Ayarlar
- **Paylaşım saati:** `.github/workflows/daily-post.yml` içindeki `cron: "0 15 * * *"` (UTC).
  Türkiye saati = UTC + 3. Örn. 12:00 için `"0 9 * * *"`.
- **Kullanıcı adı, uyarı metni, hashtag'ler:** `content.json` → `brand`.
- **Hazır içerikler:** `content.json` → `posts` (ekle, sil, düzenle).
- **Logo:** `assets/logo_white.png`.

## Bilgisayarda deneme
```bash
pip install Pillow
python scripts/generate.py --preview   # tüm içeriklerin görselleri preview/ klasörüne
```

## Önemli notlar
- İçerikler bilerek **kazanç vaadi içermez**; yapay zekâ böyle bir ifade yazarsa program onu reddedip hazır içeriğe geçer.
  Instagram ve Türkiye'deki kripto düzenlemeleri açısından bu önemlidir.
- GitHub, 60 gün boyunca hiç işlem olmayan depolarda zamanlanmış görevleri durdurabilir.
  Program her gün depoya kayıt eklediği için normalde sorun olmaz.
