# LimitsHalo 0.1.0-beta — source

This source release shows remaining Codex 5-hour and weekly limits on the primary horizontal Windows taskbar. It needs a signed-in Codex Desktop session for live data. `--mock` and `--test` visibly label example values.

Local settings stay in an ignored `config.json`, initialized from `config.example.json` only when missing. Shutdown now waits for workers before closing the provider, and `--quit` works even if the config is invalid.

Automated tests, source and local PyInstaller startup/quit smoke checks, 240 px compact layout checks, and Turkish/English settings visual checks passed on the development Windows 11 machine. A clean Windows installation and separate Windows 10 or multi-monitor checks remain open. The local PyInstaller build was used only to verify bundled components and licenses. Installer and binary outputs are not part of this source release.

The PyInstaller configuration excludes unused GPL-only Qt components before collection, including Qt Virtual Keyboard. The local bundle inventory and dependency licenses are recorded in [third-party notices](THIRD_PARTY_NOTICES.md).

This is an unofficial community project, unaffiliated with OpenAI.

## Türkçe

Bu kaynak sürümü, kalan Codex 5 saatlik ve haftalık limitlerini birincil yatay Windows görev çubuğunda gösterir. Canlı veri için Codex Desktop oturumunun açık olması gerekir. `--mock` ve `--test` örnek değerleri belirgin biçimde işaretler.

Yerel ayarlar, yalnızca dosya yoksa `config.example.json` üzerinden oluşturulan ve Git tarafından yok sayılan `config.json` içinde tutulur. Kapanışta sağlayıcı kapatılmadan önce çalışan işler beklenir; `--quit`, config geçersiz olsa da çalışır.

Otomatik testler; kaynak kod ve yerel PyInstaller açılış/kapanış kontrolleri; 240 px kompakt yerleşim kontrolleri; Türkçe/İngilizce ayarların görsel kontrolleri geliştirme yapılan Windows 11 makinesinde geçti. Temiz Windows kurulumu, ayrı Windows 10 ve çoklu monitör kontrolleri açık. Yerel PyInstaller build'i yalnızca paketlenen bileşenleri ve lisansları doğrulamak için kullanıldı; installer ve binary çıktıları bu kaynak sürümüne dahil değil.

PyInstaller yapılandırması, Qt Virtual Keyboard dahil kullanılmayan yalnızca GPL lisanslı Qt bileşenlerini paketleme öncesinde dışarıda bırakır. Yerel paket envanteri ve bağımlılık lisansları [üçüncü taraf bildirimlerinde](THIRD_PARTY_NOTICES.md) yer alır.

Bu, OpenAI ile bağlantısı olmayan resmî olmayan bir topluluk projesidir.
