# Research status

## Scope

Independent implementation of selected methods from Andersen and
Bondarenko, "VPIN and the Flash Crash", and empirical evaluation
on Binance Spot BTCUSDT trades, January–March 2020.

This is not a reproduction of the US Flash Crash of May 6, 2010.

## Implemented

- Data audit and one-minute aggregation.
- Minute-bar tick-rule classification.
- Fixed-volume buckets.
- Baseline TR-VPIN.
- U2-VPIN benchmark.
- Exchange-side VPIN using individual trade maker flags.
- Hourly forecast evaluation.
- Event-window diagnostics.
- Circular block bootstrap of test forecast losses.
- Robustness to VPIN window and bucket size.
- Six automated tests of the baseline implementation.

## Main findings

- TR-VPIN is highly correlated with U2-VPIN.
- Adding baseline TR-VPIN to the selected control regression
  reduces March test MSE by approximately 0.71%.
- Adding U2-VPIN reduces MSE by approximately 1.77%.
- Exchange-side VPIN alone does not materially improve
  the selected control regression.
- Persistence has the lowest RMSE and MAE among the models
  in the primary experiment.
- Results depend on the averaging window and bucket size.

## Limitations

- Different market and event from the original paper.
- Only one three-month period.
- March was selected to include a known stress event.
- Later extensions were evaluated after March results had been viewed.
- ZIP checksum verification was not performed.
- Bootstrap intervals condition on fitted models and the observed
  March period; they do not include model-estimation uncertainty.
- Exchange-side and minute-bar VPIN differ in both classification
  and within-minute aggregation.
- Automated tests do not cover every possible input or all modules.

## Remaining work

- Run notebooks from clean kernels in the documented order.
- Finalize README and data-download instructions.
- Review saved tables and figures.
- Save reviewed changes to Git.
- Prepare the presentation.