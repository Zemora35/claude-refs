# Seçim ve doğrulama yöntemi

Bu katalog popülerlik ve kullanım amacı temelinde oluşturulmuş 54 kategorilik bir kısa listedir. GitHub üzerindeki tüm projeler incelenmedi. Genel aramalar, mevcut yerel kataloglar ve doğrudan üretici kaynakları birlikte kullanıldı. Her listelenen reponun metrikleri GitHub REST API üzerinden kontrol edildi. Arama uç noktasındaki hız sınırı nedeniyle bazı kategorilerde geniş arama tamamlanamadı; doğrudan repo doğrulaması yapıldı. Arama kaydı `catalog/research-log.json` içindedir.

## Talep göstergeleri

Yıldız ve fork sayıları topluluk ilgisi için yaklaşık göstergedir. İndirme, aktif kullanıcı, kurulum ve son dönem yıldız artışı ölçülmedi. Bu nedenle 'en çok talep gören' ifadesi gerçek satış/kullanım sırası anlamında kullanılmaz. Skill kaynaklarının yıldız sayısı içindeki tekil skill'lerin popülerliği değildir.

## Açık puan (0–100)

- Yıldız: `min(35, 7 * log10(stars + 1))`.
- Fork: `min(15, 3.75 * log10(forks + 1))`.
- Son push: 0–30 gün 25; 31–90 gün 20; 91–180 gün 15; 181–365 gün 8; daha eski 0.
- API'de tanınan lisans: 15; null/NOASSERTION: 0. Bu hukuki onay değildir.
- Arşivlenmemiş ve devre dışı olmayan repo: 10.

Puan yalnızca adaylar arasında karşılaştırma aracıdır; güvenlik, kod kalitesi veya alan uygunluğu ölçümü değildir. Skill koleksiyonlarıyla framework'ler farklı türler olarak JSON'da işaretlidir. Kategori için doğru seçim projenin yığınına göre yapılmalıdır. Son push bir commit incelemesinin veya sağlıklı bakımın kanıtı değildir.

## İçerik durumları

- `metadata-verified`: repo kimliği ve açık metrikler alındı.
- `path-verified-content-not-yet-reviewed`: Git ağacında dosya yolu ve blob SHA bulundu; talimatlar okunmuş sayılmaz.
- `static-review`: yerel metin taraması ve seçilen SKILL.md incelemesi yapıldı; işlevsel test/güvenlik sertifikası değildir.

24 skill kaynağının commit'leri sabitlendi. Tree SHA ve commit SHA ayrı alanlardır. Yeni kaynaklar bu commit'lere indirilir. Önceden var olan kaynaklara dokunulmaz; yerel commit farklıysa raporda gösterilir. Genel repo metrikleri tarihli bir anlık görüntüdür; baş commit'leri tüm projeler için sabitlenmiş değildir.

## Alan sınırları

Türkiye'deki imar, yangın, TBDY ve mühendislik uygunluğu bu listeden çıkarılamaz. Finans araçları araştırma/backtest içindir; canlı işlem açılmaz. Medikal ve hukuk kaynakları araştırma ve belge iş akışları için değerlendirilmiştir. Model ağırlıkları, veri setleri, sistem paketleri ve ücretli hizmetler kurulmaz.
