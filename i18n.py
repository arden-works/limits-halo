"""Small, explicit UI vocabulary for the two supported languages."""

STRINGS = {
    "en": {
        "settings": "Settings", "refresh": "Refresh now", "quit": "Quit",
        "language": "Language", "limits": "Limits", "five": "5-hour limit", "five_short": "5H",
        "week": "Weekly limit", "week_short": "WEEK", "at_least_one": "Keep at least one limit visible.",
        "display": "Display", "view": "Widget", "normal": "Normal",
        "compact": "Compact", "reset_info": "Show reset on widget",
        "reset_mode": "Reset", "remaining": "Time left", "clock_time": "Day / Time",
        "clock_format": "Time format", "hours_24": "24-hour", "hours_12": "12-hour",
        "font_size": "Font size", "font_small": "Small (85%)", "font_default": "Default (100%)",
        "font_large": "Large (115%)",
        "app": "App", "startup": "Launch when Windows starts", "visible": "Show widget",
        "notification": "Notifications", "pulse": "Animate the logo for new Codex notifications",
        "color": "Notification color", "amber": "Amber", "coral": "Coral", "pink": "Pink",
        "violet": "Violet", "cyan": "Cyan", "lime": "Lime", "notification_none": "No notifications",
        "mock": "MOCK DATA", "live": "LIVE", "remaining_limits": "Remaining limits",
        "unavailable": "Unavailable", "waiting": "Waiting for provider",
        "offline": "Offline · showing last data", "codex_unavailable": "Codex unavailable",
        "example": "Example data", "synced": "Data up to date",
        "saving_failed": "Could not save setting", "startup_failed": "Could not change startup setting",
    },
    "tr": {
        "settings": "Ayarlar", "refresh": "Şimdi yenile", "quit": "Çıkış Yap",
        "language": "Dil", "limits": "Limitler", "five": "5 saatlik limit", "five_short": "5SA",
        "week": "Haftalık limit", "week_short": "HAFTA", "at_least_one": "En az bir limit açık kalmalı.",
        "display": "Görünüm ve zaman", "view": "Widget", "normal": "Normal",
        "compact": "Kompakt", "reset_info": "Widget’ta sıfırlanma bilgisini göster",
        "reset_mode": "Sıfırlanma", "remaining": "Kalan süre", "clock_time": "Gün / Saat",
        "clock_format": "Saat biçimi", "hours_24": "24 saat", "hours_12": "12 saat",
        "font_size": "Yazı boyutu", "font_small": "Küçük (%85)", "font_default": "Varsayılan (%100)",
        "font_large": "Büyük (%115)",
        "app": "Uygulama", "startup": "Windows açılışında başlat", "visible": "Widget’ı göster",
        "notification": "Bildirimler", "pulse": "Yeni Codex bildiriminde logoyu ışıklandır",
        "color": "Bildirim rengi", "amber": "Amber", "coral": "Mercan", "pink": "Pembe",
        "violet": "Mor", "cyan": "Turkuaz", "lime": "Yeşil", "notification_none": "Bildirim Yok",
        "mock": "ÖRNEK VERİ", "live": "CANLI", "remaining_limits": "Kalan limitler",
        "unavailable": "Kullanılamıyor", "waiting": "Veri bekleniyor",
        "offline": "Çevrimdışı · son veri gösteriliyor", "codex_unavailable": "Codex kullanılamıyor",
        "example": "Örnek veri", "synced": "Veriler güncel",
        "saving_failed": "Ayar kaydedilemedi", "startup_failed": "Açılış ayarı değiştirilemedi",
    },
}


def tr(key, language="en"):
    return STRINGS[language][key]
