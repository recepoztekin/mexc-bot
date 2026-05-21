"""
Manuel rapor scripti.
Calistirmak: python report.py

Anlik performans ozetini hem terminalde hem Telegram'a gonderir.
"""

import tracker
import telegram_bot


def main():
    summary = tracker.format_weekly_summary()
    # HTML etiketlerini temizleyip terminale yaz
    plain = (summary.replace("<b>", "").replace("</b>", "")
                    .replace("<i>", "").replace("</i>", ""))
    print(plain)
    print("\n→ Telegram'a gonderiliyor...")
    ok = telegram_bot.send_message(summary)
    print("Gonderildi." if ok else "Telegram'a gonderilemedi.")


if __name__ == "__main__":
    main()
