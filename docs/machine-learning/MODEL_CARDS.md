# Model cards and evaluation protocol

## Repeat-purchase propensity

Purpose: estimate an eligible identified customer's positive purchase within 30 days
of a historical cutoff. Eligibility: at least one positive purchase in the preceding
180 days. Features: recency, distinct-invoice frequency, gross monetary amount, AOV,
observed tenure, product diversity and mean inter-order interval. Missing IDs are
excluded; negative quantities are excluded from the positive-purchase target.

Six chronological snapshots are separated by at least the 30-day label horizon.
First four train candidates; fifth selects by average precision (reported PR-AUC);
sixth describes untouched test results. Customers may recur across snapshots because
the use case predicts later purchases of existing customers. The assertion verifies
feature timestamps strictly precede cutoff and label windows finish before the next
validation/test snapshot. Last dataset day may be incomplete; censoring is a limitation.

Candidates: prior-probability DummyClassifier, scaled logistic regression, random
forest, histogram gradient boosting. Fixed random seeds; parameters are visible in
src/commerce/ml.py. Metrics: precision/recall/F1 at 0.5, average precision, ROC-AUC
when both classes exist, confusion matrix, Brier score and reliability bins. The prior
baseline exposes class prevalence. Test-set permutation importance explains model
sensitivity, not causation. No SHAP dependency is required for this scope.

The evaluated artifact is frozen separately from a serving artifact refitted on all
completed labelled snapshots. Latest scores are for the historical source end only.
Artifacts use joblib and must never be loaded from an untrusted source. Report actual
results from artifacts/repurchase_evaluation.json and the delivery report.

## Revenue forecasting

Target: daily net sales in GBP, including returns, resampled to a complete calendar;
days absent from source are treated as zero. This assumption cannot distinguish no
trading from unrecorded data. Models: last-observation naive, weekly seasonal-naive,
additive Holt-Winters and regularised lag regression (lags 1/7/14/28 plus weekly
harmonics). Ridge is appropriate to a short daily series and regularises lag weights;
XGBoost would add complexity without a demonstrated requirement.

Three expanding development origins compare 28-day MAE. The final 28-day horizon is
reserved for the final test. Report MAE, RMSE and WAPE using absolute actual values;
WAPE is undefined when denominator zero. The final model refits all historical data.
An approximate 90% residual band uses development absolute errors; it is not guaranteed
coverage or a probabilistic business scenario. No present-day forecast validity claimed.

## Segmentation and basket intelligence

RFM percentile scores use ties without random customer ordering. Segments: Champions,
At risk high value, Loyal, New/recent, Developing. Thresholds and precedence are visible
in code. Compare segment membership 30 days apart; recalculated thresholds cause
composition drift. Business definitions are hypotheses, not discovered causal personas.

Basket rules use distinct products per positive invoice, top 60 merchandise codes,
minimum support 0.2%, confidence=P(B|A), lift=P(B|A)/P(B). Refunds are excluded.
Rules are descriptive associations, not personalized ranking or causal recommendation
effects. High lift on rare pairs needs adequate support and independent evaluation.

## Monitoring and reproducibility

MLflow records params, test metrics and reports; database logs retain run history.
Persist uv.lock, seeds, source checksum and environment. Before use on new data,
monitor missingness, recency/frequency distributions, score drift, calibration and
observed matured-label PR-AUC; retrain only after a documented comparison. No automated
online retraining or alert delivery is claimed. Models require new evaluation before
acting on a different retailer, period or customer population.
