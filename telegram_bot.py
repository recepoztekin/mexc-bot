"""
Telegram bildirim modulu.
"""

import requests
import config


def send_message(text: str, parse_mode: str = "HTML") -> bool:
    """Telegram'a mesaj gonderir."""
    if not config.TELEGRAM_BOT_TOKEN or "BURAYA" in config.TELEGRAM_BOT_TOKEN:
        print("[!] Telegram token ayarli degil, mesaj atilamadi.")
        return False

    url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": config.TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": parse_mode,
        "disable_web_page_preview": True,
    }
    try:
        r = requests.post(url, json=payload, timeout=15)
        if r.status_code == 200:
            return True
        print(f"[X] Telegram hatasi: {r.status_code} - {r.text}")
        return False
    except Exception as e:
        print(f"[X] Telegram baglanti hatasi: {e}")
        return False


def format_signal(sig: dict) -> str:
    """Sinyali guzel formatli Telegram mesajina cevirir."""
    emoji = "🟢" if sig["direction"] == "LONG" else "🔴"
    arrow = "📈" if sig["direction"] == "LONG" else "📉"

    reasons_text = "\n".join([f"• {r}" for r in sig["reasons"]])

    msg = f"""
{emoji} <b>{sig['direction']} SINYALI</b> {arrow}

<b>Sembol:</b> <code>{sig['symbol']}</code>
<b>Zaman Dilimi:</b> {config.TIMEFRAME}
<b>Onerilen Kaldirac:</b> {config.LEVERAGE_SUGGESTION}x

<b>📍 Giris:</b> <code>{sig['entry']:.6f}</code>
<b>🛑 Stop Loss:</b> <code>{sig['sl']:.6f}</code> ({sig['risk_pct']:.2f}%)
<b>🎯 TP1 (yari kapat):</b> <code>{sig['tp1']:.6f}</code>
<b>🎯 TP2 (kalani):</b> <code>{sig['tp2']:.6f}</code> ({sig['reward_pct']:.2f}%)

<b>📊 Risk/Reward:</b> 1:{sig['rr_ratio']:.2f}

<b>✅ Sinyal Gerekceleri:</b>
{reasons_text}

⚠️ <i>Pozisyonu acmadan once kendi analizini yap. SL'i kesinlikle koy.</i>
"""
    return msg.strip()
