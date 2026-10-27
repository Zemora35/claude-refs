# Claude Code / Codex uyumluluk sonucu

Kontrol tarihi: **27 Ekim 2026**. Test ortamı: Windows, Python 3.12.14, Claude Code 2.1.285, Codex CLI 0.156.1.

## Geçen kontroller

| Kontrol | Sonuç |
|---|---|
| Claude Code yerel skill keşfi | Başlangıç çıktısında `refs-catalog`, hem skills hem slash_commands listesinde göründü. |
| Codex yerel skill keşfi | Gerçek app-server `skills/list` çağrısı `refs-catalog` becerisini `repo` kapsamında, etkin ve hatasız döndürdü. Model çağrısı gerekmedi. |
| SKILL.md biçimi | Resmî skill-creator doğrulayıcısı asıl beceri ve iki ajan kopyası için geçti. Eksik PyYAML yalnızca geçici geliştirme klasörüne alındı; kullanıcı araçlarının ek Python paketi gereksinimi yok. |
| Yönlendirici komutları | İki ajan klasöründeki gerçek giriş noktalarından arama, engelli kaynak incelemesi ve ortam kontrolü çalıştı. |
| Başka projeden erişim | İki yönlendirici ayrı test projesine kuruldu; yerel katalog konumu çözüldü ve arama çalıştı. |
| Gerçek upstream kurulum | `mattpocock/skills` içindeki `codebase-design`, sabit commit'inden iki ajan biçiminde test projesine kuruldu. Beş dosyanın kimliği ve lisans bildirimi doğrulandı. Kaynak yardımcıları çalıştırılmadı. |
| Davranış testleri | **16/16 geçti.** Önizleme, engelli beceri, çakışma, kaynak değişikliği, eksik/izlenmeyen dosya, CRLF, yol sınırı, tekrar kurulum, atıf ve platform metadata'sı kontrol edildi. |

## Tamamlanamayan canlı görev denemeleri

**Claude Code:** Yönlendirici keşfedildi; model görevine geçiş mevcut abonelik oturum limiti nedeniyle tamamlanamadı. Kotanın yenilenmesinden sonra aynı kısa görev yeniden denenebilir. Bu durum başarılı uçtan uca test olarak sayılmadı.

**Codex CLI:** Model yanıtı geldi, ancak salt okunur dosya okuma komutları yerel komut politikası tarafından reddedildi. Seçim alanları boş kaldığı için sürecin sıfır çıkış kodu başarı sayılmadı. Windows sandbox tanılama komutu da kurulum yardımcısı hatası döndürdü. Mevcut sandbox/kurum politikası ve çalışma alanı erişimi gözden geçirilmeden bu makinede CLI üzerinden tam görev akışı doğrulanmış sayılmaz. Sandbox kaldırılmadı veya zayıflatılmadı.

Bu iki sınıra rağmen, yerel beceri keşfi ve Python yönlendiricisi/kurulum araçlarının çalışması bağımsız olarak doğrulandı. Doğrulama tüm bilgisayarların, Claude web/Cowork oturumlarının veya bütün upstream becerilerin aynı şekilde çalışacağı garantisi değildir.

## Önemli platform ayrımı

Gerçek kaynak denemesinde `phuryn/pm-skills` / `prioritize-features` becerisinin `$ARGUMENTS` kullandığı görüldü. Bu, Claude'a özgü bir argüman özelliğidir: Claude kurulumunda korunur; Codex veya ortak kurulumda elle uyarlama istenir. Otomatik kabuk/hook ve alt ajan özellikleri ayrıca engellenir. Kaynaklar sessizce değiştirilmez.

1.022 upstream SKILL.md dosyasının tamamı işlevsel olarak çalıştırılmadı. Bağımlılık profilleri sınırlı ön kontrollerdir; model ağırlıkları, işletim sistemi araçları, özel MCP'ler, servis hesabı ve ücretler görev bazında değerlendirilir. Global ajan ayarları, MCP kayıtları ve sistem paketleri değiştirilmedi.

Makine tarafından okunabilen sonuç: [agent-compatibility-report.json](catalog/agent-compatibility-report.json).

Resmî belgeler: [Claude Code skills](https://code.claude.com/docs/en/skills), [Codex skill keşfi](https://learn.chatgpt.com/docs/build-skills), [Codex app-server skills/list](https://learn.chatgpt.com/docs/app-server), [Windows sandbox tanılama](https://learn.chatgpt.com/docs/windows/windows-sandbox).
