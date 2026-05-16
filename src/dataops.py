"""from dotenv import load_dotenv
import os
import pandas as pd
import requests
import finnhub
load_dotenv()

# ---------- CONFIG ----------
API_KEY = os.getenv("FINNHUB_API_KEY")
if not API_KEY:
    raise ValueError("FINNHUB_API_KEY .env'de bulunamadı!")
finnhub_client = finnhub.Client(api_key=API_KEY)

from tenacity import retry, stop_after_attempt, wait_exponential 
BASE_URL = "https://finnhub.io/api/v1/global-filings/search?token=d8180fpr01qler4hbc1gd8180fpr01qler4hbc20"


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def fetch_quote(symbol):
    data = finnhub_client.quote(symbol)
    if not data or data.get('c') == 0:
        raise ValueError(f"Quote API error: {data}")
    return data

from datetime import date, datetime, timedelta
SYMBOL = "AAPL"
today = date.today()
from_ts = int((pd.Timestamp(today) - pd.Timedelta(days=1)).timestamp())
to_ts = int(pd.Timestamp(today).timestamp())
print(f"Fetching data for {SYMBOL} from {datetime.fromtimestamp(from_ts)} to {datetime.fromtimestamp(to_ts)}...")
raw = fetch_quote(SYMBOL)
print(f"The response for {SYMBOL} is: {raw}")



"""

import yfinance as yf
import pandas as pd
from datetime import datetime
import json
import os

def fetch_live_data_yf(symbol="AAPL"):
    """Yahoo Finance ile anlik alis/satis ve fiyat verisi cek"""
    ticker = yf.Ticker(symbol)
    
    # 1. Anlik fiyat bilgisi (Bid/Ask dahil)
    # fast_info daha hizlidir, quote() ise detaylidir.
    info = ticker.info
    
    # 2. Gercek zamanli veri
    data = {
        "timestamp": datetime.now().isoformat(),
        "symbol": symbol,
        "bid": info.get('bid', 0),
        "ask": info.get('ask', 0),
        "current_price": info.get('regularMarketPrice', info.get('currentPrice')),
        "day_high": info.get('dayHigh'),
        "day_low": info.get('dayLow'),
        "volume": info.get('volume'),
        # Bazı durumlarda bid/ask icin su alternatif de kullanilabilir:
        "market_state": info.get('marketState')
    }
    
    return data

def run_pipeline_yf():
    symbol = "AAPL"
    print(f"{symbol} icin veri cekiliyor...")
    
    # Veriyi al
    live_data = fetch_live_data_yf(symbol)
    
    # Ekrana yazdir
    print(f"Alis (Bid): {live_data['bid']}")
    print(f"Satis (Ask): {live_data['ask']}")
    print(f"Son Fiyat: {live_data['current_price']}")
    
    # Bronze katmani (JSON)
    os.makedirs("./bronze", exist_ok=True)
    with open(f"./bronze/{symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", "w") as f:
        json.dump(live_data, f, indent=2)
    
    # Silver katmani (Parquet)
    df = pd.DataFrame([live_data])
    os.makedirs("./silver", exist_ok=True)
    df.to_parquet(f"./silver/{symbol}_live.parquet", index=False)
    
    print("Pipeline basariyla tamamlandi.")

if __name__ == "__main__":
    # pip install yfinance pandas pyarrow
    run_pipeline_yf()