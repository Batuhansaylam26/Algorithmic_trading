import vectorbt as vbt
import pandas as pd 
import numpy as np
from utils import get_unique_tickers
class Backtester:
    def __init__(self,data, tickers:list = None, init_cash:int=10000, fees:float=None):
        self.data = data
        if tickers:
            self.tickers = tickers
        else:
            self.tickers = get_unique_tickers(data)

        self.entries = None
        self.exits = None
        self.init_cash = init_cash
        if not fees:
            self.fees = 0 
        else:
            self.fees = fees

        self.results = None

    def get_ticker_results(self)->dict:
        self.results = {}
        for ticker in self.tickers:
            print(f'------------------{ticker}------------------')
            self.entries = self.get_entries(
                col_name_gap=f'{ticker}_Gap_Type'
            )

            self.exits = self.get_exits(
                col_name_gap=f'{ticker}_Gap_Type'
            )
            self.clean_entries()
            result = self.backtest(col_name_close=f'Close {ticker}')
            self.results[ticker] = result
        return self.results

    


    def get_combined_results(self) -> vbt.Portfolio:
        # Sütunları ticker adları olacak şekilde boş sözlükler oluşturuyoruz
        close_dict = {}
        entries_dict = {}
        exits_dict = {}
        
        for ticker in self.tickers:
            print(f'Sinyaller hazırlanıyor: {ticker}')
            
            close_dict[ticker] = self.data[f'Close {ticker}']
            
            self.entries = self.get_entries(col_name_gap=f'{ticker}_Gap_Type')
            self.exits = self.get_exits(col_name_gap=f'{ticker}_Gap_Type')
            
            self.clean_entries() 
            
            # Temizlenmiş sinyalleri ilgili hissenin anahtarıyla (key) sözlüğe kaydet
            entries_dict[ticker] = self.entries
            exits_dict[ticker] = self.exits
            
        df_close = pd.DataFrame(close_dict)
        df_entries = pd.DataFrame(entries_dict)
        df_exits = pd.DataFrame(exits_dict)
        
        print("Çoklu varlık (Multi-Asset) backtesti çalıştırılıyor...")
        
        # 6. Tüm matrisleri tek seferde VectorBT'ye yolla
        self.master_portfolio = vbt.Portfolio.from_signals(
            df_close,
            entries=df_entries,
            exits=df_exits,
            init_cash=self.init_cash,        
            fees=self.fees,           
            direction='longonly',
            freq='1D',
            group_by=True           # True olduğunda tüm hisseleri tek portföyde birleştirir.
        )
        
        print("--- MASTER PORTFOLIO BACKTEST SONUÇLARI ---")
        print(self.master_portfolio.stats())
        
        return self.master_portfolio
        



    def clean_entries(self)->None: # Bu metot çakışan sinyalleri (aynı gün hem al hem sat) otomatik temizler.
        self.entries, self.exits = self.entries.vbt.signals.clean(self.exits)


    def get_entries(self, col_name_gap:str = "Gap_Type"):
        return self.data[col_name_gap].isin(['Breakaway Up', 'Runaway Up', 'Exhaustion Down'])

    def get_exits(self, col_name_gap:str = "Gap_Type"):
        return self.data[col_name_gap].isin(['Breakaway Down','Exhaustion Up'])

    def backtest(self, col_name_close:str = "Close"):
        portfolio = vbt.Portfolio.from_signals(
            self.data[col_name_close],            
            entries=self.entries,        
            exits=self.exits,            # Zıt sinyalle çıkışı kapattık, artık TP/SL ile çıkacak
            init_cash=self.init_cash,    
            fees=self.fees,              
            direction='longonly',   # Sadece hisse alım yönlü test
            freq='1D'               
        )

        print("--- RESULTS OF BACKTEST ---")
        print(portfolio.stats())
        
        return portfolio