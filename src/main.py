import yfinance as yf
import pandas as pd
import argparse as arg
from indicators import Indicators
from conditions import Conditions
from strategy import Strategy
from backtester import Backtester
def main():
    parser = arg.ArgumentParser(description="Gap Strategy for Algoritmik Trading with Backtest tool.")

    parser.add_argument('--tickers', nargs='+', default=['MSFT', 'AAPL'], 
                        help="Test edilecek hisse sembolleri (Aralarında boşluk bırakarak yazın. Örn: AAPL MSFT TSLA)")
    parser.add_argument('--start', type=str, default="2015-01-01", 
                        help="Başlangıç tarihi (Format: YYYY-MM-DD)")
    parser.add_argument('--end', type=str, default=None, 
                        help="Bitiş tarihi (Format: YYYY-MM-DD). Boş bırakılırsa bugünü alır.")
    parser.add_argument('--interval', type=str, default="1D", 
                        help="Veri frekansı (Örn: 1D, 1wk, 1mo)")
    
    args = parser.parse_args()

    tickers = args.tickers
    if args.end:
        data = yf.download(tickers, start=args.start, end=args.end, interval=args.interval)
    else:
        data = yf.download(tickers, start=args.start, interval=args.interval)
    #print(data.head())

    if isinstance(data.columns, pd.MultiIndex):
        data.columns = [ ' '.join(col_tuple) for col_tuple in data.columns.to_flat_index()]
    #print(data.columns)
    print(f"[*] Backtest başlatılıyor...")
    print(f"[*] Tickers: {tickers} | Başlangıç: {args.start} | Frekans: {args.interval}")   

    obj_ind = Indicators(data=data)
    data = obj_ind.get_calculated_data()
    #print(data.head())

    conditioner = Conditions(data, tickers=tickers)
    data = conditioner.set_conditions()
    #print(data.head())

    obj_strategy = Strategy(data, tickers)
    data = obj_strategy.classify()
    #print(data.head())

    backtester = Backtester(data = data, tickers=tickers)
    results = backtester.get_ticker_results()
    combined_result = backtester.get_combined_results()


if __name__ == "__main__":
    main()

#/usr/local/bin/python /workspaces/Algorithmic_trading/src/main.py  --tickers AKBNK.IS TUPRS.IS YKBNK.IS
#/usr/local/bin/python /workspaces/Algorithmic_trading/src/main.py  --tickers AKBNK.IS TUPRS.IS YKBNK.IS --start 2026-01-01