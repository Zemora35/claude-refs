# Yerel kaynak incelemesi

Bu rapor dosya envanteri, anahtar kelime taraması ve seçilmiş SKILL.md metinlerinin hash/işaret kayıtlarını içerir. Kaynak kodları çalıştırılmadı. Kelime eşleşmeleri bulguların inceleme adaylarıdır; tek başına zafiyet veya güvenlik onayı değildir.

| Kaynak | Dosya | SKILL.md | Commit kilidi | Etkinleştirme |
|---|---:|---:|---|---|
| [anthropics/skills](https://github.com/anthropics/skills) | 445 | 20 | aynı | yapılmadı |
| [openai/skills](https://github.com/openai/skills) | 783 | 44 | aynı | yapılmadı |
| [vercel-labs/agent-skills](https://github.com/vercel-labs/agent-skills) | 447 | 9 | aynı | yapılmadı |
| [expo/skills](https://github.com/expo/skills) | 185 | 25 | aynı | yapılmadı |
| [cloudflare/skills](https://github.com/cloudflare/skills) | 237 | 19 | aynı | yapılmadı |
| [hashicorp/agent-skills](https://github.com/hashicorp/agent-skills) | 124 | 20 | aynı | yapılmadı |
| [supabase/agent-skills](https://github.com/supabase/agent-skills) | 61 | 2 | aynı | yapılmadı |
| [neondatabase/agent-skills](https://github.com/neondatabase/agent-skills) | 277 | 19 | aynı | yapılmadı |
| [better-auth/skills](https://github.com/better-auth/skills) | 11 | 6 | aynı | yapılmadı |
| [trailofbits/skills](https://github.com/trailofbits/skills) | 1598 | 97 | aynı | yapılmadı |
| [getsentry/skills](https://github.com/getsentry/skills) | 166 | 30 | aynı | yapılmadı |
| [K-Dense-AI/scientific-agent-skills](https://github.com/K-Dense-AI/scientific-agent-skills) | 2780 | 177 | aynı | yapılmadı |
| [remotion-dev/skills](https://github.com/remotion-dev/skills) | 293 | 12 | aynı | yapılmadı |
| [stripe/ai](https://github.com/stripe/ai) | 1052 | 50 | aynı | yapılmadı |
| [deanpeters/Product-Manager-Skills](https://github.com/deanpeters/Product-Manager-Skills) | 454 | 77 | aynı | yapılmadı |
| [phuryn/pm-skills](https://github.com/phuryn/pm-skills) | 161 | 69 | aynı | yapılmadı |
| [coreyhaines31/marketingskills](https://github.com/coreyhaines31/marketingskills) | 771 | 52 | aynı | yapılmadı |
| [kepano/obsidian-skills](https://github.com/kepano/obsidian-skills) | 15 | 6 | aynı | yapılmadı |
| [huggingface/skills](https://github.com/huggingface/skills) | 203 | 26 | aynı | yapılmadı |
| [google/skills](https://github.com/google/skills) | 1258 | 180 | aynı | yapılmadı |
| [google-labs-code/stitch-skills](https://github.com/google-labs-code/stitch-skills) | 88 | 16 | aynı | yapılmadı |
| [mattpocock/skills](https://github.com/mattpocock/skills) | 194 | 38 | aynı | yapılmadı |
| [obra/superpowers](https://github.com/obra/superpowers) | 231 | 15 | aynı | yapılmadı |
| [nextlevelbuilder/ui-ux-pro-max-skill](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill) | 698 | 13 | aynı | yapılmadı |

## İncelemede dikkat edilecek davranışlar

- **anthropics/skills** — account-or-paid-service: 1, credentials-env: 47, file-mutation: 69, global-behavior-override: 2, global-install-config: 9, network: 175, process-execution: 123, proxy-or-endpoint-change: 3, publish-or-deploy: 4, telemetry-or-data-transfer: 3
- **openai/skills** — account-or-paid-service: 7, credentials-env: 90, file-mutation: 39, global-behavior-override: 6, global-install-config: 62, network: 465, process-execution: 96, publish-or-deploy: 98, telemetry-or-data-transfer: 13
- **vercel-labs/agent-skills** — account-or-paid-service: 79, credentials-env: 50, file-mutation: 219, global-install-config: 6, network: 158, process-execution: 158, publish-or-deploy: 89, telemetry-or-data-transfer: 7
- **expo/skills** — account-or-paid-service: 18, credentials-env: 32, file-mutation: 19, global-behavior-override: 2, global-install-config: 15, network: 101, process-execution: 70, publish-or-deploy: 30, telemetry-or-data-transfer: 6
- **cloudflare/skills** — account-or-paid-service: 1, credentials-env: 18, file-mutation: 4, global-install-config: 5, network: 338, process-execution: 59, publish-or-deploy: 28, telemetry-or-data-transfer: 12
- **hashicorp/agent-skills** — account-or-paid-service: 1, credentials-env: 94, file-mutation: 2, network: 66, process-execution: 19, publish-or-deploy: 6, telemetry-or-data-transfer: 6
- **supabase/agent-skills** — credentials-env: 7, file-mutation: 2, global-behavior-override: 1, network: 20, process-execution: 8
- **neondatabase/agent-skills** — account-or-paid-service: 10, credentials-env: 134, file-mutation: 7, global-install-config: 19, network: 370, process-execution: 36, proxy-or-endpoint-change: 2, publish-or-deploy: 106, telemetry-or-data-transfer: 36
- **better-auth/skills** — account-or-paid-service: 1, credentials-env: 12, global-install-config: 12, network: 31, process-execution: 1
- **trailofbits/skills** — account-or-paid-service: 20, credentials-env: 131, file-mutation: 705, global-behavior-override: 6, global-install-config: 30, network: 424, process-execution: 1052, publish-or-deploy: 44, telemetry-or-data-transfer: 29
- **getsentry/skills** — account-or-paid-service: 1, credentials-env: 20, file-mutation: 29, global-behavior-override: 2, global-install-config: 29, network: 48, process-execution: 80, publish-or-deploy: 10, telemetry-or-data-transfer: 12
- **K-Dense-AI/scientific-agent-skills** — account-or-paid-service: 61, credentials-env: 1146, file-mutation: 925, global-behavior-override: 4, global-install-config: 16, network: 2446, process-execution: 1622, proxy-or-endpoint-change: 5, publish-or-deploy: 36, telemetry-or-data-transfer: 109
- **remotion-dev/skills** — credentials-env: 24, file-mutation: 31, network: 27
- **stripe/ai** — account-or-paid-service: 328, credentials-env: 525, file-mutation: 7, global-install-config: 4, network: 578, process-execution: 111, proxy-or-endpoint-change: 1, publish-or-deploy: 5, telemetry-or-data-transfer: 16
- **deanpeters/Product-Manager-Skills** — account-or-paid-service: 82, credentials-env: 32, file-mutation: 3, global-install-config: 32, network: 79, process-execution: 248, publish-or-deploy: 14, telemetry-or-data-transfer: 66
- **phuryn/pm-skills** — account-or-paid-service: 13, global-install-config: 3, network: 169, process-execution: 36, publish-or-deploy: 2, telemetry-or-data-transfer: 26
- **coreyhaines31/marketingskills** — account-or-paid-service: 162, credentials-env: 602, file-mutation: 50, global-install-config: 41, network: 532, process-execution: 368, publish-or-deploy: 24, telemetry-or-data-transfer: 136
- **kepano/obsidian-skills** — global-install-config: 2, network: 15
- **huggingface/skills** — account-or-paid-service: 14, credentials-env: 60, file-mutation: 20, global-install-config: 4, network: 345, process-execution: 121, publish-or-deploy: 69, telemetry-or-data-transfer: 65
- **google/skills** — account-or-paid-service: 433, credentials-env: 490, file-mutation: 44, global-behavior-override: 3, global-install-config: 10, network: 1278, process-execution: 1310, proxy-or-endpoint-change: 1, publish-or-deploy: 306, telemetry-or-data-transfer: 504
- **google-labs-code/stitch-skills** — account-or-paid-service: 1, credentials-env: 17, file-mutation: 2, global-behavior-override: 1, global-install-config: 9, network: 57, process-execution: 12, proxy-or-endpoint-change: 1, publish-or-deploy: 1, telemetry-or-data-transfer: 33
- **mattpocock/skills** — account-or-paid-service: 4, credentials-env: 9, file-mutation: 2, global-install-config: 27, network: 6, process-execution: 9, publish-or-deploy: 10
- **obra/superpowers** — account-or-paid-service: 1, credentials-env: 39, file-mutation: 54, global-behavior-override: 4, global-install-config: 95, network: 68, process-execution: 137, publish-or-deploy: 5, telemetry-or-data-transfer: 8
- **nextlevelbuilder/ui-ux-pro-max-skill** — account-or-paid-service: 3, credentials-env: 203, file-mutation: 192, global-behavior-override: 29, global-install-config: 20, network: 224, process-execution: 171, publish-or-deploy: 9, telemetry-or-data-transfer: 19

Kaynakların bazıları API anahtarı, hesap veya ücretli hizmet; bazısı global kurulum, hook/ayar değişikliği, telemetri, veri yükleme, yayınlama veya genel ajan davranışını değiştirme talimatı içerir. Bunlar uygulanmadı. Özellikle iş akışı paketlerinin tümünü otomatik etkinleştirmek yerine görev için gereken tekil beceri incelenmelidir.

Tam dosya listesi ve satır bazında eşleşme konumları `catalog/source-review.json` içindedir. Bu JSON kaynak satırlarını veya kimlik bilgilerini kopyalamaz. İki mevcut kaynağın yerel commit'i çevrimiçi kilitten farklı olabilir; bunlara dokunulmaz. Seçili becerilerin içerik değerlendirme notları `catalog/skill-review-notes.json` içindedir; son sürümün tüm talimatları denetlenmiş sayılmaz.


## Son doğrulama ve etkinleştirme kararı

24 kaynağın tamamı kilitli commit ile eşleşti. 1.022 SKILL.md dosyasının Git blob kimliği doğrulandı; Windows CRLF/LF dönüşümü ayrı değerlendirildi. Eksik veya içerik kimliği uyuşmayan dosya bulunmadı. 12.532 dosya envantere alındı. Yeni 22 repo yerel `.sources/` alanına eklendi.

İki beceri etkinleştirmeye kapalı olarak işaretlendi:

- `vercel-labs/agent-skills/skills/vercel-cli-with-tokens/SKILL.md`: Token değerlerini çıktılamayı isteyen yönergeler.
- `obra/superpowers/skills/using-superpowers/SKILL.md`: Görev dışına taşan genel ajan davranışı ve zorunlu skill çağırma dayatması.

Diğer beceriler için de görev öncesi inceleme gerekir. 24 kaynağın 22 tanesinden seçilen örnek metin parçaları okundu; iki kaynakta yalnızca statik envanter/tarama yapıldı. Tüm talimatlar tam kapsamlı incelenmiş veya işlevsel olarak test edilmiş sayılmaz. Lisans ve davranış notları `catalog/skill-review-notes.json` içindedir.

## 28 Ekim 2026 eklemeleri

İlk incelemeye ek olarak 12 kaynak ve 1 harici veri koleksiyonu işlendi. Yerel kurulum, lisans istisnaları, platform koşulları ve ücretli servis gereksinimleri [ekleme raporunda](EKLENEN_KAYNAKLAR.md) ve `catalog/requested-additions.json` içinde kayıtlıdır. Upstream kopyalar kendi lisanslarını taşır; paketin MIT lisansı bunları kapsamaz.
