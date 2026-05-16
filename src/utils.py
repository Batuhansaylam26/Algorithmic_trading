import requests
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from tqdm.auto import tqdm
from dataclasses import dataclass

def get_bist_symbols_fast():
    # TradingView'in hisse tarayıcı (screener) arka plan URL'si
    url = "https://scanner.tradingview.com/turkey/scan"
    
    # Sadece Türkiye pazarındaki hisselerin "isimlerini" getirmesini istiyoruz
    payload = {
        "columns": ["name"],
        "filter": [
            {"left": "exchange", "operation": "equal", "right": "BIST"},
            {"left": "type", "operation": "equal", "right": "stock"}
        ],
        "range": [0, 1000] # İlk 1000 hisseyi getir
    }
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status() # Hata varsa yakala
        
        data = response.json()
        
        # Gelen JSON verisinden sadece hisse isimlerini ayıkla
        symbols_list = [item["d"][0] for item in data["data"]]
        return symbols_list
        
    except Exception as e:
        print(f"Hata oluştu: {e}")
        return []

# Kodu Çalıştır
bist_symbols = get_bist_symbols_fast()
print("\n--- İŞLEM TAMAMLANDI ---")
print(f"Toplam {len(bist_symbols)} adet hisse sembolü bulundu.\n")
#print(bist_symbols)


def get_unique_tickers(data)->list:
    return [ i.replace('Close ', '') for i in data.columns if 'Close' in i ]


def prepare_data_for_forecasting(data: pd.DataFrame, tickers: list) -> pd.DataFrame:
    new_data = []

    for ticker in tickers:
        rename_map = {
            f"Open {ticker}": "Open",
            f"High {ticker}": "High",
            f"Low {ticker}": "Low",
            f"Close {ticker}": "Close",
            f"Adj Close {ticker}": "Adj Close",
            f"Volume {ticker}": "Volume",
        }

        available_cols = [col for col in rename_map if col in data.columns]
        ticker_df = data[available_cols].copy()

        ticker_df.reset_index(inplace=True)

        date_col = "Date" if "Date" in ticker_df.columns else "Datetime"
        ticker_df.rename(columns={date_col: "Date"}, inplace=True)
        ticker_df.rename(columns=rename_map, inplace=True)

        ticker_df["Date"] = pd.to_datetime(ticker_df["Date"]).dt.tz_localize(None)
        ticker_df["unique_id"] = ticker
        ticker_df.sort_values("Date", inplace=True)
        ticker_df.drop_duplicates("Date", inplace=True)
        ticker_df.dropna(subset=["Close"], inplace=True)
        ticker_df.reset_index(drop=True, inplace=True)
        ticker_df["time_idx"] = np.arange(len(ticker_df), dtype=int)

        new_data.append(ticker_df)

    return pd.concat(new_data, ignore_index=True, sort=False)

        

@dataclass
class SplitData:
    train_df: pd.DataFrame
    val_df: pd.DataFrame
    test_df: pd.DataFrame
    trainval_df: pd.DataFrame
    X_train: pd.DataFrame
    y_train: pd.Series
    X_val: pd.DataFrame
    y_val: pd.Series
    X_trainval: pd.DataFrame
    y_trainval: pd.Series
    X_test: pd.DataFrame
    y_test: pd.Series


def build_supervised_data(
    df: pd.DataFrame,
    tickers: list,
    train_size: float,
    val_size: float,
) -> SplitData:
    print("\n[2/9] Building supervised data: y_t=Close_t, X_t=OHLCV_(t-1)...")

    train_new_data = []
    val_new_data = []
    test_new_data = []
    trainval_new_data = []

    feature_cols = ["Open", "High", "Low", "Close", "Volume"]

    for ticker in tickers:
        filtered_data = df[df["unique_id"] == ticker].copy()
        filtered_data.sort_values("Date", inplace=True)

        for col in tqdm(feature_cols, desc=f"Creating previous-day OHLCV for {ticker}"):
            filtered_data[f"prev_{col}"] = filtered_data[col].shift(1)

        filtered_data.dropna(subset=[f"prev_{col}" for col in feature_cols] + ["Close"], inplace=True)
        filtered_data.reset_index(drop=True, inplace=True)

        n = len(filtered_data)
        train_end = int(n * train_size)
        val_end = int(n * (train_size + val_size))

        train_new_data.append(filtered_data.iloc[:train_end])
        val_new_data.append(filtered_data.iloc[train_end:val_end])
        test_new_data.append(filtered_data.iloc[val_end:])
        trainval_new_data.append(filtered_data.iloc[:val_end])

    supervised_train_df = pd.concat(train_new_data, ignore_index=True, sort=False)
    supervised_val_df = pd.concat(val_new_data, ignore_index=True, sort=False)
    supervised_test_df = pd.concat(test_new_data, ignore_index=True, sort=False)
    supervised_trainval_df = pd.concat(trainval_new_data, ignore_index=True, sort=False)

    prev_cols = [f"prev_{col}" for col in feature_cols]

    return SplitData(
        train_df=supervised_train_df,
        val_df=supervised_val_df,
        test_df=supervised_test_df,
        trainval_df=supervised_trainval_df,
        X_train=supervised_train_df[["unique_id", "time_idx", "Close"] + prev_cols],
        y_train=supervised_train_df["Close"],
        X_val=supervised_val_df[["unique_id", "time_idx", "Close"] + prev_cols],
        y_val=supervised_val_df["Close"],
        X_trainval=supervised_trainval_df[["unique_id", "time_idx", "Close"] + prev_cols],
        y_trainval=supervised_trainval_df["Close"],
        X_test=supervised_test_df[["unique_id", "time_idx", "Close"] + prev_cols],
        y_test=supervised_test_df["Close"],
    )


def add_prediction_frame(frames: list, model: str, split: SplitData, y_pred, fold: int = 1) -> None:
    frames.append(
        pd.DataFrame(
            {
                "Date": split.test_df["Date"].values,
                "unique_id": split.test_df["unique_id"].values,
                "Actual": split.y_test.values,
                "Prediction": np.asarray(y_pred, dtype=float),
                "Model": model,
                "Fold": fold,
            }
        )
    )



def record_result(rows: list, source: str, model: str, metrics: dict, **extra) -> None:
    row = {
        "source": source,
        "model": model,
        "test_mae": metrics["mae"],
        "test_rmse": metrics["rmse"],
        "test_mape": metrics["mape"],
        "test_r2": metrics["r2"],
        "test_directional_accuracy": metrics["directional_accuracy"],
    }
    row.update(extra)
    rows.append(row)

def plot_predictions(predictions_df: pd.DataFrame, ticker: str, output_path: str = '../outputs') -> None:
    print("\n[8/9] Plotting last fold test predictions...")
    last_fold = predictions_df["Fold"].max()
    plot_df = predictions_df[predictions_df["Fold"] == last_fold].copy()

    plt.figure(figsize=(14, 6))
    actual_df = plot_df.drop_duplicates(subset=["Date"])[["Date", "Actual"]]

    plt.plot(
        actual_df["Date"],
        actual_df["Actual"],
        label="Gercek Close",
        linewidth=2,
        color="black",
    )

    for model_name in plot_df["Model"].unique():
        temp = plot_df[plot_df["Model"] == model_name]
        plt.plot(
            temp["Date"],
            temp["Prediction"],
            label=model_name,
            alpha=0.75,
        )

    plt.title(f"{ticker} - Time Series Forecasting Benchmark")
    plt.xlabel("Tarih")
    plt.ylabel("Close")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(output_path, dpi=160)
    plt.show()