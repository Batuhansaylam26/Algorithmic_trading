import optuna
import numpy as np
import pandas as pd
from tqdm.auto import tqdm
from mlforecast import MLForecast
from sklearn.metrics import mean_absolute_error
from model_configs import sklearn_non_boosting_configs
from metrics import evaluate
from utils import SplitData, record_result, add_prediction_frame

def tune_with_timeseries(builder, split: SplitData, n_trials: int, random_state: int):
    def objective(trial):
        X_fit = split.X_train
        y_fit = split.y_train
        X_valid = split.X_val
        y_valid = split.y_val

        model = builder(trial)
        model.fit(X_fit, y_fit)
        pred = model.predict(X_valid)
        score = mean_absolute_error(y_valid, pred)
        if trial.should_prune():
            raise optuna.TrialPruned()

        return float(score)

    study = optuna.create_study(
        direction="minimize",
        sampler=optuna.samplers.TPESampler(seed=random_state),
        pruner=optuna.pruners.MedianPruner(n_startup_trials=10, n_warmup_steps=1),
    )
    study.optimize(objective, n_trials=n_trials, show_progress_bar=True)

    final_model = builder(study.best_trial)
    final_model.fit(split.X_trainval, split.y_trainval)
    return final_model, study

def build_mlforecast_model(
    params: dict,
    model_name: str,
    random_state: int,
) -> tuple[MLForecast, str]:
    model_config = sklearn_non_boosting_configs(random_state)[model_name]
    model = model_config["build"](params)

    forecast_name = f"MLForecast_{model_name}_lag1"

    mlf = MLForecast(
        models={forecast_name: model},
        freq=1,
        lags=[1],
        date_features=[],
    )

    return mlf, forecast_name





def run_mlforecast(
    split: SplitData,
    benchmark_rows: list,
    prediction_frames: list,
    random_state: int,
    n_trials: int,
) -> None:
    print("\n[7/9] Running MLForecast tuning + one-step rolling benchmark...")

    train_history = (
        split.train_df[["unique_id", "time_idx", "Close"]]
        .rename(columns={"time_idx": "ds", "Close": "y"})
        .dropna(subset=["unique_id", "ds", "y"])
        .sort_values(["unique_id", "ds"])
        .copy()
    )

    if train_history.empty:
        raise ValueError("MLForecast train_history is empty.")

    if train_history.groupby("unique_id").size().max() <= 1:
        raise ValueError(
            "MLForecast needs at least 2 observations per unique_id because lags=[1]."
        )

    df_all = pd.concat(
        [split.X_train, split.X_val, split.test_df],
        ignore_index=True,
    )


    mlf_all = (
        df_all[["unique_id", "time_idx", "Close"]]
        .rename(columns={"time_idx": "ds", "Close": "y"})
        .dropna(subset=["unique_id", "ds", "y"])
        .sort_values(["unique_id", "ds"])
        .copy()
    )

    val_frame = (
        split.val_df[["unique_id", "time_idx"]]
        .rename(columns={"time_idx": "ds"})
        .copy()
    )
    val_frame["y"] = split.y_val.values

    model_configs = sklearn_non_boosting_configs(random_state=random_state)

    for model_name, model_config in model_configs.items():
        forecast_name = f"MLForecast_{model_name}_lag1"
        print(f"\nTuning {forecast_name}...")

        def objective(trial, model_name=model_name, model_config=model_config):
            params = model_config["suggest"](trial)

            mlf, forecast_name = build_mlforecast_model(
                params=params,
                model_name=model_name,
                random_state=random_state,
            )

            mlf.fit(train_history)

            h = val_frame.groupby("unique_id")["ds"].nunique().max()
            pred_df = mlf.predict(h=h)

            scored = val_frame.merge(
                pred_df[["unique_id", "ds", forecast_name]],
                on=["unique_id", "ds"],
                how="inner",
            )

            if scored.empty:
                raise ValueError(
                    f"No validation predictions matched for {forecast_name}. "
                    "Check that val ds values come immediately after train ds values per unique_id."
                )

            score = mean_absolute_error(scored["y"], scored[forecast_name])

            trial.report(score, step=1)
            if trial.should_prune():
                raise optuna.TrialPruned()

            return float(score)

        study = optuna.create_study(
            direction="minimize",
            sampler=optuna.samplers.TPESampler(seed=random_state),
            pruner=optuna.pruners.MedianPruner(
                n_startup_trials=10,
                n_warmup_steps=1,
            ),
        )

        study.optimize(
            objective,
            n_trials=max(10, n_trials // 2),
            show_progress_bar=False,
        )

        rolling_preds = []

        for _, row in tqdm(
            split.test_df.iterrows(),
            total=len(split.test_df),
            desc=f"{forecast_name} rolling",
        ):
            target_id = row["unique_id"]
            target_idx = int(row["time_idx"])

            history = (
                mlf_all[mlf_all["ds"] < target_idx]
                .sort_values(["unique_id", "ds"])
                .copy()
            )

            mlf, forecast_name = build_mlforecast_model(
                params=study.best_params,
                model_name=model_name,
                random_state=random_state,
            )

            mlf.fit(history)
            pred_df = mlf.predict(h=1)

            pred = pred_df.loc[
                pred_df["unique_id"] == target_id,
                forecast_name,
            ].iloc[0]

            rolling_preds.append(float(pred))

        metrics = evaluate(split.y_test, rolling_preds)

        record_result(
            benchmark_rows,
            source="mlforecast",
            model=forecast_name,
            metrics=metrics,
            pruning_enabled=True,
            tuning_mae=study.best_value,
            best_params=study.best_params,
        )

        add_prediction_frame(
            prediction_frames,
            forecast_name,
            split,
            rolling_preds,
        )

        print(
            f"{forecast_name} val MAE: {study.best_value:.6f} | "
            f"Test MAE: {metrics['mae']:.6f}"
        )
