import yfinance as yf
import pandas as pd
import argparse as arg

from indicators import Indicators
from conditions import Conditions
from strategy import Strategy
from backtester import Backtester
from hpo import run_mlforecast
from utils import prepare_data_for_forecasting, build_supervised_data


def main():
    parser = arg.ArgumentParser(
        description="Gap Strategy for Algoritmik Trading with Backtest tool."
    )

    parser.add_argument(
        "--tickers",
        nargs="+",
        default=["MSFT", "AAPL"],
        help="Test edilecek hisse sembolleri. Örn: AAPL MSFT TSLA",
    )
    parser.add_argument(
        "--start",
        type=str,
        default="2015-01-01",
        help="Başlangıç tarihi. Format: YYYY-MM-DD",
    )
    parser.add_argument(
        "--end",
        type=str,
        default=None,
        help="Bitiş tarihi. Format: YYYY-MM-DD. Boş bırakılırsa bugünü alır.",
    )
    parser.add_argument(
        "--interval",
        type=str,
        default="1d",
        help="Veri frekansı. Örn: 1d, 1wk, 1mo",
    )
    parser.add_argument(
        "--n-trials",
        type=int,
        default=30,
        help="Optuna deneme sayısı.",
    )
    parser.add_argument(
        "--random-state",
        type=int,
        default=42,
        help="Tekrarlanabilirlik için random seed.",
    )

    args = parser.parse_args()

    tickers = args.tickers

    if args.end:
        data = yf.download(
            tickers,
            start=args.start,
            end=args.end,
            interval=args.interval,
            auto_adjust=False,
        )
    else:
        data = yf.download(
            tickers,
            start=args.start,
            interval=args.interval,
            auto_adjust=False,
        )

    if data.empty:
        raise ValueError("yfinance boş veri döndürdü. Ticker, tarih veya interval değerlerini kontrol edin.")

    if isinstance(data.columns, pd.MultiIndex):
        data.columns = [" ".join(col_tuple).strip() for col_tuple in data.columns.to_flat_index()]

    print("[*] Backtest başlatılıyor...")
    print(f"[*] Tickers: {tickers} | Başlangıç: {args.start} | Frekans: {args.interval}")

    original_data = data.copy()

    obj_ind = Indicators(data=data)
    data = obj_ind.get_calculated_data()

    conditioner = Conditions(data, tickers=tickers)
    data = conditioner.set_conditions()

    obj_strategy = Strategy(data, tickers)
    data = obj_strategy.classify()

    backtester = Backtester(data=data, tickers=tickers)
    results = backtester.get_ticker_results()
    combined_result = backtester.get_combined_results()

    print("\n[*] Backtest sonuçları:")
    print(results)

    print("\n[*] Kombine sonuç:")
    print(combined_result)

    ml_data = prepare_data_for_forecasting(original_data, tickers)
    split = build_supervised_data(
        ml_data,
        tickers,
        train_size=0.7,
        val_size=0.15,
    )

    benchmark_rows = []
    prediction_frames = []

    print("ml_data shape:", ml_data.shape)
    print("ml_data columns:", ml_data.columns.tolist())
    print("split.X_train shape:", split.X_train.shape)
    print("split.X_val shape:", split.X_val.shape)
    print("split.test_df shape:", split.test_df.shape)

                     

    run_mlforecast(
        split=split,
        benchmark_rows=benchmark_rows,
        prediction_frames=prediction_frames,
        random_state=args.random_state,
        n_trials=args.n_trials,
    )

    benchmark_df = pd.DataFrame(benchmark_rows)

    print("\n[*] MLForecast benchmark sonuçları:")
    print(benchmark_df)

    if prediction_frames:
        predictions_df = pd.concat(prediction_frames, ignore_index=True)
        print("\n[*] MLForecast tahminleri:")
        print(predictions_df.head())


if __name__ == "__main__":
    main()


#/usr/local/bin/python /workspaces/Algorithmic_trading/src/main.py  --tickers AKBNK.IS TUPRS.IS YKBNK.IS
#/usr/local/bin/python /workspaces/Algorithmic_trading/src/main.py  --tickers AKBNK.IS TUPRS.IS YKBNK.IS --start 2026-01-01