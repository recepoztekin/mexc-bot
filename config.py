"""
================================================
  MEXC FUTURES SINYAL BOTU - YAPILANDIRMA
================================================
Bu dosyada tum ayarlar yer alir.
Telegram token ve chat ID'ini buraya yaz.
"""

# ============ TELEGRAM AYARLARI ============
TELEGRAM_BOT_TOKEN = "BURAYA_BOTFATHER_TOKENINI_YAPISTIR"
TELEGRAM_CHAT_ID   = "BURAYA_KENDI_CHAT_IDINI_YAPISTIR"

# ============ TAKIP EDILECEK COINLER ============
# MEXC Futures sembol formati: BTC_USDT (alt cizgi ile)
SYMBOLS = [
    # Top 10
    "BTC_USDT",
    "ETH_USDT",
    "SOL_USDT",
    "BNB_USDT",
    "XRP_USDT",
    "ADA_USDT",
    "DOGE_USDT",
    "AVAX_USDT",
    "LINK_USDT",
    "POL_USDT",
    # Layer1 / Layer2
    "ARB_USDT",
    "OP_USDT",
    "SUI_USDT",
    "APT_USDT",
    "TON_USDT",
    "NEAR_USDT",
    "ATOM_USDT",
    # DeFi
    "UNI_USDT",
    "AAVE_USDT",
    "INJ_USDT",
    "LDO_USDT",
    # Meme
    "SHIB_USDT",
    "PEPE_USDT",
    "WIF_USDT",
    "BONK_USDT",
    # Diger
    "TRX_USDT",
    "ICP_USDT",
    "FIL_USDT",
    "RNDR_USDT",
    "FET_USDT",
]

# ============ ZAMAN DILIMI ============
# MEXC futures intervals: Min1, Min5, Min15, Min30, Min60, Hour4, Hour8, Day1, Week1, Month1
TIMEFRAME = "Hour4"   # 4 saatlik mum

# ============ STRATEJI PARAMETRELERI ============
EMA_FAST   = 50
EMA_SLOW   = 200
RSI_PERIOD = 14
RSI_LOW    = 40
RSI_HIGH   = 60
MACD_FAST  = 12
MACD_SLOW  = 26
MACD_SIGNAL = 9
BB_PERIOD  = 20
BB_STD     = 2
ATR_PERIOD = 14
VOLUME_MULTIPLIER = 1.5   # Hacim ortalamasinin kac kati olmali
VOLUME_LOOKBACK   = 20

# ============ RISK YONETIMI ============
ATR_SL_MULTIPLIER = 1.5   # Stop loss = ATR x 1.5
TP1_RR = 1.5              # Take profit 1 = Risk x 1.5
TP2_RR = 3.0              # Take profit 2 = Risk x 3.0
MIN_RR = 2.0              # Minimum risk/reward orani (filtreleme)
LEVERAGE_SUGGESTION = 5   # Onerilen kaldirac

# ============ BOT DAVRANISI ============
CHECK_INTERVAL_SECONDS = 60       # Kac saniyede bir kontrol etsin
SIGNAL_COOLDOWN_HOURS = 24        # Ayni coinde 2 sinyal arasi minimum sure
KLINES_LIMIT = 300                # Cekecegi mum sayisi (indikatorler icin yeterli)

# ============ MEXC API ============
MEXC_FUTURES_BASE = "https://contract.mexc.com"
KLINE_ENDPOINT    = "/api/v1/contract/kline/{symbol}"
