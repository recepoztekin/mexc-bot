"""
MEXC Futures veri cekme modulu.
Sadece public endpoint kullanir - API key gerekmez.
"""

import requests
import pandas as pd
from datetime import datetime
import config


def fetch_klines(symbol: str, interval: str = config.TIMEFRAME, limit: int = config.KLINES_LIMIT) -> pd.DataFrame | None:
    """
    MEXC Futures'tan mum verisi ceker.
    Donen DataFrame: time, open, high, low, close, volume
    """
    url = f"{config.MEXC_FUTURES_BASE}{config.KLINE_ENDPOINT.format(symbol=symbol)}"
    params = {"interval": interval}

    try:
        r = requests.get(url, params=params, timeout=15)
        r.raise_for_status()
        data = r.json()

        if not data.get("success"):
            print(f"[!] {symbol} icin veri alinamadi: {data}")
            return None

        d = data["data"]
        # MEXC formatinda data ayri listelerde gelir
        df = pd.DataFrame({
            "time":   d["time"],
            "open":   d["open"],
            "high":   d["high"],
            "low":    d["low"],
            "close":  d["close"],
            "volume": d["vol"],
        })

        # Sayisal donusturmeler
        for c in ["open", "high", "low", "close", "volume"]:
            df[c] = pd.to_numeric(df[c], errors="coerce")

        df["datetime"] = pd.to_datetime(df["time"], unit="s")
        df = df.dropna().reset_index(drop=True)

        # Son N mumu al
        if len(df) > limit:
            df = df.iloc[-limit:].reset_index(drop=True)

        return df

    except Exception as e:
        print(f"[X] {symbol} mum verisi cekilirken hata: {e}")
        return None


def get_current_price(symbol: str) -> float | None:
    """Anlik fiyat (son mum kapanisi)."""
    df = fetch_klines(symbol, limit=2)
    if df is None or df.empty:
        return None
    return float(df["close"].iloc[-1])


if __name__ == "__main__":
    # Test
    print("MEXC client testi...")
    df = fetch_klines("BTC_USDT")
    if df is not None:
        print(f"Cekilen mum sayisi: {len(df)}")
        print(df.tail(3))
