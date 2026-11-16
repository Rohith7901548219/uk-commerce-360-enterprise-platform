# Interview questions

## Technical discussion

1. Why do invoice-line and order grain produce different AOV/frequency calculations?
2. How do source checksum, raw row identity and business duplicate fingerprint differ?
3. Why retain missing-ID sales in revenue while excluding them from customer modelling?
4. How do cancellation sign conventions and Decimal rounding affect reconciliation?
5. How are chronological label horizons separated from validation and test cutoffs?
6. Why can the same known customer appear in different time-based snapshots?
7. What do average precision, Brier score and calibration each measure?
8. Why can a selected model lose to a baseline on the untouched final test?
9. How should invoice/customer dependence change a bootstrap uncertainty estimate?
10. What happens if a consumer crashes after database commit but before offset commit?
11. Why must DLQ acknowledgement precede committing a rejected source message?
12. When is a dbt full refresh necessary after an older backfill?
13. What security controls are missing from a loopback development application?
14. Which published assets allow a fresh checkout to rebuild private local data/models?

## Business discussion

1. Which decision does each KPI support, and what is its denominator?
2. What evidence would validate a retention or targeting recommendation?
3. Why are campaign ROI, profit and causal uplift unavailable from this source?
4. What would you confirm with actual stakeholders before adopting the RFM definitions?
5. How would you communicate low recall or a forecast that underperforms seasonal-naive?
6. Which quality and deployment gaps should be addressed first, and why?

Practical preparation: reproduce a KPI using SQL, explain a model split, inspect an
actual query plan, demonstrate a failed-write 401 response and discuss the broker
verification blocker. Do not claim personal understanding that has not been developed.
See the [expanded STAR/demo pack](INTERVIEW_AND_DEMO.md).
