# LimitsHalo

[English](README.md) / [Türkçe](README.tr.md)

LimitsHalo, kalan Codex 5 saatlik ve haftalık limitlerini gösteren, resmî olmayan bir Windows görev çubuğu widget'ıdır. Oturum açılmış Codex Desktop oturumundaki verileri yerel Codex app-server üzerinden okur. Bildirim alanı simgesi ayarları açar; yenileme ve çıkış seçeneklerini sunar. Bu kaynak sürümü `0.1.0-beta`dır.

## Kaynak koddan çalıştırma

Windows 10 veya 11 ve Python 3.10 ya da daha yeni bir sürüm kullanın:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

Canlı limitleri görmek için Codex Desktop kurulu olmalı ve oturum açılmış olmalıdır. İlk çalıştırmada `config.example.json`, yerel ve Git tarafından yok sayılan `config.json` dosyasına kopyalanır. Widget'ı kapatmak için `main.py --quit` komutunu çalıştırın. `main.py --mock` ve `main.py --test`, örnek verileri belirgin biçimde işaretleyerek gösterir; `--test` ayrıca sağ tıklamayla örnek yüzdeler arasında geçiş yapmanızı sağlar.

## Sınırlar

Widget, birincil yatay görev çubuğunu destekler. Codex'in sağlamadığı bir limit için tahmini değer göstermez. Bildirim animasyonu Windows'un yerel bildirim veritabanına bağlıdır ve bu veritabanı değişirse çalışmayabilir. Windows 10, çoklu monitör ve temiz bir makinedeki davranış ayrı ayrı doğrulanmamıştır. Tüm zamanlar token kullanımı sorgulanmaz veya gösterilmez.

## Lisans

LimitsHalo kaynak kodu [Apache License 2.0](LICENSE) kapsamında lisanslanmıştır. Copyright (c) 2026 Arden Works; bkz. [NOTICE](NOTICE). Bağımlılıklar için [üçüncü taraf bildirimlerine](THIRD_PARTY_NOTICES.md) bakın. Codex adı ve işaretleri OpenAI'a aittir; bu proje OpenAI ile bağlantılı değildir.
