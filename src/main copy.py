from matplotlib import ticker
import yfinance as yf
import pandas as pd
import argparse as arg
from indicators import Indicators
from conditions import Conditions
from strategy import Strategy
from backtester import Backtester
from utils import get_bist_symbols_fast

import warnings
warnings.filterwarnings("ignore")

def main():
    parser = arg.ArgumentParser(description="Gap Strategy for Algoritmik Trading with Backtest tool.")


    parser.add_argument('--start', type=str, default="2026-04-27", 
                        help="Başlangıç tarihi (Format: YYYY-MM-DD)")
    parser.add_argument('--end', type=str, default=None, 
                        help="Bitiş tarihi (Format: YYYY-MM-DD). Boş bırakılırsa bugünü alır.")
    parser.add_argument('--interval', type=str, default="1m", 
                        help="Veri frekansı (Örn: 1D, 1wk, 1mo)")
    
    args = parser.parse_args()

    tickers = [i + ".IS" for i in get_bist_symbols_fast()] # İlk 10 hisseyi alıyoruz
    if args.end:
        data = yf.download(tickers, start=args.start, end=args.end, interval=args.interval)
    else:
        data = yf.download(tickers, start=args.start, interval=args.interval)
    #print(data.head())

    if isinstance(data.columns, pd.MultiIndex):
        data.columns = [ ' '.join(col_tuple) for col_tuple in data.columns.to_flat_index()]
        data.drop(columns=[col for col in data.columns if 'Adj Close' in col], inplace=True, axis=1)
    for ticker in tickers:
        columns_list = [col for col in data.columns if ticker in col]
        if sum(data[columns_list].notna().sum().to_dict().values()) == 0:
            print(f"Uyarı: {ticker} için veri bulunamadı ve atlanacak.")
            tickers.remove(ticker)
            data = data.drop(columns=columns_list, axis=1)
    #print(data.columns)
    print(f"[*] Backtest başlatılıyor...")
    print(f"[*] Tickers: {tickers} | Başlangıç: {args.start} | Frekans: {args.interval}")   

    obj_ind = Indicators(data=data)
    data = obj_ind.get_calculated_data()
    print(f"[*] Hesaplamalar tamamlandı. Shape: {data.shape}")
    print(data.columns)    #print(data.head())

    conditioner = Conditions(data, tickers=tickers)
    data = conditioner.set_conditions()
    #print(data.head())

    obj_strategy = Strategy(data, tickers)
    data = obj_strategy.classify()
    son_gapler = []

    for ticker in tickers:
        gap_kolonu = f'{ticker}_Gap_Type'
        
        # İlgili hisse için 'None' olmayan tüm satırları filtrele
        gecerli_gapler = data[data[gap_kolonu] != 'None']
        
        if not gecerli_gapler.empty:
            # En son geçerli gap'in yaşandığı satırı alıyoruz
            son_satir = gecerli_gapler.iloc[-1]
            
            # Eğer index'iniz datetime ise, gap'in ne zaman gerçekleştiğini de yakalayabiliriz
            tarih = son_satir.name 
            gap_turu = son_satir[gap_kolonu]
            
            if gap_turu  in ['Breakaway Up', 'Runaway Up', 'Exhaustion Down']:
                son_gapler.append(ticker)
                

    print(f"Son gap türü 'Breakaway Up', 'Runaway Up' veya 'Exhaustion Down' olan hisseler: {son_gapler}")

    backtester = Backtester(data = data, tickers=son_gapler)
    results = backtester.get_ticker_results()
    combined_result = backtester.get_combined_results()


if __name__ == "__main__":
    main()

#/usr/local/bin/python /workspaces/Algorithmic_trading/src/main.py  --tickers AKBNK.IS TUPRS.IS YKBNK.IS
#/usr/local/bin/python /workspaces/Algorithmic_trading/src/main.py  --tickers AKBNK.IS TUPRS.IS YKBNK.IS --start 2026-01-01