# ChatGPT araştırır, Claude Code uygular

Bu akış kullanıcının başlattığı kontrollü bir dosya aktarımıdır. ChatGPT/Codex araştırmayı ve TASK.md'yi hazırlar; Claude Code yerel abonelik oturumuyla ayrı bir Git worktree'sinde kodu uygular. OpenAI API anahtarı veya yeni bir ajan frameworkü gerekmez. Normal ChatGPT web sohbeti bilgisayarındaki runner'ı doğrudan çalıştırmaz: görev belgesini indirip yerel araca verirsin. Yerel dosya erişimi olan bu tür bir Codex oturumunda hazırlama adımı dosyaya doğrudan yapılabilir.


## Ekonomik varsayılan akış

Yeni görevlerde **bir veya iki gerçek hata grubu** bildir: `prepare --issue-group "Hata A" --issue-group "Hata B"`. Üçüncü grup reddedilir. TASK.md 80–12000 UTF-8 baytla sınırlıdır; kalan işleri ayrı görevlere böl. Bu, etiket sayısını kontrol eder; büyük bir listeyi tek etiketle gizlememek görev hazırlayan ajanın sorumluluğudur. Eski mühürlü paketler değiştirilmeden okunur.

Dar testler `--target-test-commands-file targeted-approved.json` veya tekrarlanan `--target-test-command-json` ile verilir; Claude'a otomatik izinli olur. `--test-commands-file` / `--test-command-json` **son host paketidir** ve Claude'un Bash izinlerine eklenmez. Aynı son komutun ayrıca `--allow-command` olması yeni paketlerde reddedilir. Kurulum/bağlantı komutlarını test listesi gibi sınıflandırma. Ham logları TASK.md'ye kopyalama; kısa hata özeti ve dosya yolu ver.

Claude kodlarken hedef testlerle çalışır. Kodlama başarılıysa host hedefleri bağımsız kontrol eder; geçerlerse son paketi bir kez çalıştırır. Hedefler başarısızsa tam paket atlanır ve geçmiş sayılmaz. Bu hedef hata kanıtı güncelse düzeltme taslağı hazırlanabilir. Konsol/tekrar promptu kısa özet taşır; tam stdout/stderr yerel verification JSON'unda korunur.

Kişisel helper'ın mutlak yolunu, **seçilmiş projenin Git kökünden** kullan:

```text
python <skill>/scripts/handoff_entry.py launch --bundle <görev> --expected-project <proje-kökü> --start
```

Alternatif merkezi araç: `python <toolkit>/scripts/handoff_job.py start ... --start`. `launch` yalnız worker'ın başladığını bildirir; Claude oturum açma/model sonucu sonradan oluşur. Yerel Python worker gizli pencerede mevcut runner'ı ve testleri takip eder; `job.json`, `progress.json`, `RESULT.md`, `run-result.json`, `changes.patch` ve yerel logları yazar. Aktif iş ikinci kez başlatılmaz. Kota/izin hatasında otomatik tekrar, merge veya push yapılmaz.

**Her dakika modele durum sorgulatma.** Yerel worker kendi bekler. İstemci yerel bitiş olayı sunuyorsa onu kullan; sunmuyorsa sonuç dosyasının konumunu ver ve kullanıcının sonraki durum isteğinde bir kez oku. Otomatik sohbet bildirimi kurulmaz. Yerel terminalde `handoff_entry.py wait --bundle ... --expected-project ... --timeout-seconds 600` Python içinde bekler; `--timeout-seconds 0` anlık worker durumudur. Bu komut Claude, test veya yeniden deneme başlatmaz. Sık model çağrısıyla wait/status döngüsü oluşturma. Foreground `run --start` geriye uyumludur.

Kullanıcının incelediği sonuçtan sonra açık yeniden denemesi: `launch ... --start --retry`. Kısmi çalışma korunur. Yeni akış tercihi araştırma varsayılanını, sağlayıcıyı veya model seçimini değiştirmez.

## Hazırlama

Önce proje klasörünü ve istediğin özelliği araştırmayı yapacak ajana ver. [Araştırma promptu](handoff/templates/RESEARCH_PROMPT.md) ve [TASK şablonu](handoff/templates/TASK_TEMPLATE.md) bu adım içindir. Şablon doldurma işaretleri kaldırılmış, gerçek dosya yolları ve kabul ölçütleri olan bir TASK.md üret.

Hedef bir Git deposu olmalı ve izlenen dosyalarda kaydedilmemiş değişiklik bulunmamalı. Hiçbir şey otomatik stash/reset yapılmaz. Görev paketi hedef deponun dışında tutulur. Örnek yolları kendi mevcut proje ve görev konumunla değiştir:

```powershell
python scripts/handoff.py prepare --project ../my-project --task ../TASK.md --out ../handoffs/feature-one --allow-path src/ --allow-path tests/ --issue-group "Hedef hata" --target-test-commands-file ../targeted-approved.json --test-commands-file ../tests-approved.json
```

`--allow-path src/` bir dizin kapsamıdır; sondaki `/` önemlidir. `--allow-path README.md` yalnızca o dosyayı kapsar. Ajan ayarları, Git metadata'sı ve sır dosyaları bu ilk sürümün otomatik değişiklik kapsamına alınmaz. Yalnızca gerçekten incelenmiş test/kurulum komutlarını `--allow-command` ile belirt. Operatör, joker veya komut zinciri kabul edilmez. Bağımlılıklar worktree'ye otomatik kopyalanmaz; gerekiyorsa incelenmiş kurulum komutunu ayrıca izin listesine al.

Hazırlama model çağrısı yapmaz, worktree oluşturmaz. Başlangıç commit'i, TASK.md kimliği, izin verilen yollar/komutlar ve süre/bütçe sınırı `run.json` içine kaydedilir. Görev veya sözleşme değişirse yeni paket hazırlanmalıdır. Hash kontrolü yanlışlıkla değişiklikleri fark etmek içindir; imza veya farklı kullanıcılar arasında yetkilendirme sistemi değildir.

`tests-approved.json`, ayrıca bağımsız çalıştırılması incelenmiş test komutlarının argv dizilerini içerir. İlk öğe gerçek Python/Node gibi native çalıştırılabilir dosyanın mutlak yolu olmalıdır; aşağıdaki örnek yolu kendi kurulumuna göre değiştir:

```json
[["C:/Python312/python.exe", "-B", "-m", "unittest", "discover", "-s", "tests", "-v"]]
```

Test listesi sözleşmeye kaydedilir; dosyadaki sonraki değişiklikler hazırlanmış paketi değiştirmez. Alternatif olarak her komut için `--test-command-json` ile bir argv dizisi verilebilir. Bu liste Claude'un Bash izinlerinden ayrıdır. Kodlama başarılıysa runner listelenen testleri ayrıca `shell=False` ile worktree içinde çalıştırır. Test komutu verilmemiş eski paketler bağımsız test edilmiş sayılmaz. `.cmd`/`.bat` sarmalayıcıları desteklenmez; örneğin npm komutları için gözden geçirilmiş gerçek Node çalıştırma yolu/argümanları kullanılmalıdır.

## Tek komutla başlat

Önce yalnızca planı görmek için:

```powershell
python scripts/handoff.py run --bundle ../handoffs/feature-one
```

İncelediğin görevi başlatan tek komut:

```powershell
python scripts/handoff.py run --bundle ../handoffs/feature-one --expected-project ../my-project --start
```

Bu açık başlatma Claude'un mevcut abonelik kotasını kullanabilir. Varsayılan akış doğrulanmış `claude.ai` oturumu ister; API-key veya özel sağlayıcı ortamını sessizce ücretli kullanıma çevirmez. Windows npm kurulumundaki native `claude.exe` desteklenir; batch/shell wrapper çalıştırılmaz. Eksik CLI/oturum varsa kodlama başlamadan hata verilir.

`--expected-project`, aktif sohbetin projesinden belirlenir ve görev paketindeki proje köküyle aynı olmalıdır. Bu parametre olmadan veya farklı proje verilerek canlı başlatma reddedilir. Böylece eski bir görev paketini başka bir projenin sohbetinde yanlışlıkla çalıştırma riski kontrol edilir.

Runner `handoff/...` dalını ve ayrı worktree'yi oluşturur. Claude'a dosya kapsamına göre Edit kuralları ve yalnızca incelenmiş Bash komutları verilir; `dontAsk` modu diğer izin isteyen işlemleri reddeder. Oturum için proje/kullanıcı ayar kaynakları dışlanır ve hooks kapatılır. Varsayılan MCP listesi boştur; araştırma açıkça etkinleştirildiyse yalnızca göreve bağlı araştırma sunucusu eklenir. Kurumsal yönetilen politikalar yine geçerlidir. İzin atlatma modu kullanılmaz.

Varsayılan duvar saati sınırı 600 saniyedir. `prepare --timeout-seconds` ile 5–3600 saniye seçilebilir. `--budget-usd` Claude CLI'ın tahmini maliyet sınırıdır; abonelik kotasının veya faturalandırmanın bağımsız garantisi değildir. Süre sınırında yalnızca runner'ın başlattığı süreç ağacı durdurulur. Kota/izin hatası veya kesilmede otomatik tekrar döngüsü yoktur.

## Sonucu incele

Görev paketinde şunlar oluşur:

- `worktree/`: İncelenecek kod değişiklikleri; asıl çalışma kopyasına otomatik aktarılmaz.
- `RESULT.md`: Claude'un özeti ve runner durumu.
- `run-result.json`: Kapsam/izin/başlangıç commit'i kontrolleri.
- `changes.patch`: İzin verilen yollardaki izlenen ve yeni dosyaların diff'i.
- `claude-output.json`, `claude-stderr.log`: Yerel hata ve sonuç kayıtları.
- `verification-*.json`: Bağımsız çalıştırılan komutlar, çalışma klasörü, çıkış kodu, süre ve stdout/stderr kanıtı.

`completed-needs-review`, kullanıcının incelemesi gerektiğini belirtir. Test sonucunu `verification` alanından ayrıca kontrol et: `passed`, tüm yapılandırılmış komutların gerçekten sıfır çıkış koduyla bittiğini belirtir; test kapsamının yeterli olduğunu garanti etmez. `tests-failed`, gözlenen başarısızlığı; `verification-incomplete`, süre aşımı, yarım kalan çalıştırma veya test sırasında kaynak değişikliğini belirtir. Kota ve izin reddi başarı değildir. Kapsam dışı değişiklikler veya değişen Git geçmişi raporlanır; dosyalar otomatik silinmez veya geri alınmaz. Çalışma paketi ve loglar özel proje verisi içerebilir; otomatik GitHub yüklemesi yapılmaz.

Görev/proje/dal, değişen dosyalar, testlerin güncelliği ve kalan işler için:

```powershell
python scripts/handoff.py status --bundle ../handoffs/feature-one
```

Bu komut model veya test çalıştırmaz. Kod değişirse eski test kanıtı güncel sayılmaz. Testlerin açıkça yeniden çalıştırılması için:

```powershell
python scripts/handoff.py verify --bundle ../handoffs/feature-one --expected-project ../my-project --execute-tests
```

Güncel ve tamamlanmış bağımsız testlerde başarısızlık varsa, kanıtı ve dar kapsamı içeren düzeltme taslağı üret:

```powershell
python scripts/handoff.py draft-correction --bundle ../handoffs/feature-one --out ../CORRECTION.md
```

Bu adım Claude'u başlatmaz. Güncel başarısız test yoksa taslak üretmez. Taslağı inceleyip açıkça yeniden başlatma istediğinde aynı pakete `run --start --retry` uygulanır; kısmi kod korunur, önceki deneme arşivlenir ve eşleşen test kanıtı Claude'a verilir. Taslağın düzenlenmesi özgün görev/sözleşmeyi değiştirmez; farklı kapsam veya yeni gereksinim için yeni paket gerekir.

Sonucu ChatGPT/Codex'e vermek için [inceleme promptunu](handoff/templates/REVIEW_PROMPT.md) kullan. Düzeltme gerekirse yeni görev veya incelenmiş bir tekrar oluştur. Aynı paketi yeniden başlatmak ancak açık `--start --retry` ile olur; mevcut worktree'deki kısmi değişiklikler korunur. Otomatik commit, merge veya push yapılmaz.

## Sınırlar

Git worktree ayrı bir kod çalışma alanıdır, işletim sistemi sandbox'ı değildir. Onayladığın test/kurulum komutları kullanıcı yetkileriyle çalışabilir; güvenmediğin projeleri bu araçla çalıştırma. Dosya kapsamı kontrolü ve Claude izinleri, alt süreçler için tam OS izolasyonu garantisi sağlamaz. Bu ilk sürüm tek kullanıcılı yerel iş akışıdır; çok kullanıcılı servis, uzaktan yönetim veya sınırsız ajan döngüsü içermez.

Runner'ın deterministik testleri sahte Claude aktarımı, gerçek yerel Git depoları ve gerçek test alt süreçlerini kullanır. Canlı model denemesi bunlardan ayrı raporlanır; güncel sonuç ve sınırlamalar [UYUMLULUK_RAPORU.md](UYUMLULUK_RAPORU.md) içindedir.

Kaynaklar: [Claude programatik kullanım](https://code.claude.com/docs/en/headless), [Claude izinleri](https://code.claude.com/docs/en/permissions), [Claude hooks](https://code.claude.com/docs/en/hooks). Uygulamadaki görev/izin sınırları için yerel OWASP AI Agent Security rehberindeki en az yetki ve karar-yürütme ayrımı dikkate alındı; rehber metni kopyalanmadı.

## Her yerel sohbette çağırma

Özgün `research-to-claude` becerisi kişisel konumlara kurulabilir. Katalog kökünden `python scripts/install_personal_handoff.py` planı gösterir; `--apply` Codex için `~/.agents/skills/research-to-claude`, Claude Code için `~/.claude/skills/research-to-claude` konumlarına kurar. Var olan aynı adlı beceriyi ezmez. Yerel kayıt yalnızca toolkit ve Python konumlarını tutar; son proje veya son görev kaydedilmez.

Bu bilgisayardaki yerel bir proje sohbetinde “Claude'u başlat” diyebilirsin. Açık çağrı için Codex'te `$research-to-claude`, Claude Code'da `/research-to-claude` kullanılabilir. Görünmezse yeni bir sohbet aç veya istemciyi yeniden başlat. Normal ChatGPT web/mobil ve başka makinelerde bu yerel kurulum otomatik bulunmaz.

Beceri önce sohbetin aktif proje bilgisini, komutun çalışma dizininden bulunan Git kökünü ve görev paketinin proje yolunu eşleştirir. Başka sohbetin son projesine, örnek projeye veya en son görev klasörüne otomatik geçmez. Projesiz sohbette ya da belirsizlikte proje yolu sorulur. Claude, aynı projenin başlangıç commit'inden oluşturulan ayrı fiziksel worktree klasöründe çalışır; başka bir projede başlamaz.

Bu sohbetin konuşma geçmişi Claude'a otomatik aktarılmaz. Uygulama için gereken araştırma, karar ve sınırlar bu sohbetten TASK.md'ye yazılır. Sırf sohbet bitti diye Claude çalışmaz; açık başlatma isteği gerekir.

## Claude kodlarken Codex'e araştırma sorma

Bu isteğe bağlı köprüde Claude Code, `mcp__research__research_question` aracıyla Codex CLI'dan kaynaklı araştırma isteyebilir. Codex, ChatGPT ile açılmış yerel CLI oturumunu kullanır; tarayıcıdaki ChatGPT sohbetleri veya Deep Research oturumları okunmaz. API anahtarı/özel sağlayıcı ortamı bu akışta sessizce ücretli kullanıma çevrilmez. Araştırma Codex abonelik kullanımına dahildir.

Mevcut `prepare` komutuna şu seçenekler eklenir:

```text
--enable-research --research-context-file src/example.py --research-max-calls 2 --research-timeout-seconds 120 --research-total-seconds 240 --research-cache-hours 24
```

`--research-context-file` isteğe bağlı ve tekrar edilebilirdir. Dosya seçilmezse yalnızca araştırma sorusu aktarılır. Seçilen dosyalar hazırlama anında kopyalanıp SHA-256 ile sözleşmeye bağlanır; Claude'un sonraki canlı değişiklikleri araştırmacıya kendiliğinden gönderilmez. En fazla sekiz UTF-8 dosya, dosya başına 32.000 ve toplam 64.000 bayt kabul edilir. Gizli dosyalar, sembolik bağlantılar, hassas dosya adları ve bilinen bazı sır kalıpları reddedilir. Bu kontrol tüm hassas verileri bulmayı garanti etmez; dosya seçimi ve araştırma sorusu ayrıca gözden geçirilmelidir.

Araç yalnızca `question` ve onaylı `context_ids` alır; model komut, klasör, hesap, model adı veya sınırsız içerik belirleyemez. Sunucu yalnızca açıkça başlatılmış ve proje kimliği eşleşen görev süresince geçerli bir oturum yetkisiyle çalışır. Global MCP kaydı veya dışarıya açık port oluşturulmaz. Sonuçta bu yetki iptal edilir.

Araştırmacı, ayrı ve boş bir çalışma klasöründe `read-only` sandbox ile çalışır. Komut çalıştırma, alt ajanlar, uygulama araçları, kullanıcı hooks'u ve hafıza bu araştırma çağrısında kapatılır. Gerekli bağlam doğrudan verildiği için yerel kaynak okuma komutu gerekmez. Yönetilen politikalar ve execpolicy kuralları atlatılmaz. Bu yöntem, önceki genel Codex dosya okuma hatasının her kullanımda düzeldiği anlamına gelmez; araştırma yolu o komutlara ihtiyaç duymaz.

Varsayılanlar: **iki model çağrısı, çağrı başına 120 saniye, toplam 240 saniye**. Başarısız çağrı da sınırı tüketir. Aynı başarısız soru veya sağlayıcı kota hatası aynı Claude çalışmasında otomatik tekrar edilmez. Kullanıcı incelemesinden sonra açık `run --start --retry` yeni araştırma oturumu açabilir; önceki çağrı sayısı ve süre toplamı sıfırlanmaz. Kota veya eksik izin başka hesap/anahtar/sandbox yoluyla aşılmaz.

Aynı görev, soru ve seçilmiş bağlam için başarılı rapor 24 saat önbellekte tutulur. Önceki başarısızlık başarı olarak saklanmaz. Farklı proje ve görevlerin önbelleği paylaşılmaz. Bunlar token veya ücret için kesin tavan değildir: modelin sistem bağlamı ve web sonuçları da token tüketir. CLI'ın raporladığı gerçek kullanım yerel rapora kaydedilir.

`research/call-N/` altında soru, web arama olayları, stderr ve tarihli `report.json`; `research/state.json` içinde kalıcı çağrı/süre hesabı; `research/cache/` içinde süreli raporlar bulunur. `status` araştırma çağrılarını ve hatalarını da gösterir. Kaynak URL'leri, araştırmanın gerçekten web araması yaptığı kanıtı ile birlikte kaydedilir; kaynakta yazan her iddianın otomatik doğrulandığı anlamına gelmez. Rapor uygulama kapsamını genişletmez ve otomatik kod değişikliği, commit veya yayınlama yetkisi vermez.

Yeni kişisel kurulumda araştırmayı varsayılan yapmak için `install_personal_handoff.py --apply --enable-research-default` seçilebilir. Bu tercih yalnızca makineye özel kurulum kaydına yazılır. Görev bazında `prepare --disable-research` tercihi geçersiz kılar; merkezi runner'ın varsayılanı araştırmayı kapalı tutar. Hazırlama veya kurulum sırasında model çağrısı yapılmaz.
