# Five-minute project demonstration

1. **Source and honesty:** show the historical 2009–2011/mirror label, source attribution
   and independent-project disclaimer. The application is local, not a hosted retailer.
2. **Trust:** explain the raw/staging/fact reconciliation and one quarantined rule.
3. **Trading:** filter dates/country, explain gross minus returns, AOV and repeat rate.
4. **Customers/products:** inspect a pseudonymous customer, RFM/cohort retention,
   top/bottom products, returns and descriptive basket associations.
5. **Models:** explain feature cutoffs and later labels; compare baselines, AP/calibration,
   low-recall limitations and final forecast results. Do not hide baseline wins.
6. **Scenarios:** vary response/incrementality or segment budget priorities. Every campaign
   value is assumed; no profit/attribution/uplift is observed.
7. **Operations:** show actual pipeline/model/test history. Demonstrate streaming only
   if a real broker/consumer is running and verified; otherwise state the blocker.
8. **Engineering evidence:** show tests, PostgreSQL/dbt results, architecture, Power BI
   source assets and current CI/publication verification.

Prepared-workspace startup:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/start.ps1
```

For a fresh checkout, follow the README setup first; ignored data, binaries, environment
files and trained models are intentionally not included in GitHub. The application uses
http://127.0.0.1:8501 and the API documentation uses http://127.0.0.1:8000/docs.

Longer interview/STAR narrative and two-minute narration:
[existing interview and demo material](INTERVIEW_AND_DEMO.md).
