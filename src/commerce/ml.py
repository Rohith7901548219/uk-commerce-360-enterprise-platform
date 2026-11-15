"""Temporal repurchase evaluation and rolling-origin daily revenue forecasts."""

import json
import logging
import os
import uuid
from datetime import UTC, datetime
from pathlib import Path

import joblib
import mlflow
import numpy as np
import pandas as pd
from sklearn.calibration import calibration_curve
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    mean_absolute_error,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from statsmodels.tsa.holtwinters import ExponentialSmoothing

from commerce.analytics import rfm, sales_frame, trends
from commerce.config import settings
from commerce.db import engine, forecasts, model_logs, predictions

FEATURES = [
    "recency",
    "frequency",
    "monetary",
    "average_order_value",
    "tenure",
    "product_diversity",
    "mean_interval",
]


def features_at(frame, cutoff, horizon=30, lookback=180):
    cutoff = pd.Timestamp(cutoff, tz="UTC") if pd.Timestamp(cutoff).tzinfo is None else pd.Timestamp(cutoff)
    history = frame[(frame.event_time < cutoff) & (frame.quantity > 0) & frame.customer_key.notna()]
    recent = history[history.event_time >= cutoff - pd.Timedelta(days=lookback)]
    grouped = recent.groupby("customer_key")
    result = grouped.agg(
        last_purchase=("event_time", "max"),
        frequency=("invoice", "nunique"),
        monetary=("amount", "sum"),
        product_diversity=("stock_code", "nunique"),
    )
    first = history.groupby("customer_key").event_time.min()
    result["recency"] = (cutoff - result.last_purchase).dt.total_seconds() / 86400
    result["tenure"] = (cutoff - first.reindex(result.index)).dt.total_seconds() / 86400
    result["average_order_value"] = result.monetary / result.frequency
    order_dates = (
        recent.groupby(["customer_key", "invoice"]).event_time.min().reset_index().sort_values("event_time")
    )
    intervals = order_dates.groupby("customer_key").event_time.diff().dt.total_seconds() / 86400
    result["mean_interval"] = (
        intervals.groupby(order_dates.customer_key).mean().reindex(result.index).fillna(lookback)
    )
    future = frame[
        (frame.event_time >= cutoff)
        & (frame.event_time < cutoff + pd.Timedelta(days=horizon))
        & (frame.quantity > 0)
    ]
    result["target"] = result.index.isin(future.customer_key.dropna().unique()).astype(int)
    result["cutoff"] = cutoff
    result["feature_max_time"] = grouped.event_time.max()
    return result.reset_index()


def classification_metrics(y, probability):
    predicted = probability >= 0.5
    fraction, mean_probability = calibration_curve(y, probability, n_bins=8, strategy="quantile")
    return {
        "precision": float(precision_score(y, predicted, zero_division=0)),
        "recall": float(recall_score(y, predicted, zero_division=0)),
        "f1": float(f1_score(y, predicted, zero_division=0)),
        "pr_auc": float(average_precision_score(y, probability)),
        "roc_auc": float(roc_auc_score(y, probability)) if len(set(y)) > 1 else None,
        "brier_score": float(brier_score_loss(y, probability)),
        "confusion_matrix": confusion_matrix(y, predicted, labels=[0, 1]).tolist(),
        "calibration": {
            "fraction_positive": fraction.tolist(),
            "mean_probability": mean_probability.tolist(),
        },
        "samples": len(y),
        "positive_rate": float(np.mean(y)),
    }


def train_repurchase(frame, horizon=30):
    first, last = frame.event_time.min(), frame.event_time.max()
    if (last - first).days < 300:
        raise ValueError(
            "Repurchase evaluation needs at least 300 days; small fixtures are not model evidence"
        )
    # Snapshots spaced by >= horizon: complete labels before the next evaluation cutoff.
    cutoffs = pd.date_range(first + pd.Timedelta(days=180), last - pd.Timedelta(days=horizon), periods=6)
    if min(np.diff(cutoffs.values)).astype("timedelta64[D]").astype(int) < horizon:
        raise ValueError("Insufficient history for embargoed chronological snapshots")
    snapshots = [features_at(frame, cutoff, horizon) for cutoff in cutoffs]
    training = pd.concat(snapshots[:4], ignore_index=True)
    validation, test = snapshots[4], snapshots[5]
    assert training.cutoff.max() + pd.Timedelta(days=horizon) <= validation.cutoff.min()
    assert validation.cutoff.max() + pd.Timedelta(days=horizon) <= test.cutoff.min()
    assert (training.feature_max_time < training.cutoff).all()
    candidates = {
        "prior_baseline": DummyClassifier(strategy="prior"),
        "logistic_regression": make_pipeline(
            StandardScaler(), LogisticRegression(max_iter=1000, random_state=42)
        ),
        "random_forest": RandomForestClassifier(
            n_estimators=160, min_samples_leaf=15, max_depth=9, random_state=42, n_jobs=-1
        ),
        "gradient_boosting": HistGradientBoostingClassifier(
            max_iter=150, max_leaf_nodes=15, l2_regularization=2, random_state=42
        ),
    }
    report = {
        "horizon_days": horizon,
        "lookback_days": 180,
        "split": {
            "train_cutoffs": [str(x) for x in cutoffs[:4]],
            "validation_cutoff": str(cutoffs[4]),
            "test_cutoff": str(cutoffs[5]),
        },
        "models": {},
    }
    for name, model in candidates.items():
        model.fit(training[FEATURES], training.target)
        val_probability = model.predict_proba(validation[FEATURES])[:, 1]
        test_probability = model.predict_proba(test[FEATURES])[:, 1]
        report["models"][name] = {
            "validation": classification_metrics(validation.target, val_probability),
            "test": classification_metrics(test.target, test_probability),
        }
    winner = max(report["models"], key=lambda name: report["models"][name]["validation"]["pr_auc"])
    report["selected_model"] = winner
    chosen = candidates[winner]
    importance = permutation_importance(
        chosen, test[FEATURES], test.target, scoring="average_precision", n_repeats=5, random_state=42
    )
    report["permutation_importance_test"] = dict(
        zip(FEATURES, importance.importances_mean.tolist(), strict=True)
    )
    # The evaluated artifact stays frozen. A separate serving artifact uses all completed labelled snapshots.
    evaluated_path = Path("artifacts/repurchase_evaluated.joblib")
    joblib.dump({"model": chosen, "features": FEATURES}, evaluated_path)
    chosen.fit(pd.concat(snapshots)[FEATURES], pd.concat(snapshots).target)
    serving_cutoff = last.normalize() + pd.Timedelta(days=1)
    current = features_at(frame, serving_cutoff, horizon)
    probability = chosen.predict_proba(current[FEATURES])[:, 1]
    run_id = uuid.uuid4().hex
    artifact = Path("artifacts/repurchase.joblib")
    joblib.dump(
        {
            "model": chosen,
            "features": FEATURES,
            "run_id": run_id,
            "as_of": str(serving_cutoff),
            "horizon_days": horizon,
        },
        artifact,
    )
    report["serving_as_of"] = str(serving_cutoff)
    report["limitations"] = [
        "Historical observational data; no causal effect or present-day validity established.",
        "Customers can occur across time splits; this evaluates future purchases by known customers.",
        "Latest source day may be incomplete; boundary labels can be right-censored.",
    ]
    Path("artifacts/repurchase_evaluation.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    with engine().begin() as connection:
        connection.execute(predictions.delete())
        connection.execute(
            predictions.insert(),
            [
                {
                    "customer_key": key,
                    "as_of": serving_cutoff.to_pydatetime(),
                    "probability": float(p),
                    "model_run": run_id,
                }
                for key, p in zip(current.customer_key, probability, strict=True)
            ],
        )
        connection.execute(
            model_logs.insert().values(
                run_id=run_id,
                model_type="repurchase",
                trained_at=datetime.now(UTC),
                metrics=report,
                artifact=str(artifact),
            )
        )
    with mlflow.start_run(run_name="repurchase-chronological"):
        mlflow.log_params({"winner": winner, "horizon_days": horizon, "seed": 42, "lookback_days": 180})
        mlflow.log_metrics(
            {
                f"test_{k}": v
                for k, v in report["models"][winner]["test"].items()
                if isinstance(v, (float, int))
            }
        )
        mlflow.log_artifact(str(evaluated_path))
        mlflow.log_artifact(str(artifact))
        mlflow.log_artifact("artifacts/repurchase_evaluation.json")
    return report


def predict_series(history, horizon, name):
    values = np.asarray(history, dtype=float)
    if name == "naive":
        return np.repeat(values[-1], horizon)
    if name == "seasonal_naive":
        return np.resize(values[-7:], horizon)
    if name == "holt_winters":
        return np.asarray(
            ExponentialSmoothing(
                values, trend="add", seasonal="add", seasonal_periods=7, initialization_method="estimated"
            )
            .fit(optimized=True)
            .forecast(horizon)
        )

    # Ridge autoregression: lagged values and weekday harmonics, recursive multi-step forecasts.
    def row(data, index):
        return [data[index - lag] for lag in (1, 7, 14, 28)] + [
            np.sin(index * 2 * np.pi / 7),
            np.cos(index * 2 * np.pi / 7),
        ]

    model = make_pipeline(StandardScaler(), Ridge(alpha=10))
    model.fit([row(values, index) for index in range(28, len(values))], values[28:])
    extended = values.tolist()
    result = []
    for _ in range(horizon):
        prediction = float(model.predict([row(extended, len(extended))])[0])
        result.append(prediction)
        extended.append(prediction)
    return np.asarray(result)


def train_forecast(frame, horizon=28):
    series = trends(frame).set_index("date").net_sales.asfreq("D", fill_value=0)
    if len(series) < 180:
        raise ValueError("Forecast evaluation needs at least 180 daily observations")
    names = ["naive", "seasonal_naive", "holt_winters", "ridge_autoregression"]
    results, residuals, comparisons = {}, {}, []
    # Three development origins select the model; the final horizon remains an untouched test.
    origins = [len(series) - horizon * x for x in (5, 4, 3, 1)]
    for name in names:
        fold_metrics, development_errors = [], []
        for fold, origin in enumerate(origins):
            predicted = predict_series(series.iloc[:origin], horizon, name)
            actual = series.iloc[origin : origin + horizon].values
            errors = actual - predicted
            metrics = {
                "origin": str(series.index[origin]),
                "role": "test" if fold == 3 else "development",
                "mae": float(mean_absolute_error(actual, predicted)),
                "rmse": float(np.sqrt(np.mean(errors**2))),
                "wape": float(np.abs(errors).sum() / np.abs(actual).sum()) if np.abs(actual).sum() else None,
            }
            fold_metrics.append(metrics)
            if fold < 3:
                development_errors.extend(errors.tolist())
            else:
                comparisons.extend(
                    {"date": str(day.date()), "model": name, "actual": float(a), "prediction": float(p)}
                    for day, a, p in zip(
                        series.index[origin : origin + horizon], actual, predicted, strict=True
                    )
                )
        results[name] = {
            "development_mae": float(np.mean([x["mae"] for x in fold_metrics[:3]])),
            "folds": fold_metrics,
        }
        residuals[name] = development_errors
    winner = min(results, key=lambda name: results[name]["development_mae"])
    predicted = predict_series(series, horizon, winner)
    radius = float(np.quantile(np.abs(residuals[winner]), 0.9))
    future_dates = pd.date_range(series.index[-1] + pd.Timedelta(days=1), periods=horizon)
    rows = [
        {
            "forecast_date": day.date(),
            "prediction": round(float(value), 2),
            "lower": round(float(value - radius), 2),
            "upper": round(float(value + radius), 2),
            "model": winner,
        }
        for day, value in zip(future_dates, predicted, strict=True)
    ]
    report = {
        "selected_model": winner,
        "horizon_days": horizon,
        "models": results,
        "interval_method": "Approximate 90% absolute development-residual band; coverage is not guaranteed.",
        "forecast_target": "Daily net sales GBP, including returns; missing calendar days are zero.",
        "source_last_date": str(series.index[-1].date()),
        "test_comparison": comparisons,
    }
    Path("artifacts/forecast_evaluation.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    pd.DataFrame(rows).to_csv("artifacts/revenue_forecast.csv", index=False)
    run_id = uuid.uuid4().hex
    with engine().begin() as connection:
        connection.execute(forecasts.delete())
        connection.execute(forecasts.insert(), rows)
        connection.execute(
            model_logs.insert().values(
                run_id=run_id,
                model_type="forecast",
                trained_at=datetime.now(UTC),
                metrics=report,
                artifact="artifacts/forecast_evaluation.json",
            )
        )
    with mlflow.start_run(run_name="revenue-rolling-origin"):
        mlflow.log_params({"winner": winner, "horizon_days": horizon, "origins": 4})
        mlflow.log_metrics(
            {k: v for k, v in results[winner]["folds"][-1].items() if isinstance(v, (float, int))}
        )
        mlflow.log_artifact("artifacts/forecast_evaluation.json")
    return report


def train_all():
    git_path = Path("C:/Program Files/Git/cmd/git.exe")
    if git_path.exists():
        os.environ.setdefault("GIT_PYTHON_GIT_EXECUTABLE", str(git_path))
    frame = sales_frame()
    if frame.empty:
        raise ValueError("Load the historical dataset before training")
    mlflow.set_tracking_uri(settings().mlflow_tracking_uri)
    mlflow.set_experiment("UK-Commerce-360-Historical")
    from importlib.metadata import version

    from sqlalchemy import select

    from commerce.db import sources

    with engine().connect() as connection:
        provenance = [dict(row) for row in connection.execute(select(sources)).mappings()]
    manifest = {
        "sources": provenance,
        "features": FEATURES,
        "random_seed": 42,
        "training_time": datetime.now(UTC).isoformat(),
        "versions": {name: version(name) for name in ("numpy", "pandas", "scikit-learn", "mlflow-skinny")},
    }
    Path("artifacts/training_manifest.json").write_text(json.dumps(manifest, indent=2, default=str))
    repurchase = train_repurchase(frame)
    forecast = train_forecast(frame)
    previous = rfm(frame[frame.date_key <= frame.date_key.max() - pd.Timedelta(days=30)])
    latest = rfm(frame)
    comparison = previous[["customer_key", "segment"]].merge(
        latest[["customer_key", "segment"]], on="customer_key", suffixes=("_prior", "_latest")
    )
    stability = {
        "customers_compared": len(comparison),
        "unchanged_segment_rate": float((comparison.segment_prior == comparison.segment_latest).mean()),
        "comparison_days": 30,
        "note": "Business RFM segments; percentile thresholds are recalculated at each snapshot.",
    }
    Path("artifacts/segment_stability.json").write_text(json.dumps(stability, indent=2))
    logging.getLogger(__name__).info(
        "Training complete: %s / %s", repurchase["selected_model"], forecast["selected_model"]
    )
