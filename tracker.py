"""
Sinyal performans takip modulu.

Her sinyal CSV'ye yazilir. Bot her tarama dongusunde acik sinyallerin
canli fiyatini kontrol eder ve SL/TP1/TP2'ye degip degmedigine bakar.
Sonuc otomatik isaretlenir.

CSV dosyasi: signals.csv
"""

import csv
import os
from datetime import datetime, timedelta
from pathlib import Path

import mexc_client

CSV_FILE = Path(__file__).parent / "signals.csv"

# CSV sutunlari
FIELDS = [
    "id",
    "timestamp",          # Sinyal zamani (UTC)
    "symbol",
    "direction",          # LONG / SHORT
    "entry",
    "sl",
    "tp1",
    "tp2",
    "risk_pct",
    "reward_pct",
    "rr_ratio",
    "leverage",
    "status",             # OPEN / TP1_HIT / TP2_HIT / SL_HIT / CLOSED
    "result",             # WIN / LOSS / BREAKEVEN / PARTIAL
    "pnl_pct",            # Kar/zarar yuzdesi (kaldiracsiz)
    "closed_at",          # Kapanma zamani (UTC)
    "reasons",            # Sinyal gerekceleri
]


def _ensure_file():
    """CSV dosyasi yoksa header ile olusturur."""
    if not CSV_FILE.exists():
        with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDS)
            writer.writeheader()


def _read_all() -> list[dict]:
    _ensure_file()
    with open(CSV_FILE, "r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _write_all(rows: list[dict]):
    with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def log_signal(sig: dict, leverage: int):
    """Yeni sinyali CSV'ye kaydeder."""
    _ensure_file()
    rows = _read_all()
    new_id = len(rows) + 1
    row = {
        "id": new_id,
        "timestamp": datetime.utcnow().isoformat(timespec="seconds"),
        "symbol": sig["symbol"],
        "direction": sig["direction"],
        "entry": f"{sig['entry']:.8f}",
        "sl": f"{sig['sl']:.8f}",
        "tp1": f"{sig['tp1']:.8f}",
        "tp2": f"{sig['tp2']:.8f}",
        "risk_pct": f"{sig['risk_pct']:.2f}",
        "reward_pct": f"{sig['reward_pct']:.2f}",
        "rr_ratio": f"{sig['rr_ratio']:.2f}",
        "leverage": leverage,
        "status": "OPEN",
        "result": "",
        "pnl_pct": "",
        "closed_at": "",
        "reasons": " | ".join(sig["reasons"]),
    }
    rows.append(row)
    _write_all(rows)
    return new_id


def update_open_signals():
    """
    Acik sinyallerin durumunu gunceller.
    Her sinyal icin son fiyat cekilir, SL/TP1/TP2 kontrol edilir.
    """
    rows = _read_all()
    if not rows:
        return []

    updates = []  # bildirim icin

    # Sembol bazinda son fiyatlari cache'le
    price_cache: dict[str, float] = {}

    for row in rows:
        if row["status"] in ("SL_HIT", "TP2_HIT", "CLOSED"):
            continue
        if row["status"] not in ("OPEN", "TP1_HIT"):
            continue

        symbol = row["symbol"]
        if symbol not in price_cache:
            price = mexc_client.get_current_price(symbol)
            if price is None:
                continue
            price_cache[symbol] = price
        price = price_cache[symbol]

        entry = float(row["entry"])
        sl    = float(row["sl"])
        tp1   = float(row["tp1"])
        tp2   = float(row["tp2"])
        direction = row["direction"]

        new_status = row["status"]
        result = row.get("result", "")
        closed = False

        if direction == "LONG":
            # SL kontrol
            if price <= sl:
                if row["status"] == "TP1_HIT":
                    # TP1 vurdu, SL'i breakeven yap kabul et: result = PARTIAL
                    new_status = "CLOSED"
                    result = "PARTIAL"  # Yari karli kapatildi
                    pnl = ((tp1 - entry) / entry) * 50  # %50 pozisyon TP1
                else:
                    new_status = "SL_HIT"
                    result = "LOSS"
                    pnl = ((sl - entry) / entry) * 100
                closed = True
            # TP2 kontrol
            elif price >= tp2:
                new_status = "TP2_HIT"
                result = "WIN"
                # %50 TP1 + %50 TP2
                pnl_part1 = ((tp1 - entry) / entry) * 50
                pnl_part2 = ((tp2 - entry) / entry) * 50
                pnl = pnl_part1 + pnl_part2
                closed = True
            # TP1 kontrol
            elif row["status"] == "OPEN" and price >= tp1:
                new_status = "TP1_HIT"
                result = ""  # hala acik, devam ediyor
                pnl = 0
        else:  # SHORT
            if price >= sl:
                if row["status"] == "TP1_HIT":
                    new_status = "CLOSED"
                    result = "PARTIAL"
                    pnl = ((entry - tp1) / entry) * 50
                else:
                    new_status = "SL_HIT"
                    result = "LOSS"
                    pnl = ((entry - sl) / entry) * 100
                closed = True
            elif price <= tp2:
                new_status = "TP2_HIT"
                result = "WIN"
                pnl_part1 = ((entry - tp1) / entry) * 50
                pnl_part2 = ((entry - tp2) / entry) * 50
                pnl = pnl_part1 + pnl_part2
                closed = True
            elif row["status"] == "OPEN" and price <= tp1:
                new_status = "TP1_HIT"
                result = ""
                pnl = 0

        if new_status != row["status"]:
            row["status"] = new_status
            if closed:
                row["result"] = result
                row["pnl_pct"] = f"{pnl:.2f}"
                row["closed_at"] = datetime.utcnow().isoformat(timespec="seconds")
            updates.append({
                "id": row["id"],
                "symbol": symbol,
                "direction": direction,
                "status": new_status,
                "result": result,
                "pnl_pct": row.get("pnl_pct", ""),
                "price": price,
            })

    _write_all(rows)
    return updates


def get_stats(days: int | None = None) -> dict:
    """
    Performans istatistikleri uretir.
    days=None -> tum zamanlar, days=7 -> son 7 gun.
    """
    rows = _read_all()
    closed = [r for r in rows if r["status"] in ("TP2_HIT", "SL_HIT", "CLOSED")]

    if days is not None:
        cutoff = datetime.utcnow() - timedelta(days=days)
        closed = [r for r in closed
                  if r.get("closed_at") and datetime.fromisoformat(r["closed_at"]) >= cutoff]

    total = len(closed)
    wins = len([r for r in closed if r["result"] == "WIN"])
    losses = len([r for r in closed if r["result"] == "LOSS"])
    partials = len([r for r in closed if r["result"] == "PARTIAL"])

    pnls = [float(r["pnl_pct"]) for r in closed if r.get("pnl_pct")]
    total_pnl = sum(pnls) if pnls else 0
    avg_pnl = (total_pnl / len(pnls)) if pnls else 0

    win_rate = ((wins + partials * 0.5) / total * 100) if total > 0 else 0

    open_count = len([r for r in rows if r["status"] in ("OPEN", "TP1_HIT")])

    return {
        "total_closed": total,
        "wins": wins,
        "losses": losses,
        "partials": partials,
        "win_rate": win_rate,
        "total_pnl": total_pnl,
        "avg_pnl": avg_pnl,
        "open_count": open_count,
    }


def format_weekly_summary() -> str:
    """Haftalik ozeti Telegram mesaj formatinda dondurur."""
    s7  = get_stats(days=7)
    sall = get_stats(days=None)

    msg = f"""
📊 <b>HAFTALIK PERFORMANS RAPORU</b>

<b>━━━ SON 7 GUN ━━━</b>
✅ Kazanan: {s7['wins']}
❌ Kaybeden: {s7['losses']}
🟡 Kismi: {s7['partials']}
🎯 Win Rate: <b>{s7['win_rate']:.1f}%</b>
💰 Toplam P&L: <b>{s7['total_pnl']:+.2f}%</b>
📈 Ortalama: {s7['avg_pnl']:+.2f}% / sinyal

<b>━━━ TUM ZAMANLAR ━━━</b>
Toplam Kapali: {sall['total_closed']}
Win Rate: {sall['win_rate']:.1f}%
Toplam P&L: {sall['total_pnl']:+.2f}%

🔓 Su an acik: <b>{sall['open_count']} pozisyon</b>

<i>Not: P&L kaldiracsiz hesaplanmistir. {_get_leverage_note()}</i>
"""
    return msg.strip()


def _get_leverage_note() -> str:
    try:
        import config
        return f"5x kaldirac ile bu rakamlari 5 ile carp."
    except Exception:
        return ""


def format_status_change(update: dict) -> str:
    """SL/TP gerceklesince Telegram bildirimi."""
    status = update["status"]
    symbol = update["symbol"]
    direction = update["direction"]

    if status == "TP1_HIT":
        return (f"🎯 <b>{symbol} {direction}</b> - TP1 vuruldu\n"
                f"Yari pozisyonu kapatabilirsin. SL'i girise (break-even) cek.")
    elif status == "TP2_HIT":
        return (f"🏆 <b>{symbol} {direction}</b> - TP2 vuruldu! KAZANC\n"
                f"P&L: <b>{update['pnl_pct']}%</b> (kaldiracsiz)")
    elif status == "SL_HIT":
        return (f"🛑 <b>{symbol} {direction}</b> - Stop Loss vuruldu\n"
                f"P&L: <b>{update['pnl_pct']}%</b>")
    elif status == "CLOSED":
        return (f"✅ <b>{symbol} {direction}</b> - Kismi karla kapandi\n"
                f"TP1 sonrasi SL'e dondu. P&L: <b>{update['pnl_pct']}%</b>")
    return f"{symbol} durum: {status}"


def is_weekly_summary_time() -> bool:
    """Pazar gunu 20:00 (Istanbul) icin kontrol. Sade tutuldu."""
    now = datetime.utcnow()
    # UTC 17:00 = Istanbul 20:00 (yaz saati varsa 19:00 UTC)
    return now.weekday() == 6 and now.hour == 17 and now.minute < 5
