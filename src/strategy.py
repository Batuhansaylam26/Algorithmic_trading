import numpy as np
from utils import get_unique_tickers
class Strategy:
    def __init__(self,data, tickers:list):
        self.data = data
        if tickers:
            self.tickers = tickers
        else:
            self.tickers = get_unique_tickers(data)
        self.choices = [
            'Breakaway Up', 'Breakaway Down',
            'Exhaustion Up', 'Exhaustion Down',
            'Runaway Up', 'Runaway Down',
            'Common Up', 'Common Down'
        ]

    def classify(self):
        for prefix in self.tickers:
            conditions = self.get_conditions(prefix)
            self.data[f'{prefix}_Gap_Type'] = np.select(conditions, self.choices, default='None')
        return self.data

    
    def get_conditions(self,prefix):
        return  [
            # Breakaway: Direnç/Destek kırılımı + Yüksek Hacim
            (self.data[f'{prefix}_gap_up'] & self.data[f'{prefix}_breakout_up'] & self.data[f'{prefix}_high_vol'] & self.data[f'{prefix}_consolidation'].shift(1)),
            (self.data[f'{prefix}_gap_down'] & self.data[f'{prefix}_breakout_down'] & self.data[f'{prefix}_high_vol'] & self.data[f'{prefix}_consolidation'].shift(1)),
            
            # Exhaustion: Trend içi aşırı bölge + Ekstrem Hacim
            (self.data[f'{prefix}_exhaustion_gap_up'] & self.data[f'{prefix}_uptrend'] & self.data[f'{prefix}_overbought'] & self.data[f'{prefix}_extreme_vol'] & ~self.data[f'{prefix}_consolidation']),
            (self.data[f'{prefix}_exhaustion_gap_down'] & self.data[f'{prefix}_downtrend'] & self.data[f'{prefix}_oversold'] & self.data[f'{prefix}_extreme_vol'] & ~self.data[f'{prefix}_consolidation']),
            
            # Runaway: Trend içi gap + Kırılım yok + Aşırı bölgede değil
            (self.data[f'{prefix}_gap_up'] & self.data[f'{prefix}_uptrend'] & ~self.data[f'{prefix}_breakout_up'] & ~self.data[f'{prefix}_overbought'] & ~self.data[f'{prefix}_consolidation']),
            (self.data[f'{prefix}_gap_down'] & self.data[f'{prefix}_downtrend'] & ~self.data[f'{prefix}_breakout_down'] & ~self.data[f'{prefix}_oversold'] & ~self.data[f'{prefix}_consolidation']),
            
            # Common: Range içi, düşük hacimli (yukarıdaki şartları sağlamayan)
            (self.data[f'{prefix}_gap_up'] & ~self.data[f'{prefix}_breakout_up'] & ~self.data[f'{prefix}_high_vol']),
            (self.data[f'{prefix}_gap_down'] & ~self.data[f'{prefix}_breakout_down'] & ~self.data[f'{prefix}_high_vol'])
        ]

    