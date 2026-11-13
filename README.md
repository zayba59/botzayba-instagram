# BotZayba – Otomatik Günlük Instagram Paylaşımı

Her gün **Türkiye saati 09.00'dan sonra**, GitHub Actions'ın çalıştırdığı ilk uygun denemede (GitHub yoğunluğuna göre gecikebilir):
1. O günün BotZayba reklamını hazırlar (Gemini yapay zekâsı ile yeni metin, yoksa hazır 30 içerikten sıradaki),
2. Logolu 1080×1350 reklam görselini tasarlar,
3. Instagram'a paylaşır.

GitHub Actions + Instagram resmi API + Gemini kullanır. **GitHub Actions ve diğer servislerin kullanım kotaları geçerlidir; ücretsiz kullanım garanti değildir.**

---

## Kurulum (tek seferlik)

Facebook **Sayfası** gerekmez. Sadece Meta geliştirici paneline girmek için bir Facebook
hesabı gerekir (Instagram'ın resmi API'si Meta'ya ait).

### 1) Instagram'ı profesyonel hesaba çevirin
Instagram → Profil → ☰ → **Hesap türü ve araçlar** → **Profesyonel hesaba geç** →
kategori seçin → **İşletme**. (Zorunludur; kişisel hesaplar API ile paylaşım yapamaz.)

### 2) Meta uygulaması oluşturun
1. https://developers.facebook.com → Facebook hesabınızla giriş yapın.
2. **Uygulamalarım → Uygulama oluştur**. Ad: `BotZayba Poster`.
3. Kullanım alanı sorulursa **Diğer / Other** → tür: **İşletme / Business** → **Oluştur**.
4. Sol menüden **Instagram** ürününü ekleyin ve
   **API setup with Instagram login** bölümünü açın.
5. **3. Set up Instagram business login** → **Business login settings**:
   - **Redirect URI** kutusuna açılabilen bir https adresi yazın. Kendi siteniz yoksa
     `https://zayba-download.vercel.app/` gibi size ait herhangi bir adres olur;
     bu sayfa sadece anahtarı almak için bir kez kullanılacak.
   - Kaydedin.
6. Aynı sayfadaki **Instagram App ID** ve **Instagram App Secret** değerlerini not edin.

### 3) Erişim anahtarını alın
Bilgisayarınızda proje klasöründe:
```bash
python scripts/token.py
```
Program sırayla App ID, App Secret ve Redirect URI'yi ister, size bir bağlantı verir.
Bağlantıyı tarayıcıda açıp Instagram ile izin verirsiniz; yönlendirildiğiniz adresi
kopyalayıp programa yapıştırırsınız. Sonunda ekrana **IG_ACCESS_TOKEN** ve
**IG_USER_ID** değerleri yazılır.

### 4) Gemini anahtarı (isteğe bağlı ama önerilir)
https://aistudio.google.com → **Get API key** → **Create API key**.
Bu anahtar varsa program her gün yeni bir reklam yazar; yoksa hazır 30 içeriği sırayla kullanır.

### 5) GitHub Secrets
Depoda **Settings → Secrets and variables → Actions → New repository secret**:

| Ad | Değer | Zorunlu |
|---|---|---|
| `IG_ACCESS_TOKEN` | 3. adımdaki anahtar | evet |
| `IG_USER_ID` | 3. adımdaki kimlik | evet |
| `GEMINI_API_KEY` | 4. adımdaki anahtar | hayır |
| `GH_TOKEN` | GitHub kişisel erişim anahtarı (aşağıya bakın) | hayır |

**GH_TOKEN nedir?** Instagram anahtarı 60 günde bir yenilenmek zorundadır. Bu anahtarı
eklerseniz program yenilemeyi kendisi yapar ve hiç uğraşmazsınız. Eklemezseniz süre
dolmaya yaklaşınca GitHub size uyarı e-postası gönderir, `scripts/token.py` ile yeni
anahtar alıp `IG_ACCESS_TOKEN` değerini elle güncellersiniz.

Oluşturmak için: GitHub → sağ üst profil → **Settings** → en altta **Developer settings**
→ **Personal access tokens → Fine-grained tokens** → **Generate new token**.
Repository access: sadece `botzayba-instagram`. Permissions → Repository permissions →
**Secrets: Read and write**. Süreyi **No expiration** yapın.

### 6) Çalıştırın
**Actions** sekmesi → **Günlük Instagram paylaşımı** → **Run workflow**.
Yeşil tik çıkınca Instagram'ı kontrol edin. Bundan sonra her gün kendiliğinden paylaşır.

## Ayarlar
- **Paylaşım zamanı:** `.github/workflows/daily-post.yml` içindeki birden fazla `schedule` cron'u, Türkiye saati 09.00 sonrasında deneme yapar. GitHub zamanlanmış işleri geciktirebilir; **sabit 09.00 paylaşım garantisi yoktur**.
- **Günde bir kez kontrolü:** `.gunluk-son` dosyası, o gün tamamlanan yayını işaretler. Gün içindeki ek zamanlanmış denemelerde `post` işinin atlanması, daha önce paylaşım yapıldıysa normaldir.
- **Doğrulama:** Actions ekranında sadece genel yeşil sonuca değil, aynı günün `post` işinin ve `Instagram'a paylaş` adımının başarılı olup olmadığına bakılmalıdır.
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

## Depolama ve güvenli bakım

- Günlük video üretimi, YouTube deposunun `gunluk-video.yml` işinden Instagram deposundaki `reels/` klasörüne dosya gönderir. Bu iş **çalışma ağacında** en yeni 7 `.mp4` dosyasını tutacak şekilde tasarlanmıştır.
- Git'te bir video dosyasının son commit'ten silinmesi, o dosyanın eski Git geçmişindeki kopyalarını otomatik olarak kaldırmaz. Dolayısıyla depo boyutu video paylaşımı devam ettikçe artabilir.
- `tanitim/` klasöründeki videoları veya `reels/` geçmişini **otomatik temizlemeyin**: aktif URL'ler, yayın bağlantıları ve geçmiş kayıtları etkilenebilir. Önce güvenli arşivleme/taşıma planı, bağlantı kontrolleri ve geri dönüş yöntemi hazırlanmalıdır.
- Her ay GitHub'da **Settings → Billing and licensing / Billing** üzerinden Actions dakikalarını ve artifact/cache kullanımını kontrol edin. Depo boyutu, hesabın toplam Actions kullanım yüzdesi değildir.
- Bu belge yalnızca mevcut işleyişi açıklar; yayımlama kodunda, zamanlamada ve Git geçmişinde değişiklik yapmaz.
