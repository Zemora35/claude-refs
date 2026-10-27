# ChatGPT / Codex için araştırma isteği

Bu projedeki isteği araştır ve Claude Code'un uygulayabileceği bir TASK.md hazırla. Bu aşamada uygulama kodunu değiştirme.

Önce erişebildiğin mevcut projeyi ve geçerli proje talimatlarını incele. Erişemediğin dosyaların içeriğini varsayma; gereken en küçük eksik bilgiyi sor. Güncel teknik iddiaları üreticinin birincil belgeleriyle doğrula. Claude Refs kataloğu gerekiyorsa aday bulmak için kullan; yıldız sayısını kalite veya güvenlik garantisi olarak sunma.

TASK.md; amaç, mevcut durum, araştırma kaynakları ve tarihi, kararlar, değişiklik kapsamı, kapsam dışı işler, uygulama adımları, kabul ölçütleri, incelenmiş test komutları ve açık soruları içersin. Özel kodu, sırları veya kimlik bilgilerini araştırma servislerine gönderme.

Doğrulanmış bulguları varsayımlardan ayır. Claude'a devredilen görev mevcut yığına uygun ve tek oturumda gözden geçirilebilir büyüklükte olsun. Yeni framework, hesap, ücretli servis veya geniş refaktör gerçekten gerekiyorsa nedenini ve etkisini açıkla; bunları sessizce kapsamın içine ekleme.

Görevin tamamlandığını gösterecek kanıtı tanımla. Claude'dan ayrı worktree'de çalışmasını, yalnızca izin verilen yolları değiştirmesini ve gözlenen test sonuçlarıyla özet döndürmesini iste. Commit, merge, push veya yayınlama görevin parçası olmasın.

Sonuç, `handoff.py prepare` komutuna verilebilecek tamamlanmış bir TASK.md olmalı; doldurulmamış şablon işaretleri bırakma. Kullanıcı proje yolu ve gerçek özellik belirtmediyse uygulama görevi uydurma.
