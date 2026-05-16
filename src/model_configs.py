from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge, ElasticNet
from sklearn.ensemble import RandomForestRegressor, ExtraTreesRegressor


def sklearn_non_boosting_configs(random_state: int) -> dict:
    return {
        "Ridge": {
            "build": lambda params: make_pipeline(
                StandardScaler(),
                Ridge(alpha=params["alpha"]),
            ),
            "suggest": lambda trial: {
                "alpha": trial.suggest_float("alpha", 1e-4, 100.0, log=True),
            },
        },
        "ElasticNet": {
            "build": lambda params: make_pipeline(
                StandardScaler(),
                ElasticNet(
                    alpha=params["alpha"],
                    l1_ratio=params["l1_ratio"],
                    max_iter=20_000,
                    random_state=random_state,
                ),
            ),
            "suggest": lambda trial: {
                "alpha": trial.suggest_float("alpha", 1e-4, 10.0, log=True),
                "l1_ratio": trial.suggest_float("l1_ratio", 0.05, 0.95),
            },
        },
        "RandomForest": {
            "build": lambda params: RandomForestRegressor(
                n_estimators=params["n_estimators"],
                max_depth=params["max_depth"],
                min_samples_leaf=params["min_samples_leaf"],
                max_features=params["max_features"],
                random_state=random_state,
                n_jobs=-1,
            ),
            "suggest": lambda trial: {
                "n_estimators": trial.suggest_int("n_estimators", 200, 800),
                "max_depth": trial.suggest_int("max_depth", 2, 24),
                "min_samples_leaf": trial.suggest_int("min_samples_leaf", 1, 25),
                "max_features": trial.suggest_float("max_features", 0.5, 1.0),
            },
        },
        "ExtraTrees": {
            "build": lambda params: ExtraTreesRegressor(
                n_estimators=params["n_estimators"],
                max_depth=params["max_depth"],
                min_samples_leaf=params["min_samples_leaf"],
                max_features=params["max_features"],
                random_state=random_state,
                n_jobs=-1,
            ),
            "suggest": lambda trial: {
                "n_estimators": trial.suggest_int("n_estimators", 200, 800),
                "max_depth": trial.suggest_int("max_depth", 2, 24),
                "min_samples_leaf": trial.suggest_int("min_samples_leaf", 1, 25),
                "max_features": trial.suggest_float("max_features", 0.5, 1.0),
            },
        },
    }
