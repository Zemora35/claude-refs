# Claude Refs — kategori bazında kaynak ve skill koleksiyonu

GitHub: [Zemora35/claude-refs](https://github.com/Zemora35/claude-refs).

İlk doğrulama **2026-10-27**, son ekleme kontrolü **2026-10-29**: **55 kategori**, **188 repo kaydı**, **44 sabitlenmiş kaynak**, **1056 SKILL.md yolu**, **106 seçilmiş beceri** ve **1 harici veri koleksiyonu**.

Bu koleksiyon kaynak bulmayı ve doğru aracı seçmeyi kolaylaştırır. Seçimler popülerlik, güncellik, lisans bilgisi ve kullanım amacıyla değerlendirilir. Üçüncü taraf kaynak kodları otomatik çalıştırılmaz; upstream beceriler yalnızca açık kurulum isteğiyle seçilerek kurulur. Projeye eklenen özgün `refs-catalog` yönlendiricisi Claude Code ve Codex tarafından keşfedilebilir.

| İhtiyaç | Dosya |
|---|---|
| Ücretsiz yerel medya eklemeleri (29 Ekim) | [UCRETSIZ_MEDYA.md](UCRETSIZ_MEDYA.md) |
| 28 Ekim eklemeleri ve yerel kurulum sınırları | [EKLENEN_KAYNAKLAR.md](EKLENEN_KAYNAKLAR.md) |
| Kategoriler ve repo karşılaştırmaları | [KATALOG.md](KATALOG.md) |
| İşe göre skill seçimi | [SKILL_REHBERI.md](SKILL_REHBERI.md) |
| Claude Code/Codex kurulumu ve kullanımı | [AGENT_KULLANIMI.md](AGENT_KULLANIMI.md) |
| ChatGPT araştırma → Claude kodlama aktarımı | [ARASTIRMA_KOD_AKISI.md](ARASTIRMA_KOD_AKISI.md) |
| Doğrulanan ajan davranışları ve test sınırları | [UYUMLULUK_RAPORU.md](UYUMLULUK_RAPORU.md) |
| Puanın anlamı ve kapsam | [YONTEM.md](YONTEM.md) |
| Yerel kaynakların inceleme durumu | [SOURCE_REVIEW.md](SOURCE_REVIEW.md) |
| GitHub'a taşınacak bölüm | [GITHUB_YUKLEME.md](GITHUB_YUKLEME.md) |
| Kaynaklar ve lisans sınırları | [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) |

## Kullanım

Python 3.10+ ve Git yeterlidir; ek Python paketi gerekmez.

Koleksiyonu klonlayıp proje klasöründe oturum açınca Claude Code'da `/refs-catalog`, Codex'te `$refs-catalog` ile yönlendiriciyi çağırabilirsin. Başka projelere yalnızca yönlendiriciyi eklemek veya tek bir upstream beceriyi seçmek için [ajan kullanım rehberini](AGENT_KULLANIMI.md) izle.

Araştırma/kodlama aktarımını tüm yerel proje sohbetlerinde çağırmak için [kişisel `research-to-claude` kurulumunu](ARASTIRMA_KOD_AKISI.md#her-yerel-sohbette-çağırma) kullan. Başlatma aktif sohbetin projesiyle eşleşir; önceki projenin kaydı kullanılmaz.

Aktarım aracı ayrıca onaylı testleri bağımsız çalıştırır, `status` ile görev/dal/değişiklik/kalan iş özetini gösterir ve gerçek test hatalarından `draft-correction` taslağı üretir. Düzeltme çalıştırması açık başlatma isteği gerektirir. Ayrıntılar [akış rehberinde](ARASTIRMA_KOD_AKISI.md).

İsteğe bağlı `--enable-research` ile Claude Code kodlama sırasında Codex CLI'a kaynaklı araştırma sorabilir. Göreve bağlı tek MCP aracı, seçilmiş bağlam kopyaları, iki çağrı/süre sınırı ve süreli önbellek kullanılır. Araştırmacı komut çalıştırmaz veya kod değiştirmez. Canlı doğrulama ve kullanım sınırları [uyumluluk raporunda](UYUMLULUK_RAPORU.md) açıklanır.

```powershell
python scripts/catalog.py categories
python scripts/catalog.py search postgres
python scripts/catalog.py search --category bim
python scripts/catalog.py search terraform --skills
python scripts/catalog.py validate
python scripts/catalog.py refresh
```

`refresh` varsayılan olarak yalnızca değişiklikleri gösterir; `--apply` metadata JSON'unu günceller. Raporları yeniden oluşturmak için `python scripts/catalog.py render` çalıştırılır. GitHub hız sınırında durur. Token gerekiyorsa yalnızca ortamdan okunur; dosyaya yazılmaz.

Yeni kaynakların sabit commit'lerini yerel `.sources/` alanına almak için:

```powershell
python scripts/sync_sources.py --root .
```

Yeni eklenen kaynaklarda kilitteki `sparse_paths` yalnızca belgeler ve eksiksiz skill klasörlerini seçer; büyük medya, LFS varlıkları ve uygulama bağımlılıkları indirilmez. NVIDIA veri kümesi bu komutla indirilmez.

Bu komut yerel referans indirir; skill/global paket/MCP kurulumu yapmaz. Mevcut kaynakları değiştirmez. Yeni kaynaklardaki kodlar çalıştırılmaz. Yalnızca belirli bir kaynak için `--repo owner/repo` kullanılabilir. Yeniden indirme ve otomatik güncelleme yapılmaz; mevcut commit farklıysa hata raporlanır.

## Kapsam

Yazılım, AI/ML, MCP, tasarım, mobil, test, güvenlik, DevOps, veri, otomasyon, ofis, bilim, BIM/IFC, yapı mühendisliği, GIS, robotik, oyun/3D, medya, finans, ürün, pazarlama, CRM/ERP, hukuk teknolojisi, kariyer, IoT, ses ve çeviri.

Bu bir kürasyondur; GitHub'ın tamamını kapsayan kesin bir 'en iyi' sıralaması değildir. Mevcut 33 referans klasörü korunur. Önceden kurulu beceriler isim ve sağlayıcı bazında kaydedilir; özel yerel talimatlar yayımlanan pakete kopyalanmaz.

## Önceki yerel genişletme (27–28 Ekim)

22 yeni kaynak eklendi; 24 kaynak sabit commit'leriyle kontrol edildi. 12.532 dosya statik envantere alındı ve 1.022 SKILL.md kimliği doğrulandı. İki beceri etkinleştirmeye kapalı işaretlendi. İnceleme sınırlamaları ve kaynak bazında notlar [SOURCE_REVIEW.md](SOURCE_REVIEW.md) içindedir.

## Ücretsiz yerel medya — 29 Ekim

7 yeni repo ve mevcut faster-whisper kaydı, 3 animasyon skill’i (iki ajan için 6 yerel kopya) eklendi. Uygulama veya ses modeli kurulmaz. [Kullanım, ücretsiz yollar ve GitHub’dan yeniden kurma](UCRETSIZ_MEDYA.md).
