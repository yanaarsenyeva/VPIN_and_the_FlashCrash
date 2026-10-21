# Data

This directory contains Binance BTCUSDT market data used in the project.

Raw data are **not stored in the Git repository** because they are large and can be downloaded directly from Binance. The `data/raw/` directory is ignored by Git.

## Data overview

| Item | Value |
|---|---|
| Asset | BTCUSDT |
| Market | Binance spot |
| Sample period | 1 January 2020 – 31 March 2020 |
| Frequency | 1-minute bars |
| Main event | 12–13 March 2020 |
| Target variable | Next-one-hour realized volatility, `rv_next_1h_pct` |

The analysis uses one-minute OHLCV data and, where available, aggregate trade information. The data cover a calm January–February period and a high-volatility March period, including the market stress episode of 12–13 March 2020.

## Directory structure

```text
data/
├── raw/          # Downloaded Binance files; ignored by Git
└── processed/    # Cleaned and feature-engineered files created by notebooks
```

## Required raw files

Place the downloaded Binance files in:

```text
data/raw/
```

The notebooks expect monthly or daily Binance kline and trade files covering January–March 2020. The exact filenames depend on the download format used in `notebooks/02_binance_data.ipynb`.

At minimum, the raw data should contain:

- open time;
- open, high, low, and close prices;
- volume;
- number of trades;
- close time.

For exchange-direction classification, the pipeline also uses Binance aggregate trade data when available.

## How to download the data

### Option 1: Binance Vision

1. Open [Binance Vision](https://data.binance.vision/).
2. Go to **Data Type → Klines**.
3. Select:
   - **Spot**
   - **BTCUSDT**
   - **1m**
4. Download the daily or monthly files for January, February, and March 2020.
5. Place the downloaded `.zip` or `.csv` files in:

```bash
data/raw/
```

For trade-level information, also download:

1. **Data Type → Trades** or **AggTrades**
2. **Spot**
3. **BTCUSDT**
4. Files for January–March 2020.

### Option 2: Binance API

The data-preparation notebook can also use the Binance public REST API. It downloads 1-minute klines with:

```text
[https://api.binance.com/api/v3/klines](https://api.binance.com/api/v3/klines)
```

Relevant parameters:

- `symbol=BTCUSDT`
- `interval=1m`
- `startTime` and `endTime` in milliseconds
- `limit=1000`

The notebook paginates requests until it has collected all bars for Q1 2020.

## Processing pipeline

Run the notebooks in this order:

1. `notebooks/02_binance_data.ipynb`  
   Downloads or reads raw Binance data, cleans timestamps, checks for missing or duplicated minutes, and creates the processed minute-level dataset.

2. `notebooks/03_vpin_analysis.ipynb`  
   Constructs volume buckets and computes TR-VPIN and U2-VPIN.

3. `notebooks/04_trade_classification.ipynb`  
   Applies tick-rule classification to minute bars and creates buy/sell volume columns.

4. Later notebooks  
   Use the processed files to compute exchange-direction VPIN, forecasts, placebo tests, and robustness checks.

## Processed files

After running the notebooks, `data/processed/` should contain files such as:

| File | Description |
|---|---|
| `btcusdt_1min_2020_q1.csv` | Cleaned one-minute OHLCV data |
| `btcusdt_1min_classified_2020_q1.csv` | Minute-level data with tick-rule signs and buy/sell volumes |
| `btcusdt_tr_vpin_with_u2_2020_q1.csv` | Volume buckets with TR-VPIN and U2-VPIN |
| `btcusdt_exchange_vpin_2020_q1.csv` | VPIN based on exchange-reported trade direction |
| `forecast_train.csv` | Training sample for volatility forecasting |
| `forecast_test.csv` | March out-of-sample forecasting sample |

The exact set of files may vary slightly depending on which notebooks have been run.

## Data-quality checks

The data-preparation notebook checks that:

- timestamps are unique and increasing;
- the sample covers the full Q1 2020 period;
- there are no unexpected missing minutes;
- volume is non-negative;
- price and volume fields have valid numeric types;
- the total classified volume is preserved when constructing volume buckets.

The test suite also verifies that volume buckets conserve total and side-specific volume, that bucket boundaries are correct, and that VPIN calculations do not use future information.

## Git policy

Do **not** commit the following:

```text
data/raw/
```

Raw Binance files can be large and should be downloaded locally. Only small processed outputs needed to reproduce tables and figures, if any, should be committed deliberately.
