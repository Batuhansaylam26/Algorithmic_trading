from utils import get_unique_tickers
class Conditions:
    def __init__(self,data, tickers:list = None):
        self.data = data
        if tickers:
            self.tickers = tickers
        else:
            self.tickers = get_unique_tickers(data)


    def set_conditions(self):
        for prefix in self.tickers:
            self.get_gap(
                prefix=prefix,
                col_name_low= f'Low {prefix}',
                col_name_high= f'High {prefix}'
            )

            self.get_exhaustion_gap(
                prefix=prefix,
                col_name_open= f'Open {prefix}',
                col_name_close= f'Close {prefix}'
            )

            self.volume_filter(
                prefix=prefix,
                col_name_vol= f'{prefix}_SMA_Short',
                col_name_vol_sma= f'{prefix}_SMA_Long'
            )

            self.get_breakout(
                prefix=prefix,
                col_name_low= f'Low {prefix}',
                col_name_high= f'High {prefix}',
                col_name_range_low= f'{prefix}_Range_Low',
                col_name_range_high= f'{prefix}_Range_High'
            )

            self.get_consolidation(
                prefix=prefix,
                col_name_adx = f'{prefix}_ADX',
                threshold= 25
            )
            self.get_trend_type(
                prefix=prefix,
                col_name_long_sma=f'{prefix}_SMA_Long',
                col_name_short_sma=f'{prefix}_SMA_Short',
            )

            self.get_sold_type(
                prefix=prefix,
                col_name_rsi=f'{prefix}_RSI',
                lower=30,
                upper=70
            )
        return self.data

    def get_gap(self,
                prefix:str, 
                col_name_low:str = 'Low', 
                col_name_high:str= 'High'
    )->None:

        self.data[f'{prefix}_gap_up']= self.data[col_name_low] > self.data[col_name_high].shift(1)
        self.data[f'{prefix}_gap_down']= self.data[col_name_high] < self.data[col_name_low].shift(1)

    def get_exhaustion_gap(self, 
                           prefix:str, 
                           col_name_open:str = 'Open', 
                           col_name_close:str= 'Close'
    )->None:

        self.data[f'{prefix}_exhaustion_gap_up']= self.data[col_name_open] > self.data[col_name_close].shift(1)
        self.data[f'{prefix}_exhaustion_gap_down'] = self.data[col_name_open] < self.data[col_name_close].shift(1)

    def volume_filter(self, 
                      prefix:str, 
                      col_name_vol:str = 'Volume', 
                      col_name_vol_sma:str = 'Vol_SMA'
    )->None:
        self.data[f'{prefix}_high_vol']= self.data[col_name_vol] > (1.5 * self.data[col_name_vol_sma])
        self.data[f'{prefix}_extreme_vol']= self.data[col_name_vol] > (2 * self.data[col_name_vol_sma])

    def get_breakout(self, 
                     prefix:str, 
                     col_name_low:str = 'Low', 
                     col_name_high:str= 'High',
                     col_name_range_low:str = 'Range_Low', 
                     col_name_range_high:str= 'Range_High'
    )->None:
        self.data[f'{prefix}_breakout_up'] = self.data[col_name_low] > self.data[col_name_range_high]
        self.data[f'{prefix}_breakout_down']= self.data[col_name_high] < self.data[col_name_range_low]

    def get_consolidation(self, 
                          prefix:str, 
                          col_name_adx:str = 'ADX', 
                          threshold:int = 25
    )->None:
        self.data[f'{prefix}_consolidation']= self.data[col_name_adx] < threshold

    def get_trend_type(self, 
                       prefix:str, 
                       col_name_short_sma:str = 'SMA_Short', 
                       col_name_long_sma:str= 'SMA_Long'
    )->None:
        self.data[f'{prefix}_uptrend'] = self.data[col_name_short_sma] > self.data[col_name_long_sma]
        self.data[f'{prefix}_downtrend'] = self.data[col_name_short_sma] < self.data[col_name_long_sma]

    def get_sold_type(self, 
                      prefix:str, 
                      col_name_rsi: str = 'RSI', 
                      lower: int = 30, 
                      upper:int =70 
    )->None:
        self.data[f'{prefix}_overbought'] = self.data[col_name_rsi] > upper
        self.data[f'{prefix}_oversold'] = self.data[col_name_rsi] < lower


