# MEXC Futures Sinyal Botu — 4H Swing

Yüksek win rate odaklı, **5 konfirmasyon** koşulu ile çalışan vadeli işlem sinyal botu.
MEXC Futures'tan canlı veri çeker, Telegram'a sinyal gönderir ve CMD ekranında renkli çıktı verir.

## Klasör İçeriği

| Dosya | Görevi |
|---|---|
| `config.py` | Tüm ayarlar (Telegram token, coinler, parametreler) |
| `mexc_client.py` | MEXC Futures'tan mum verisi çekme |
| `indicators.py` | EMA, RSI, MACD, Bollinger, ATR hesaplama |
| `strategy.py` | 5 koşullu sinyal mantığı + SL/TP hesaplama |
| `telegram_bot.py` | Telegram'a mesaj gönderme |
| `main.py` | Ana çalıştırma scripti |
| `tracker.py` | Sinyal performans takibi (CSV) |
| `report.py` | Anlık rapor alma scripti |
| `signals.csv` | Tüm sinyallerin kaydı (otomatik oluşur) |
| `requirements.txt` | Gerekli Python paketleri |

## Strateji Mantığı

Bir sinyal üretilmesi için **5 koşulun aynı anda** sağlanması gerekir:

**LONG sinyali:**
1. Fiyat EMA200'ün üstünde **ve** EMA50 > EMA200 (yukarı trend)
2. RSI 40–60 arasında **ve** yükseliyor (momentum dönüşü)
3. MACD histogram pozitif **ve** artıyor
4. Fiyat Bollinger orta bandının üstünde
5. Son mum hacmi 20-mum ortalamasının **1.5 katından** fazla

**SHORT sinyali:** Yukarıdakilerin tam tersi.

**Ek filtreler:**
- Risk/Reward minimum **1:2** olmalı
- Aynı coinde **24 saatte tek sinyal** (overtrading önlemi)
- SL = ATR × 1.5 (volatiliteye göre dinamik)
- TP1 = Risk × 1.5, TP2 = Risk × 3

## Kurulum (Adım Adım)

### 1) Python kur (yoksa)
https://python.org → Python 3.10+ indir, kurulumda "Add to PATH" işaretle.

### 2) Paketleri yükle
CMD/Terminal aç, bot klasörüne gir ve şunu çalıştır:
```bash
pip install -r requirements.txt
```

### 3) Telegram ayarlarını gir
`config.py` dosyasını aç, şu 2 satırı düzenle:
```python
TELEGRAM_BOT_TOKEN = "123456:ABCdef..."   # BotFather'dan aldığın token
TELEGRAM_CHAT_ID   = "987654321"          # Senin chat ID'in
```

> **Chat ID bulamıyorsan:** Telegram'da `@userinfobot` aramasını yap, ona /start de, sana ID'ini verir.

### 4) Botu çalıştır
**Sürekli çalışsın (önerilen):**
```bash
python main.py
```

**Sadece bir kez tarasın:**
```bash
python main.py --once
```

Bot başlayınca Telegram'a "Bot başlatıldı" mesajı atar. Sinyal yakaladığında hem CMD'ye renkli yazar, hem Telegram'a güzel formatlı mesaj gönderir.

## Önerilen Kullanım

- **Kaldıraç:** 3x–5x (4H'de daha fazlası yüksek likidasyon riski)
- **Pozisyon büyüklüğü:** Bakiyenin **%2–3'ü** risk olacak şekilde
- **SL'i mutlaka koy** — bot SL hesaplıyor ama emir vermiyor, sen koyacaksın
- **TP1'de yarıyı kapat**, SL'i girişe çek (break-even), TP2'yi bekle

## İnce Ayarlar

`config.py` içinden:
- `SYMBOLS`: takip edilecek coinleri düzenle
- `TIMEFRAME`: `Hour1` veya `Min15` yapabilirsin (daha çok sinyal, daha az kalite)
- `VOLUME_MULTIPLIER`: 1.5'i 1.2'ye düşürürsen daha çok sinyal alırsın
- `MIN_RR`: 2.0'ı 1.5'e düşürürsen daha çok sinyal, ama win rate düşer
- `SIGNAL_COOLDOWN_HOURS`: aynı coinde sinyal aralığı

## Performans Takibi

Bot her sinyali otomatik olarak `signals.csv` dosyasına kaydeder.
Her tarama döngüsünde açık sinyallerin canlı fiyatını kontrol eder:
- **TP1 vurulursa:** Telegram'a "yarı kapat, SL'i breakeven yap" bildirimi
- **TP2 vurulursa:** Kazanç bildirimi + P&L
- **SL vurulursa:** Kayıp bildirimi + P&L

Her pazar 20:00 (Istanbul) **haftalık özet** Telegram'a gelir.

**Anlık rapor almak için:**
```bash
python report.py
```

**CSV'yi bilgisayara indirmek için** (WinSCP veya scp):
```bash
scp -i ssh-key.key ubuntu@SUNUCU_IP:/home/ubuntu/mexc-bot/signals.csv .
```

Excel/Google Sheets'te açıp analiz edebilirsin.

## Uyarı

Bu bot sana sinyal **önerir**, otomatik işlem **açmaz**. Tüm işlemler senin sorumluluğundadır.
Pozisyon açmadan önce her zaman kendi analizini de yap. SL koymadan asla işlem alma.
