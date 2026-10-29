# 28 Ekim 2026: istenen kaynakların kurulumu

12 ad, iki Open Higgsfield seçimiyle **12 GitHub deposu + 1 Hugging Face veri koleksiyonu** olarak eşleştirildi. AppFlowy zaten katalogdaydı; kaydı yenilendi. Böylece 11 yeni repo kaydı eklendi.

**Yerel kapsam:** `Tools/claude-refs` koleksiyonunda 22 özgün upstream beceri, hem `.agents/skills/` hem `.claude/skills/` içine kuruldu (44 kopya). Kişisel/global skill dizinleri değiştirilmedi. Bu beceriler koleksiyon klasöründe açılan yeni ajan oturumunda keşfedilir. Başka projede yalnızca istenen beceriyi aşağıdaki kurulum komutuyla seç.

Kaynak klonları sabit commit’e bağlıdır; yalnızca belgeler ve becerilerin tam klasörleri indirilmiştir. Uygulamaların bütün kaynakları, servisleri, modelleri ve çalışma bağımlılıkları kurulmamıştır. Kaynak kodunu gerektiğinde commit bağlantısından incele. `.sources/` ve yerel upstream kurulumları GitHub yayımlama alanından dışlanır; taşınabilir katalog/lock/kurulum betikleri yayımlanabilir.

| Kaynak | Sabit commit | Kullanım ve koşullar |
|---|---|---|
| [wesbos/3d-model-anything](https://github.com/wesbos/3d-model-anything) | [`31b2dc9da3fb`](https://github.com/wesbos/3d-model-anything/tree/31b2dc9da3fb541e501f2f0936e55b32afb70ee8) | MIT license file verified; capture/demo assets have separate conditions. Python conversion uses stdlib; comparisons need Pillow, geometry may need NumPy/Open3D, capture scripts require zsh/agent-browser and are not Windows-native. Texture helper calls Poly Haven/ambientCG only when explicitly run. Personal scans remain local. Viewer/iPhone app and dependencies are not installed. |
| [xiiiabu/motionsites.ai](https://github.com/xiiiabu/motionsites.ai) | [`8e7f3ad60410`](https://github.com/xiiiabu/motionsites.ai/tree/8e7f3ad604105e75dba82ab2706b0ba1df6da4c2) | MIT reference collection of website prompts/examples; no SKILL.md. Only README and LICENSE fetched; large preview media excluded. |
| [Jakeschincariol/replica-skill](https://github.com/Jakeschincariol/replica-skill) | [`77c9436fb3d1`](https://github.com/Jakeschincariol/replica-skill/tree/77c9436fb3d18c3d58169efb8caf4fe906b0dc51) | All eleven skill instructions read. Local Python helpers statically screened; external accounts, commits, messages and publication still require task-specific authorization. Build instructions suggest commits; installation grants no commit authority. Adjacent Replica skills are installed together to preserve cross-skill helper paths. No hooks/plugin activated. |
| [debpalash/VoiceStudio](https://github.com/debpalash/VoiceStudio) | [`336d48481b8c`](https://github.com/debpalash/VoiceStudio/tree/336d48481b8c7c0ef810bc5f00e80a3aaddace8f) | AGPL-3.0; two VoiceStudio-specific skills reviewed. Generic FastAPI/Vite copies indexed but not activated. Audio requires a running backend and installed models; no app, MCP server, model weights, microphone or voice clone started. Model rights and download requirements are separate. |
| [duckduckdeploy/openseo](https://github.com/duckduckdeploy/openseo) | [`522ea0e44011`](https://github.com/duckduckdeploy/openseo/tree/522ea0e44011ac52cf8973df73a6f72785bf2aaa) | Current OpenSEO at openseo.gg, distinct from old TahaHachana/OpenSEO. All seven instructions reviewed. Requires configured OpenSEO MCP/account; paid data lookups require dry_run, disclosed price and agreed max_cost_usd. No MCP registration, Google connection, crawl or paid lookup performed. |
| [AppFlowy-IO/AppFlowy](https://github.com/AppFlowy-IO/AppFlowy) | [`5cf3a365dec0`](https://github.com/AppFlowy-IO/AppFlowy/tree/5cf3a365dec0d59f64bad1ee4bb1050471a39b93) | Already in repository catalog; metadata refreshed and pinned documentation source added. AGPL-3.0 application, no upstream SKILL.md found in recursive tree. Desktop/server dependencies not installed. |
| [calcom/cal.diy](https://github.com/calcom/cal.diy) | [`56da01b4b166`](https://github.com/calcom/cal.diy/tree/56da01b4b1664894b784aca636eccab0c56cc141) | MIT repo with five skill paths including duplicate Vercel guidance. calcom-api hardcodes https://api.cal.com/v2 rather than a discovered self-hosted Cal.diy endpoint: activation blocked pending endpoint/credentials review. No key read or booking created. |
| [chatwoot/chatwoot](https://github.com/chatwoot/chatwoot) | [`90ed589c695f`](https://github.com/chatwoot/chatwoot/tree/90ed589c695f6aeaeea0e78f6be7d4ec0fb3e1b3) | MIT community core plus separately licensed enterprise directory. Only documentation/notices fetched; no application, Postgres/Redis, integration, messaging or account started. |
| [CapSoftware/Cap](https://github.com/CapSoftware/Cap) | [`d0aa6cb7ec0e`](https://github.com/CapSoftware/Cap/tree/d0aa6cb7ec0ea9ce46a42fa5d733965719dd1647) | Main cap CLI skill reviewed; requires installed Cap CLI and authorized account. cap-demo explicitly macOS Apple Silicon only and is blocked on this Windows package. building skill assumes provisioning, recording, uploads and PR publication from invocation: blocked pending a narrower separately reviewed workflow. Repository uses mixed licensing, predominantly AGPL-3.0. |
| [opf/openproject](https://github.com/opf/openproject) | [`d19b45aa8b47`](https://github.com/opf/openproject/tree/d19b45aa8b4757b4e17c51facff5fa47ff6eb2c2) | GPL-3.0; pinned root documentation fetched. Root-only inventory because recursive API response exceeded connector limits; absence of nested skills has not been established. No Rails service, database or containers started. |
| [Autom8AI/Open-Higgsfield-AI](https://github.com/Autom8AI/Open-Higgsfield-AI) | [`d32d022e6723`](https://github.com/Autom8AI/Open-Higgsfield-AI/tree/d32d022e6723b74d587aa559b6e7d4586c3a3243) | User selected this and wide-trace variant. README claims MIT, no LICENSE file in reviewed tree. Reference only; paid MuAPI key needed for generation. No installer/security-setting bypass, remote generation or upload executed. |
| [wide-trace/open-higgsfield](https://github.com/wide-trace/open-higgsfield) | [`b16a0efe4d7e`](https://github.com/wide-trace/open-higgsfield/tree/b16a0efe4d7e2707b56f8ccb02387fd2a9d2eddf) | User selected both variants. No repository license file detected; reference only. Generation requires provider key and may incur charges; media inputs can become public Vercel Blob URLs. No key, cloud service or upload configured. |

## NVIDIA SimReady

[nvidia/simready-assets](https://huggingface.co/datasets/nvidia/simready-assets), `catalog/resources.json` içinde revision ve lisans metadatasıyla kayıtlıdır. 3D varlık dosyaları indirilmedi. Seçilen tekil paketlerin boyutu, CC BY 4.0 bildirimi ve atfı kullanım sırasında kontrol edilmelidir. `search --query simready` ile yönlendiricide bulunur.

## Beceri seçimi

**Kurulanlar:** `scan-to-threejs`; Replica’nın 11 becerisi; `voicestudio`, `voicestudio-maintainer`; OpenSEO’nun 7 becerisi; `cap`. Toplam 22.

**Etkinleştirmeye kapalı:** `calcom-api` (Cal.diy/Cal.com uç noktası kontrolü gerekiyor), `cap-demo` (macOS Apple Silicon gerektiriyor), Cap’in `building` becerisi (altyapı/yayınlama kapsamı ayrıca daraltılmalı). Bunlar kaynak ve katalogda korunur. VoiceStudio’nun FastAPI/Vite kopyaları ile Cal.diy’nin dört Vercel kopyası yalnızca envanterdedir; aynı amaçlı mevcut becerileri çoğaltmaz.

Cap CLI/Desktop, VoiceStudio backend/modelleri ve OpenSEO MCP bağlantısı bu işlemle kurulmadı. OpenSEO/Open Higgsfield servislerinde ücret veya dışarı medya aktarımı söz konusu olabilir; bu kurulumda ücretli çağrı, kayıt, ses klonlama, yükleme ya da yayın yapılmadı. `scan-to-threejs` Python dönüşümleri ile zsh tabanlı görsel yakalama farklı gereksinimlere sahiptir; Windows’ta tüm araçların çalıştığı iddia edilmez.

## Kullanım

```powershell
python skills/refs-catalog/scripts/route.py search --query replica
python skills/refs-catalog/scripts/route.py search --query simready
python scripts/agent_bridge.py inspect --repository debpalash/VoiceStudio --skill voicestudio
python scripts/agent_bridge.py plan --repository Jakeschincariol/replica-skill --skill replica-recon --project C:/projem --platform both
python scripts/agent_bridge.py install --repository Jakeschincariol/replica-skill --skill replica-recon --project C:/projem --platform both --apply
```

Replica akışını başka projeye taşırken 11 beceriyi birlikte seç: bazı komutlar komşu becerinin yardımcı betiğine başvurur. Kurulum planını okumak; commit, mesaj, dağıtım veya ücretli servis işlemleri için yetki vermez.

## Doğrulama

Seçilen 410 dosyanın Git blob kimliği kontrol edildi; 31 SKILL.md yolu eklendi. Seçilen 22 becerinin planı, iki platforma kopyası, yardımcı dosyaları ve lisans bildirimleri doğrulanır. Statik inceleme, uygulamanın veya modelin uçtan uca çalıştığı anlamına gelmez. Test sonuçları yerel kurulum raporunda ayrıca bulunur.

## 29 Ekim: ücretsiz yerel medya

7 yeni repo, mevcut faster-whisper kaydının yenilenmesi, 8 sabit kaynak ve 3 skill (iki platform için 6 koleksiyon kopyası) eklendi. [Kapsam ve yeniden kurma](UCRETSIZ_MEDYA.md). Ücretli üretim, uygulama veya ses modeli kurulumu yapılmadı.
