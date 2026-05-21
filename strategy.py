"""
Sinyal uretme stratejisi.
5 kosullu konfirmasyon sistemi - yuksek win rate odakli.
"""

import pandas as pd
import config


def check_long_signal(df: pd.DataFrame) -> tuple[bool, list[str]]:
    """Long sinyali icin 5 kosul kontrolu. (True/False, gerekceler)"""
    if len(df) < config.EMA_SLOW + 5:
        return False, ["Yetersiz veri"]

    last = df.iloc[-1]
    prev = df.iloc[-2]
    reasons = []

    # 1) Trend filtresi: Fiyat EMA200 ustunde + EMA50 > EMA200
    cond1 = last["close"] > last["ema_slow"] and last["ema_fast"] > last["ema_slow"]
    if cond1:
        reasons.append("Trend yukari (Fiyat > EMA200, EMA50 > EMA200)")

    # 2) RSI momentum bolgesi: 40-60 arasinda (asiri alimda degil, momentum dogusu)
    cond2 = config.RSI_LOW <= last["rsi"] <= config.RSI_HIGH and last["rsi"] > prev["rsi"]
    if cond2:
        reasons.append(f"RSI momentum yukari ({last['rsi']:.1f})")

    # 3) MACD histogram pozitife dondu veya pozitif ve artiyor
    cond3 = last["macd_hist"] > 0 and last["macd_hist"] > prev["macd_hist"]
    if cond3:
        reasons.append("MACD histogram pozitif ve artiyor")

    # 4) Bollinger: Fiyat orta bandi yukari kirdi veya ust banda dogru
    cond4 = last["close"] > last["bb_mid"] and prev["close"] <= prev["bb_mid"]
    # Alternatif: fiyat orta bandin uzerinde ve ust banda dogru hareket
    cond4_alt = last["close"] > last["bb_mid"] and last["close"] > prev["close"]
    cond4_final = cond4 or cond4_alt
    if cond4_final:
        reasons.append("Bollinger orta bandi ustunde ve yukari")

    # 5) Hacim teyidi
    cond5 = last["volume"] > last["vol_avg"] * config.VOLUME_MULTIPLIER
    if cond5:
        reasons.append(f"Hacim patlamasi ({last['volume']/last['vol_avg']:.1f}x ortalama)")

    all_ok = cond1 and cond2 and cond3 and cond4_final and cond5
    return all_ok, reasons


def check_short_signal(df: pd.DataFrame) -> tuple[bool, list[str]]:
    """Short sinyali icin 5 kosul kontrolu."""
    if len(df) < config.EMA_SLOW + 5:
        return False, ["Yetersiz veri"]

    last = df.iloc[-1]
    prev = df.iloc[-2]
    reasons = []

    # 1) Trend asagi
    cond1 = last["close"] < last["ema_slow"] and last["ema_fast"] < last["ema_slow"]
    if cond1:
        reasons.append("Trend asagi (Fiyat < EMA200, EMA50 < EMA200)")

    # 2) RSI momentum asagi
    cond2 = config.RSI_LOW <= last["rsi"] <= config.RSI_HIGH and last["rsi"] < prev["rsi"]
    if cond2:
        reasons.append(f"RSI momentum asagi ({last['rsi']:.1f})")

    # 3) MACD histogram negatif ve azaliyor
    cond3 = last["macd_hist"] < 0 and last["macd_hist"] < prev["macd_hist"]
    if cond3:
        reasons.append("MACD histogram negatif ve azaliyor")

    # 4) Bollinger orta bandi asagi kirdi
    cond4 = last["close"] < last["bb_mid"] and prev["close"] >= prev["bb_mid"]
    cond4_alt = last["close"] < last["bb_mid"] and last["close"] < prev["close"]
    cond4_final = cond4 or cond4_alt
    if cond4_final:
        reasons.append("Bollinger orta bandi altinda ve asagi")

    # 5) Hacim
    cond5 = last["volume"] > last["vol_avg"] * config.VOLUME_MULTIPLIER
    if cond5:
        reasons.append(f"Hacim patlamasi ({last['volume']/last['vol_avg']:.1f}x ortalama)")

    all_ok = cond1 and cond2 and cond3 and cond4_final and cond5
    return all_ok, reasons


def calculate_trade_levels(df: pd.DataFrame, direction: str) -> dict:
    """Giris, SL, TP1, TP2 seviyelerini hesaplar."""
    last = df.iloc[-1]
    entry = float(last["close"])
    atr_val = float(last["atr"])
    sl_distance = atr_val * config.ATR_SL_MULTIPLIER

    if direction == "LONG":
        sl  = entry - sl_distance
        tp1 = entry + sl_distance * config.TP1_RR
        tp2 = entry + sl_distance * config.TP2_RR
    else:  # SHORT
        sl  = entry + sl_distance
        tp1 = entry - sl_distance * config.TP1_RR
        tp2 = entry - sl_distance * config.TP2_RR

    risk_pct = (abs(entry - sl) / entry) * 100
    reward_pct = (abs(entry - tp2) / entry) * 100
    rr_ratio = reward_pct / risk_pct if risk_pct > 0 else 0

    return {
        "entry": entry,
        "sl": sl,
        "tp1": tp1,
        "tp2": tp2,
        "risk_pct": risk_pct,
        "reward_pct": reward_pct,
        "rr_ratio": rr_ratio,
        "atr": atr_val,
    }


def evaluate(symbol: str, df: pd.DataFrame) -> dict | None:
    """
    Bir sembol icin sinyal degerlendirmesi yapar.
    Sinyal varsa dict doner, yoksa None.
    """
    long_ok, long_reasons = check_long_signal(df)
    short_ok, short_reasons = check_short_signal(df)

    if long_ok:
        levels = calculate_trade_levels(df, "LONG")
        if levels["rr_ratio"] >= config.MIN_RR:
            return {
                "symbol": symbol,
                "direction": "LONG",
                "reasons": long_reasons,
                **levels,
            }

    if short_ok:
        levels = calculate_trade_levels(df, "SHORT")
        if levels["rr_ratio"] >= config.MIN_RR:
            return {
                "symbol": symbol,
                "direction": "SHORT",
                "reasons": short_reasons,
                **levels,
            }

    return None
