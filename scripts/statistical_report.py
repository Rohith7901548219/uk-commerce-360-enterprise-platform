"""Seeded descriptive uncertainty and temporal basket-rule validation."""

import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import bootstrap

from commerce.analytics import basket_rules, sales_frame


def run():
    frame = sales_frame()
    paid = frame[frame.quantity > 0]
    orders = paid.groupby("invoice").amount.sum().values
    interval = bootstrap(
        (orders,),
        np.mean,
        n_resamples=2000,
        batch=20,
        method="percentile",
        confidence_level=0.95,
        rng=np.random.default_rng(42),
    )
    cutoff = frame.date_key.min() + (frame.date_key.max() - frame.date_key.min()) * 0.7
    rules = basket_rules(frame[frame.date_key < cutoff])[:30]
    future = paid[(paid.date_key >= cutoff) & (paid.category == "merchandise")]
    baskets = future.groupby("invoice").stock_code.agg(set)
    validation = []
    for rule in rules:
        antecedents = sum(rule["antecedent"] in basket for basket in baskets)
        together = sum({rule["antecedent"], rule["consequent"]}.issubset(basket) for basket in baskets)
        validation.append(
            {
                **rule,
                "held_out_pair_count": together,
                "held_out_support": together / len(baskets) if len(baskets) else None,
                "held_out_confidence": together / antecedents if antecedents else None,
            }
        )
    report = {
        "positive_invoice_count": len(orders),
        "mean_gross_order_value": float(np.mean(orders)),
        "median_gross_order_value": float(np.median(orders)),
        "bootstrap_95pct_mean_interval": [
            float(interval.confidence_interval.low),
            float(interval.confidence_interval.high),
        ],
        "bootstrap_seed": 42,
        "bootstrap_resamples": 2000,
        "limitations": "Resamples invoices, assuming independence; repeat-customer clustering and calendar dependence are not corrected. Descriptive, not causal.",
        "basket_temporal_cutoff": str(pd.Timestamp(cutoff).date()),
        "held_out_baskets": len(baskets),
        "basket_rule_validation": validation,
    }
    Path("artifacts/statistical_analysis.json").write_text(json.dumps(report, indent=2))
    print(json.dumps({k: v for k, v in report.items() if k != "basket_rule_validation"}, indent=2))


if __name__ == "__main__":
    run()
