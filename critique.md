## What the paper gets right

The core result is robust. The link between VPIN and trading volume is mechanical by construction and follows analytically from the expected order imbalance under random order flow:

E[OI] = F(Q) ≈ √(2 / (πQ)),

where Q is the number of time bars in a volume bucket. When trading intensifies, Q falls and OI rises, whether or not order flow is toxic. This argument does not depend on the sample, so our critique targets what the paper *could not test*, not its main finding.

## Four weak spots

### 1. No ground truth for trade direction
- Every variant (TR, BV, FB, transaction VPIN) signs trades with the tick rule or the bulk-volume rule. None is checked against the actual aggressor side.
- The paper therefore refutes *one implementation* of VPIN. It cannot show that *order-flow toxicity* itself is uninformative.
- The surprising negative link between FB-VPIN and volatility (Finding 10) is explained only informally. It may be an artefact of misclassification in volatile markets.
- The authors acknowledge this and defer it to a follow-up study ("Assessing VPIN measurement of order flow toxicity via perfect trade classification", 2013 working paper).

### 2. The crash evidence rests on a single event (n = 1)
- The crash-warning verdict is based on one day, May 6, 2010. No false-alarm or hit rate can be estimated from one event. This applies equally to ELO's claim and to the authors' rebuttal.
- The "not an all-time high" result (exceeded on 26 days, 4.3%) depends on the sample window: 2.5 years including the 2008 crisis, shorter than ELO's sample.
- One asset and one parameter set (V = 40,000, L = 50). Sensitivity to V and L is not reported.

### 3. Forecast evaluation is in-sample only
- All regressions are full-sample OLS with HAC t-stats and adjusted R². There is no rolling or expanding out-of-sample test and no forecast-comparison test such as Diebold–Mariano.
- TR-VPIN, U1-VPIN and volume are highly collinear (ρ ≈ 0.6–0.8), so the negative TR-VPIN coefficient after controls (Finding 9) is fragile, as the authors partly concede.
- **Nuance:** in-sample evaluation favours the extra regressor. This weakness therefore undermines *positive* claims, such as BV-VPIN's significance, more than the paper's negative conclusion.

### 4. Target and benchmark mismatch
- VPIN was proposed as a **liquidity-stress** indicator (order-book depletion, liquidity providers withdrawing), but it is tested almost only as a **volatility** forecaster. Liquidity targets such as spread widening or book depth are not tested.
- VIX is a 30-day implied-volatility measure used for horizons from minutes to days. The authors admit (footnote 14) that realized volatility would be a better benchmark; a standard model such as HAR-RV is missing.

## How our project responds

| Weak spot | Our response (Binance BTCUSDT, Q1 2020) | Result |
|---|---|---|
| 1. No ground truth | Exchange-direction VPIN signed by Binance's `is_buyer_maker` aggressor flag | MSE gain −0.02% vs controls (Clark–West p = 0.50); minute tick rule matches the exchange side for only 57.5% of volume |
| 2. n = 1 | New market and crisis (12–13 March 2020); 9 window, bucket and calendar variants | Uninformed U2-VPIN beats TR-VPIN in all 9 variants |
| 3. In-sample only | Train Jan–Feb, test March; Clark–West, Diebold–Mariano, circular block bootstrap; fixed, expanding and rolling refits | TR gain 0.71% [0.36, 1.57]: detectable but economically tiny and below U2 (1.77%) |
| 4. Target mismatch | **Still open:** we also forecast realized volatility | Spread and depth targets are the next step |

## How could these results be overfit?

| Risk | How Andersen & Bondarenko checked | How we checked |
|---|---|---|
| **Hindsight design:** VPIN was built around a crash that had already happened (ELO) | Reconstructed what an observer could see before 13:30 (Figs 8–10) | Model fitted once on Jan–Feb, evaluated on unseen March |
| **Lucky trade signs:** classification may help only by chance | U1/U2-VPIN benchmarks with random signs | 100 within-day sign shuffles: 80 of 100 match or beat the real signs |
| **Researcher degrees of freedom:** bar length, bins, buckets, sample | δ ∈ {10, 60, 300} s, ν ∈ {1, 1K, 5K}; 2008–09 excluded (fn. 20); 400 shifted bucket grids (Fig. 5) | 9 parameter variants; 3 refit schemes; results with and without the 48 event hours |

**Our own overfitting risk:** March 2020 was chosen because it contains a crash, and the extensions were designed after seeing March results. Key forecasts are repeated without the event hours; the clean fix is a test on a crash we have not looked at.

## Verdict

The paper's main conclusion survives all four weak spots: on Bitcoin, with true trade labels and out-of-sample evaluation, VPIN's apparent information still comes from trading activity, not from who was buying or selling. The open question is whether VPIN predicts **liquidity** stress rather than volatility.
