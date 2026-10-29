# Ücretsiz yerel medya paketi — 29 Ekim 2026

Bu ekleme **7 yeni repo kaydı**, mevcut faster-whisper kaydının güncellenmesi, **8 sabit kaynak referansı** ve **3 seçilmiş animasyon skill'i** içerir. Yerel kurulum yalnızca koleksiyon içindeki `.agents/skills/` ve `.claude/skills/` klasörlerini kapsar. Kişisel/global skill dizinleri değişmez.

Uygulamalar, Python/Node bağımlılıkları ve ses modelleri kurulmaz. İleride bir video veya ses görevi geldiğinde yalnızca gereken motor ayrıca hazırlanır. Kurulu skill, çalışan video/ses motoru demek değildir.

| Kaynak | Amaç | Lisans / önemli koşul |
|---|---|---|
| [Motion Canvas](https://github.com/motion-canvas/motion-canvas) | Sesle eşzamanlı yazı ve vektör animasyonu | MIT; program ve FFmpeg exporter bağımlılıkları ayrıca gerekir |
| [Kinetic Typography](https://github.com/iart-ai/kinetic-typography-skills) | Başlık, harf/kelime vurgusu ve yazı geçişi | MIT; yerel font/CSS yolu tercih edilir |
| [Lower Thirds](https://github.com/iart-ai/lower-thirds-skills) | Şeffaf isim, iletişim ve fiyat bilgi katmanları | MIT; Node, Chrome ve FFmpeg gerekir; renderer henüz test edilmedi |
| [Map Animation](https://github.com/iart-ai/map-animation-skills) | Konum, rota ve bölge animasyonu | MIT skill; ücretsiz akışta yerel GeoJSON/SVG yolu seçilir |
| [whisper.cpp](https://github.com/ggml-org/whisper.cpp) | Yerel Türkçe transkripsiyon ve altyazı | MIT; çok dilli base/small modeller ayrıca indirilir; `.en` modeli seçilmez |
| [LosslessCut](https://github.com/mifi/lossless-cut) | Hızlı kesme ve birleştirme | GPL-2.0; resmî GitHub manuel indirmesi ücretsiz, mağaza sürümleri farklı olabilir |
| [Chatterbox Multilingual](https://github.com/resemble-ai/chatterbox) | Ses örneğiyle Türkçe metin seslendirme | MIT; çok dilli model gerekir, Nano İngilizce olarak listelenir; hız/benzerlik denenmedi |
| [faster-whisper](https://github.com/SYSTRAN/faster-whisper) | Alternatif yerel altyazı motoru | MIT; mevcut katalog kaydı korundu ve yenilendi; Python/model bağımlılıkları ayrıca gerekir |

## Ücretsiz çalışma seçimi

Bu eklemelerin amacı harici medya aboneliği, üretim kredisi veya ücretli API çağrısı kullanmadan çalışmaktır. Bu belge ve manifest bir ağ güvenlik duvarı değildir; ajan, seçtiği motoru ve komutu görev öncesinde kontrol eder.

- Yerel motor eksikse durup eksik bağımlılığı bildir; ücretli servise otomatik geçme.
- Kayıt ve fotoğrafları izin verilmeden bir bulut servisine yükleme. Font ve varlıklar için uygun lisanslı yerel dosyaları tercih et.
- Map Animation içindeki After Effects yolu ücretli yazılım gerektirebilir; ücretsiz görevde GeoJSON/SVG yolunu kullan.
- Remotion kullanılacaksa onun lisansı ayrıca geçerlidir: [birey ve toplam en fazla 3 kişilik ekip/şirket koşulu](https://www.remotion.dev/docs/license/faq). MIT lisanslı Motion Canvas bu koşula alternatif olarak kataloglandı.
- `iart-ai/b-roll-skills` bu pakete alınmadı: API anahtarı varsa ElevenLabs'i otomatik önceliklendiren kod ve Windows'a uygun olmayan `which` araması bulundu. Ücretsiz yerel uyarlama yapılmadan etkinleştirilmez.
- XTTS-v2'nin ticari olmayan model/çıktı lisansı ve bazı Auto-Editor dağıtımlarındaki ücretli sınırlar nedeniyle bu iki araç ücretsiz varsayılan listeye alınmadı.

## Kullanım

Bu koleksiyon klasöründe açılan yeni Claude Code veya Codex oturumunda `kinetic-typography`, `lower-thirds`, `map-animation` becerileri keşfedilebilir. Kod üretme yönergeleri hazırdır; çalışma bağımlılıkları göreve göre kontrol edilir. Örnek istek: “Bu fotoğraflardan yerel araçlarla 30 saniyelik dikey tanıtım hazırla; hareketli başlık ve iletişim kutusu ekle.”

```powershell
python skills/refs-catalog/scripts/route.py search --category free-media --query ""
python scripts/agent_bridge.py inspect --repository iart-ai/kinetic-typography-skills --skill kinetic-typography
```

Başka projeye yalnızca istenen beceriyi kur:

```powershell
python scripts/agent_bridge.py plan --repository iart-ai/lower-thirds-skills --skill lower-thirds --project C:/projem --platform both
python scripts/agent_bridge.py install --repository iart-ai/lower-thirds-skills --skill lower-thirds --project C:/projem --platform both --apply
```

Kinetic Typography ve Map Animation paketlerinin kökte duran Bash doğrulama yardımcıları `.sources/` referansında korunur. Skill klasörüne kopyalanmaz; Windows'ta bu Bash yardımcılarını doğrudan çağırmak yerine uygun yerel araçları ve mevcut tarayıcı kullanım kurallarını uygula. Kaynak dosyalarının varlığı bunları çalıştırma yetkisi vermez.

## GitHub'dan yeniden kullanma

Koleksiyonun mevcut yayın biçimi korundu: GitHub'da katalog, kaynak URL'leri, sabit commit/blob kimlikleri, lisans notları ve kurulum araçları bulunur. `.sources/` klonları, yerel upstream skill kopyaları, ses modelleri ve uygulama bağımlılıkları Git'e eklenmez. Yeni makinede koleksiyonu klonladıktan sonra, seçilen kaynakları getir:

```powershell
$media = Get-Content catalog/free-media.json -Raw | ConvertFrom-Json
foreach ($repo in $media.repositories) {
    python scripts/sync_sources.py --root . --repo $repo
}
python scripts/agent_bridge.py install --repository iart-ai/kinetic-typography-skills --skill kinetic-typography --project . --platform both --apply
python scripts/agent_bridge.py install --repository iart-ai/lower-thirds-skills --skill lower-thirds --project . --platform both --apply
python scripts/agent_bridge.py install --repository iart-ai/map-animation-skills --skill map-animation --project . --platform both --apply
```

Bu adımlar sabit kaynakları ve seçilmiş skill klasörlerini getirir; ücretli servis başlatmaz ve model ağırlığı kurmaz. Kaynak uygulamaların tam koduna kilitlenmiş GitHub bağlantısından ulaşılır.

## Doğrulama sınırı

Seçilen 37 referans dosyası Git blob kimlikleriyle kontrol edildi. Üç SKILL.md ve ilgili yardımcıları statik olarak incelendi; lisans dosyaları korundu. Skill kurulumları ve katalog testleri ayrıca doğrulanır. Gerçek medya render'i veya Türkçe ses klonlama testi yapılmadığı için motorların bu bilgisayarda çalıştığı iddia edilmez. Model indirmesi/çalıştırması ayrı görevdir.
