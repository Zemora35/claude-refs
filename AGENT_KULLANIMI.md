# Claude Code ve Codex ile kullanım

Bu sürüm tek bir katalog yönlendiricisini iki ajanın proje konumunda sunar:

- Claude Code: `.claude/skills/refs-catalog/SKILL.md`.
- Codex: `.agents/skills/refs-catalog/SKILL.md`.
- Bakımı yapılan asıl kaynak: `skills/refs-catalog/`.

Koleksiyonu klonlayıp bu klasörde bir oturum açtığında yönlendirici proje becerisi olarak keşfedilebilir. Claude Code'da `/refs-catalog`, Codex'te `$refs-catalog` ile açıkça çağırabilirsin. Diğer projelerin veya başka bilgisayarların otomatik erişimi yoktur. Claude'un web/Cowork sürümlerine GitHub'a yayınlamak tek başına beceri yüklemez; bu paket yerel Claude Code ve Codex proje akışı için hazırlanmıştır.

## Katalogda ara

Katalog kökünde, Python 3.10+ ile:

```powershell
python scripts/agent_bridge.py doctor
python scripts/agent_bridge.py search --query postgres --category database
python scripts/agent_bridge.py search --query terraform --all-skills
python scripts/agent_bridge.py inspect --repository supabase/agent-skills --skill supabase-postgres-best-practices
```

Varsayılan arama 81 seçilmiş beceriyi kapsar; `--all-skills` tüm indeks içinde arar. Engelli bir kaynağın arama sonucunda görünmesi kurulum izni değildir. `inspect`, bilinen gereksinimleri ve yerel kaynak durumunu gösterir. Eksik kaynağı kendi kendine indirmez; kullanıcının istediği kaynak için açık indirme komutunu verir.

## Başka projede kullan

Katalog kökünden hedef projenin mevcut dizinini belirt:

```powershell
python scripts/agent_bridge.py install-router --project ../my-project --platform both
python scripts/agent_bridge.py install-router --project ../my-project --platform both --apply
```

İlk komut planı gösterir; ikinci komut yalnızca yönlendiriciyi kopyalar. `--platform claude` veya `--platform codex` ile tek ajan seçilebilir. Hedef proje altında yerel bir katalog konumu kaydı oluşur. Katalog taşınırsa konumu yeniden yapılandır; bu yerel kayıt GitHub'a taşınmaz. Kaydı kendi projenin `.gitignore` dosyasına ekleyebilirsin: `**/refs-catalog/references/catalog-location.json`.

## Seçili bir upstream beceriyi kur

Örnek, modül/arayüz tasarımı becerisini yalnızca belirtilen projeye ekler:

```powershell
python scripts/agent_bridge.py inspect --repository mattpocock/skills --skill codebase-design --show-content
python scripts/agent_bridge.py plan --repository mattpocock/skills --skill codebase-design --project ../my-project --platform both
python scripts/agent_bridge.py install --repository mattpocock/skills --skill codebase-design --project ../my-project --platform both --apply
```

Kaynak yerelde yoksa önce `inspect` çıktısındaki sabit commit indirme komutunu çalıştır. Kullanıcının görevi arama ise kurulum yapma. Kurulum istenmişse seçilen SKILL.md'yi, ilgili yürütülebilir yardımcıları ve lisansları incele.

Katalog klasörü ve hedef proje, ajanın izin verilen çalışma alanlarında olmalıdır. Bir sandbox okuma engeli varsa izinleri atlatmak yerine doğru proje/çalışma alanı erişimini yapılandır. `$ARGUMENTS` gibi Claude'a özgü değişkenler Claude kurulumunda korunur; Codex veya ortak kurulumda elle uyarlama gerektirdiği bildirilir.

Araç şu kuralları uygular:

- Engelli iki becerinin kurulumu reddedilir.
- Seçilen kaynağın commit'i ve SKILL.md blob kimliği doğrulanır.
- Kopyalanacak yardımcılar Git ağacına karşı kontrol edilir; değiştirilmiş, eksik veya izlenmeyen dosyalar reddedilir.
- Hook, dinamik kabuk genişletmesi ve otomatik alt ajan davranışı ayrı uyarlama gerektirir. Codex için Claude'a özgü çalışma metadata'sı ayrıca kontrol edilir.
- Var olan başka bir becerinin üzerine yazılmaz. Aynı yönetilen kurulum değişmemişse tekrar çağrı etkisizdir.
- Beceri klasörü, üst dizin lisans bildirimleri ve kaynak/commit/dosya kimliklerini içeren `.INSTALLED_FROM.json` korunur.

Paket, Python/Node kütüphanesi veya sistem paketi yüklemez; API anahtarını okumaz, hesap açmaz ve ücretli servis başlatmaz. Kurulumun başarılı olması becerinin bütün işlevlerinin mevcut ortamda çalıştığını kanıtlamaz.

## Gereksinim ve test kapsamı

`compatibility-profiles.json` bilinen Python modülleri, CLI'lar ve servis koşullarını kaydeder. Kontroller komutu çalıştıran Python ortamına aittir; başka bir sanal ortamı doğrulamaz. Profili olmayan beceriler için elle ortam incelemesi gerekir. İşletim sistemine özgü betikler, tarayıcı ikilileri, model ağırlıkları, özel MCP bağlantıları ve servis yetkileri görev bazında kontrol edilmelidir.

Deterministik testler:

```powershell
python scripts/catalog.py validate
python -m unittest discover -s tests -v
```

Güncel ajan denemeleri ve sınırları [UYUMLULUK_RAPORU.md](UYUMLULUK_RAPORU.md) içinde tutulur. Bunlar 1.022 upstream becerinin tamamının çalıştırıldığı anlamına gelmez.

Resmî kaynaklar: [Claude Code skill konumları](https://code.claude.com/docs/en/skills), [Codex skill keşfi](https://learn.chatgpt.com/docs/build-skills).

## Ücretsiz yerel medya

`free-media` kategorisi ve [medya rehberi](UCRETSIZ_MEDYA.md) yeni yerel üretim adaylarını içerir. Ücretli servise otomatik geçme; eksik motoru bildir. Koleksiyondaki üç yeni skill’in bulunması video/ses motorunun hazır olduğu anlamına gelmez.
