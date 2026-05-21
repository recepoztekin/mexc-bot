"""
================================================
  MEXC FUTURES SINYAL BOTU - ANA SCRIPT
================================================
Calistirmak icin:    python main.py
Tek seferlik tarama: python main.py --once
"""

import sys
import time
import json
from datetime import datetime, timedelta
from pathlib import Path

import config
import mexc_client
import indicators
import strategy
import telegram_bot
import tracker


# Sinyal gecmisi dosyasi (cooldown icin)
HISTORY_FILE = Path(__file__).parent / "signal_history.json"


# ============ RENKLI CMD CIKTILARI ============
class C:
    R = "\033[91m"   # red
    G = "\033[92m"   # green
    Y = "\033[93m"   # yellow
    B = "\033[94m"   # blue
    M = "\033[95m"   # magenta
    C = "\033[96m"   # cyan
    W = "\033[97m"   # white
    BOLD = "\033[1m"
    END  = "\033[0m"


def banner():
    print(f"""{C.C}{C.BOLD}
================================================================
        MEXC FUTURES - 4H SWING SINYAL BOTU
        Yuksek Win Rate Odakli | 5 Konfirmasyon Sistemi
================================================================{C.END}""")


def load_history() -> dict:
    if HISTORY_FILE.exists():
        try:
            return json.loads(HISTORY_FILE.read_text())
        except Exception:
            return {}
    return {}


def save_history(h: dict):
    HISTORY_FILE.write_text(json.dumps(h, indent=2))


def is_in_cooldown(symbol: str, history: dict) -> bool:
    """Son sinyalden bu yana yeterli sure gecti mi?"""
    last_str = history.get(symbol)
    if not last_str:
        return False
    try:
        last_time = datetime.fromisoformat(last_str)
        return datetime.utcnow() - last_time < timedelta(hours=config.SIGNAL_COOLDOWN_HOURS)
    except Exception:
        return False


def print_signal_console(sig: dict):
    """Sinyali renkli olarak CMD'ye yazar."""
    color = C.G if sig["direction"] == "LONG" else C.R
    print(f"\n{color}{C.BOLD}{'='*60}")
    print(f"  {sig['direction']} SINYALI - {sig['symbol']}")
    print(f"{'='*60}{C.END}")
    print(f"  {C.W}Giris:{C.END}        {C.BOLD}{sig['entry']:.6f}{C.END}")
    print(f"  {C.R}Stop Loss:{C.END}    {sig['sl']:.6f}  ({sig['risk_pct']:.2f}%)")
    print(f"  {C.G}TP1:{C.END}          {sig['tp1']:.6f}")
    print(f"  {C.G}TP2:{C.END}          {sig['tp2']:.6f}  ({sig['reward_pct']:.2f}%)")
    print(f"  {C.Y}R:R:{C.END}          1:{sig['rr_ratio']:.2f}")
    print(f"  {C.C}Kaldirac:{C.END}     {config.LEVERAGE_SUGGESTION}x")
    print(f"\n  {C.M}Gerekceler:{C.END}")
    for r in sig["reasons"]:
        print(f"    • {r}")
    print()


def scan_once(history: dict) -> int:
    """Tum sembolleri bir kez tarar. Bulunan sinyal sayisini doner."""
    found = 0
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n{C.B}[{timestamp}] Tarama basliyor... ({len(config.SYMBOLS)} sembol){C.END}")

    for symbol in config.SYMBOLS:
        # Cooldown kontrolu
        if is_in_cooldown(symbol, history):
            print(f"  {C.Y}[~] {symbol:<12} cooldown'da, atlandi{C.END}")
            continue

        # Veri cek
        df = mexc_client.fetch_klines(symbol)
        if df is None or len(df) < config.EMA_SLOW + 10:
            print(f"  {C.R}[X] {symbol:<12} veri yetersiz{C.END}")
            continue

        # Indikatorleri ekle
        df = indicators.add_all_indicators(df, config)

        # Sinyal degerlendir
        sig = strategy.evaluate(symbol, df)
        if sig:
            print_signal_console(sig)
            ok = telegram_bot.send_message(telegram_bot.format_signal(sig))
            if ok:
                print(f"  {C.G}[✓] Telegram'a gonderildi{C.END}")
            # CSV'ye kaydet
            sig_id = tracker.log_signal(sig, config.LEVERAGE_SUGGESTION)
            print(f"  {C.C}[+] signals.csv'ye kaydedildi (id={sig_id}){C.END}")
            history[symbol] = datetime.utcnow().isoformat()
            save_history(history)
            found += 1
        else:
            last = df.iloc[-1]
            print(f"  {C.W}[ ] {symbol:<12} sinyal yok  "
                  f"(close={last['close']:.4f}  RSI={last['rsi']:.1f}){C.END}")

        # Rate limit dostlugu
        time.sleep(0.3)

    # Acik sinyallerin SL/TP durumunu kontrol et
    updates = tracker.update_open_signals()
    for u in updates:
        print(f"{C.M}[!] Sinyal #{u['id']} {u['symbol']} -> {u['status']}{C.END}")
        telegram_bot.send_message(tracker.format_status_change(u))

    # Haftalik ozet zamani mi?
    if tracker.is_weekly_summary_time():
        print(f"{C.C}[i] Haftalik ozet gonderiliyor...{C.END}")
        telegram_bot.send_message(tracker.format_weekly_summary())

    print(f"\n{C.C}Tarama tamamlandi. {found} sinyal bulundu.{C.END}\n")
    return found


def main():
    banner()
    once = "--once" in sys.argv

    # Telegram test
    if not once:
        print(f"{C.Y}[i] Telegram baglanti testi...{C.END}")
        ok = telegram_bot.send_message(
            "🤖 <b>MEXC Sinyal Botu baslatildi</b>\n"
            f"Takip edilen: {len(config.SYMBOLS)} sembol\n"
            f"Zaman dilimi: {config.TIMEFRAME}\n"
            f"Tarama araligi: {config.CHECK_INTERVAL_SECONDS} saniye"
        )
        if ok:
            print(f"{C.G}[✓] Telegram baglandi.{C.END}")
        else:
            print(f"{C.R}[!] Telegram baglanmadi - config.py'yi kontrol et.{C.END}")

    history = load_history()

    if once:
        scan_once(history)
        return

    print(f"\n{C.C}Bot calisiyor. Durdurmak icin Ctrl+C.{C.END}")
    while True:
        try:
            scan_once(history)
            print(f"{C.W}Sonraki tarama {config.CHECK_INTERVAL_SECONDS} saniye sonra...{C.END}")
            time.sleep(config.CHECK_INTERVAL_SECONDS)
        except KeyboardInterrupt:
            print(f"\n{C.Y}Bot durduruluyor...{C.END}")
            break
        except Exception as e:
            print(f"{C.R}[X] Beklenmedik hata: {e}{C.END}")
            time.sleep(30)


if __name__ == "__main__":
    main()
