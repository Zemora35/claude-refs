# GitHub'a yükleme

Katalog kökündeki `.gitignore` yalnızca bu çalışmanın ürettiği belge, JSON ve betikleri izlemeye açar. Mevcut repo kopyaları, `.sources/`, iç içe `.git` dizinleri, kişisel ayarlar ve yerel çalışma çıktıları kapsam dışındadır. Üçüncü taraf kodunu kendi lisansımızla yeniden yayımlamayız.

## Yüklenecek dosyalar

`README.md`, `KATALOG.md`, `SKILL_REHBERI.md`, `YONTEM.md`, `SOURCE_REVIEW.md`, `GITHUB_YUKLEME.md`, `SECURITY.md`, `THIRD_PARTY_NOTICES.md`, `LICENSE`, `.gitignore`, `AGENTS.md`, `CLAUDE.md`, `AGENT_KULLANIMI.md`, `UYUMLULUK_RAPORU.md`, `catalog/`, `scripts/`, `tests/`, `skills/refs-catalog/`, `.agents/skills/refs-catalog/`, `.claude/skills/refs-catalog/`.

Yayın hedefi: [Zemora35/claude-refs](https://github.com/Zemora35/claude-refs), herkese açık. Aşağıdaki komutlar koleksiyonu başka bir depoya taşımak veya kendi kopyanı hazırlamak içindir; mevcut depodaysan yeniden `git init` yapmadan önce çalışma alanını ve remote bağlantısını kontrol et.

```powershell
git init
git add .gitignore README.md KATALOG.md SKILL_REHBERI.md YONTEM.md SOURCE_REVIEW.md GITHUB_YUKLEME.md SECURITY.md THIRD_PARTY_NOTICES.md LICENSE AGENTS.md CLAUDE.md AGENT_KULLANIMI.md UYUMLULUK_RAPORU.md catalog scripts tests skills/refs-catalog .agents/skills/refs-catalog .claude/skills/refs-catalog
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
