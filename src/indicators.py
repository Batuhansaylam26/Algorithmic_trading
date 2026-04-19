import talib.abstract as ta

class Indicators:
    def __init__(self,data):
        self.data = data


    def get_calculated_data(self):
        for col in self.data.columns:
            if 'Close' in col:
                prefix = col.lstrip('Close ')
                self.calculate_rsi(prefix=prefix, col_name=col)
                self.calculate_short_long_sma(prefix=prefix, col_name=col)
            elif 'Volume' in col:   
                prefix = col.lstrip('Volume ')    
                self.calculate_volume_sma(prefix=prefix, col_name=col)
            elif 'High' in col:
                prefix = col.lstrip('High ')  
                low_column = col.replace('High', 'Low')
                self.calculate_support_resistance(
                    prefix=prefix,
                    col_name_high=col,
                    col_name_low= low_column
                )
                close_column = col.replace('High', 'Close')
                self.calculate_adx(
                    prefix=prefix,
                    col_name_high=col,
                    col_name_close=close_column,
                    col_name_low=low_column,
                    timeperiod=14
                )
        return self.data


    def calculate_rsi(self, prefix:str, col_name:str = 'Close', timeperiod:int = 14):
        self.data[f'{prefix}_RSI'] = ta.RSI(
            self.data[col_name], 
            timeperiod = timeperiod
        )

    def calculate_short_long_sma(self,
                                 prefix:str, 
                                 col_name:str = 'Close', 
                                 timeperiod_short:int = 20, 
                                 timeperiod_long:int = 50):
        self.data[f'{prefix}_SMA_Short'] = ta.SMA(
            self.data[col_name], 
            timeperiod = timeperiod_short
        )
        
        self.data[f'{prefix}_SMA_Long'] = ta.SMA(
            self.data[col_name], 
            timeperiod = timeperiod_long
        )

    def calculate_volume_sma(self, prefix:str, col_name:str = 'Volume', timeperiod = 20):
        self.data[f"{prefix}_Vol_SMA"] = ta.SMA(
            self.data[col_name], 
            timeperiod
        )

    def calculate_support_resistance(self, 
                                     prefix:str, 
                                     col_name_high:str = 'High', 
                                     col_name_low:str = 'Low', 
                                     timeperiod = 20):
        self.data[f'{prefix}_Range_High'] = self.data[col_name_high].rolling(window=timeperiod).max().shift(1)
        self.data[f'{prefix}_Range_Low'] = self.data[col_name_low].rolling(window=timeperiod).min().shift(1)

    def calculate_adx(self,
                      prefix:str,
                      col_name_high:str = 'High', 
                      col_name_low:str = 'Low',
                      col_name_close:str = 'Close',
                      timeperiod:int = 14
        ):
        self.data[f"{prefix}_ADX"] = ta.ADX(
            self.data[col_name_high], 
            self.data[col_name_low], 
            self.data[col_name_close], 
            timeperiod=timeperiod
        )
