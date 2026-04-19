def get_unique_tickers(data)->list:
    return [ i.lstrip('Close ') for i in data.columns if 'Close' in i ]