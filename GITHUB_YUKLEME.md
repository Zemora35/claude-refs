# GitHub'a yükleme

Katalog kökündeki `.gitignore` yalnızca bu çalışmanın ürettiği belge, JSON ve betikleri izlemeye açar. Mevcut repo kopyaları, `.sources/`, iç içe `.git` dizinleri, kişisel ayarlar ve yerel çalışma çıktıları kapsam dışındadır. Üçüncü taraf kodunu kendi lisansımızla yeniden yayımlamayız.

## Yüklenecek dosyalar

`README.md`, `KATALOG.md`, `SKILL_REHBERI.md`, `YONTEM.md`, `SOURCE_REVIEW.md`, `GITHUB_YUKLEME.md`, `SECURITY.md`, `THIRD_PARTY_NOTICES.md`, `LICENSE`, `.gitignore`, `AGENTS.md`, `CLAUDE.md`, `AGENT_KULLANIMI.md`, `UYUMLULUK_RAPORU.md`, `catalog/`, `scripts/`, `tests/`, `skills/refs-catalog/`, `.agents/skills/refs-catalog/`, `.claude/skills/refs-catalog/`.

Araştırma/kodlama aktarımı için ayrıca `ARASTIRMA_KOD_AKISI.md` ve `handoff/templates/` izlenir. Gerçek görev paketleri, worktree'ler ve Claude çıktı logları yayımlanmaz. Aktarım aracının taşınabilir kaynağı ve testleri bu sürüme dahildir; uzak HEAD ile yerel commit eşleşmesi yayın adımında doğrulanır.

Kişisel akışın özgün kaynağı `skills/research-to-claude/` ve `scripts/install_personal_handoff.py` içindedir. Kullanıcı klasörlerindeki kurulum kayıtları (`references/installation.json`) makineye özeldir ve yayımlanmaz.

Yayın hedefi: [Zemora35/claude-refs](https://github.com/Zemora35/claude-refs), herkese açık. Aşağıdaki komutlar koleksiyonu başka bir depoya taşımak veya kendi kopyanı hazırlamak içindir; mevcut depodaysan yeniden `git init` yapmadan önce çalışma alanını ve remote bağlantısını kontrol et.

```powershell
git init
git add .gitignore README.md KATALOG.md SKILL_REHBERI.md YONTEM.md SOURCE_REVIEW.md GITHUB_YUKLEME.md SECURITY.md THIRD_PARTY_NOTICES.md LICENSE AGENTS.md CLAUDE.md AGENT_KULLANIMI.md UYUMLULUK_RAPORU.md ARASTIRMA_KOD_AKISI.md catalog scripts tests handoff/templates skills/research-to-claude skills/refs-catalog .agents/skills/refs-catalog .claude/skills/refs-catalog
git diff --cached --stat
git diff --cached
git status --short
```

Gözden geçirdikten sonra:

```powershell
git commit -m "Add curated repository and skill catalog"
git branch -M main
```

GitHub'da oluşturacağın reponun gerçek HTTPS adresini `git remote add origin` komutuna ver; ardından `git push -u origin main` çalıştır. Var olan bir Git deposundaysan önce `git remote -v` ve `git status` ile doğru depoyu kontrol et; mevcut bağlantıyı ezme.

Yerel eski repo kopyalarını da yayımlamak istersen her birinin lisansını ve üçüncü taraf bildirimlerini ayrıca incele. Tercih edilen taşınabilir yapı URL + commit manifestidir. Yeni makinede `sync_sources.py` sabitlenmiş skill kaynaklarını yeniden getirir; eski 33 klasörü otomatik indirmez.

Yalnızca özgün katalog yönlendiricisi ajan klasörlerinde yayımlanır. Seçmeli kurulumla eklenen diğer beceriler `.gitignore` tarafından dışlanır. `catalog-location.json` yerel mutlak konum taşıdığı için hiçbir konumda yayımlanmaz. İstersen yeniden kullanılabilir yönlendiriciyi daha sonra ayrı bir plugin paketi olarak dağıtabilirsin; bu sürümün dağıtımı proje becerisi biçimindedir.
