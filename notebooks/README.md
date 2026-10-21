# Notebooks

Run the notebooks in this order:

1. `02_binance_data.ipynb` — download, clean, and audit Binance BTCUSDT data.
2. `03_vpin_analysis.ipynb` — construct volume buckets and compute TR-VPIN and U2-VPIN.
3. `04_trade_classification.ipynb` — classify minute bars using the tick rule.
4. `05_forecast_uncertainty.ipynb` — bootstrap forecast uncertainty.
5. `06_window_robustness.ipynb` — test alternative VPIN windows.
6. `07_bucket_robustness.ipynb` — test alternative bucket sizes.
7. `08_placebo_vpin.ipynb` — permute trade signs within days and recompute TR-VPIN.
8. `09_calendar_window.ipynb` — compare calendar-hour and bucket-count windows.
9. `10_forecast_robustness.ipynb` — re-estimation, event exclusion, QLIKE, CW and DM tests.
