"""
Teknik indikator hesaplama modulu.
Pandas ve numpy ile saf hesaplama - harici TA kutuphanesi gerekmez.
"""

import pandas as pd
import numpy as np


def ema(series: pd.Series, period: int) -> pd.Series:
    return series.ewm(span=period, adjust=False).mean()


def rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.ewm(alpha=1/period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/period, adjust=False).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
    ema_fast = ema(series, fast)
    ema_slow = ema(series, slow)
    macd_line = ema_fast - ema_slow
    signal_line = ema(macd_line, signal)
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram


def bollinger_bands(series: pd.Series, period: int = 20, std: float = 2.0):
    mid = series.rolling(period).mean()
    sd  = series.rolling(period).std()
    upper = mid + std * sd
    lower = mid - std * sd
    return upper, mid, lower


def atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    high_low = df["high"] - df["low"]
    high_close = (df["high"] - df["close"].shift()).abs()
    low_close = (df["low"] - df["close"].shift()).abs()
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    return tr.ewm(alpha=1/period, adjust=False).mean()


def add_all_indicators(df: pd.DataFrame, cfg) -> pd.DataFrame:
    """DataFrame'e tum indikatorleri ekler."""
    df = df.copy()
    df["ema_fast"] = ema(df["close"], cfg.EMA_FAST)
    df["ema_slow"] = ema(df["close"], cfg.EMA_SLOW)
    df["rsi"] = rsi(df["close"], cfg.RSI_PERIOD)
    macd_line, signal_line, hist = macd(df["close"], cfg.MACD_FAST, cfg.MACD_SLOW, cfg.MACD_SIGNAL)
    df["macd"] = macd_line
    df["macd_signal"] = signal_line
    df["macd_hist"] = hist
    upper, mid, lower = bollinger_bands(df["close"], cfg.BB_PERIOD, cfg.BB_STD)
    df["bb_upper"] = upper
    df["bb_mid"]   = mid
    df["bb_lower"] = lower
    df["atr"] = atr(df, cfg.ATR_PERIOD)
    df["vol_avg"] = df["volume"].rolling(cfg.VOLUME_LOOKBACK).mean()
    return df
