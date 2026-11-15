# Data handling

`fixtures/retail.csv` is a nine-row synthetic test fixture with deliberate duplicates,
returns, missing IDs and invalid prices/quantities. It is not real business evidence.
`raw/`, `warehouse/` and `processed/` are ignored. Acquire UCI Online Retail II with
`commerce download`; it verifies a persistent SHA256 manifest. Retain source attribution:
Chen, D. (2012), Online Retail II, UCI, DOI 10.24432/C5CG6D, CC BY 4.0.

If this host cannot resolve UCI, see the delivery report for explicit mirror provenance.
Do not commit the full workbook, raw customer identifiers, local database or secrets.
