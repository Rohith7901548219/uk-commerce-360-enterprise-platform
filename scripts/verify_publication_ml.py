"""Check trusted local serving artifacts against stored scores without retraining."""

import json
from datetime import UTC, datetime
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sqlalchemy import select

from commerce.analytics import sales_frame
from commerce.db import engine, predictions
from commerce.ml import features_at


def run():
    bundle = joblib.load("artifacts/repurchase.joblib")  # Only the artifact built by this workspace.
    frame = sales_frame()
    features = features_at(frame, bundle["as_of"], bundle["horizon_days"])
    assert (features.feature_max_time < features.cutoff).all()
    probability = bundle["model"].predict_proba(features[bundle["features"]])[:, 1]
    with engine().connect() as connection:
        stored = pd.read_sql(select(predictions), connection)
    measured = pd.DataFrame({"customer_key": features.customer_key, "recomputed": probability})
    compared = measured.merge(stored, on="customer_key", validate="one_to_one")
    assert len(compared) == len(measured) == len(stored)
    error = np.abs(compared.recomputed - compared.probability.astype(float))
    assert (error <= 1e-7).all()
    assert compared.probability.astype(float).between(0, 1).all()
    assert set(compared.model_run) == {bundle["run_id"]}
    repurchase = json.loads(Path("artifacts/repurchase_evaluation.json").read_text())
    forecast = json.loads(Path("artifacts/forecast_evaluation.json").read_text())
    report = {
        "verified_at": datetime.now(UTC).isoformat(),
        "feature_count": len(bundle["features"]),
        "scored_customers_checked": len(compared),
        "maximum_score_difference": float(error.max()),
        "artifact_run_matches_database": True,
        "feature_cutoff_check": True,
        "selected_repurchase_model": repurchase["selected_model"],
        "repurchase_test_average_precision": repurchase["models"][repurchase["selected_model"]]["test"][
            "pr_auc"
        ],
        "selected_forecast_model": forecast["selected_model"],
        "forecast_final_test_wape": forecast["models"][forecast["selected_model"]]["folds"][-1]["wape"],
        "scope": "Trusted existing local artifact re-inference and stored evaluation inspection; no new training or broker verification",
    }
    Path("artifacts/publication-ml.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    run()
