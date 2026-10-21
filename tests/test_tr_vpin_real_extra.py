import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.tr_vpin import build_volume_buckets, calculate_tr_vpin
from src.tick_rule import classify_minutes_tick_rule  # only after step 2.2

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"


@pytest.fixture(scope="module")
def classified():
    path = PROCESSED / "btcusdt_1min_classified_2020_q1.csv"
    if not path.exists():
        pytest.skip("Prepared real data not found. Run 02_binance_data.ipynb first.")
    data = pd.read_csv(path)
    for column in ["minute_start", "available_at"]:
        data[column] = pd.to_datetime(data[column], utc=True)
    data["tick_sign"] = pd.to_numeric(data["tick_sign"], errors="raise")
    data["is_classified"] = data["volume_btc"].gt(0) & data["tick_sign"].isin([-1, 1])
    return data


@pytest.fixture(scope="module")
def params():
    with (ROOT / "research_config.json").open(encoding="utf-8") as file:
        config = json.load(file)
    return float(config["bucket_volume_btc"]), int(config["vpin_window"])


def test_vpin_does_not_use_future_minutes(classified, params):
    volume, window = params
    cut = classified.iloc[:30_000].copy()

    full = calculate_tr_vpin(build_volume_buckets(classified, volume), volume, window)
    part = calculate_tr_vpin(build_volume_buckets(cut, volume), volume, window)

    merged = part.merge(full, on="bucket_id", suffixes=("_cut", "_full"))
    assert len(merged) == len(part) > window

    np.testing.assert_allclose(
        merged["tr_vpin_cut"], merged["tr_vpin_full"], equal_nan=True
    )
    assert (merged["available_at_cut"] == merged["available_at_full"]).all()
    assert (part["available_at"] <= cut["available_at"].iloc[-1]).all()


def test_all_buckets_independently(classified, params):
    volume, _ = params
    buckets = build_volume_buckets(classified, volume)
    full = buckets.loc[buckets["is_complete"]]

    eligible = classified.loc[classified["is_classified"]]
    q = eligible["volume_btc"].to_numpy(dtype=float)
    s = eligible["tick_sign"].to_numpy(dtype=float)

    ends = np.concatenate(([0.0], np.cumsum(q)))
    cum_buy = np.concatenate(([0.0], np.cumsum(np.where(s == 1, q, 0.0))))
    cum_sell = np.concatenate(([0.0], np.cumsum(np.where(s == -1, q, 0.0))))

    edges = np.arange(len(full) + 1) * volume
    buy = np.diff(np.interp(edges, ends, cum_buy))
    sell = np.diff(np.interp(edges, ends, cum_sell))

    np.testing.assert_allclose(full["buy_volume_btc"], buy, atol=1e-6)
    np.testing.assert_allclose(full["sell_volume_btc"], sell, atol=1e-6)


def test_tick_rule_against_plain_loop():
    path = PROCESSED / "btcusdt_1min_2020_q1.csv"
    if not path.exists():
        pytest.skip("Prepared real data not found. Run 02_binance_data.ipynb first.")
    bars = pd.read_csv(path)

    expected = []
    last_close, last_sign = None, None
    for close, count in zip(bars["close"], bars["trade_count"]):
        if count == 0:
            expected.append(np.nan)
            continue
        if last_close is None:
            sign = np.nan
        else:
            change = close - last_close
            if change > 0:
                last_sign = 1
            elif change < 0:
                last_sign = -1
            sign = np.nan if last_sign is None else last_sign
        last_close = close
        expected.append(sign)

    result = classify_minutes_tick_rule(bars)
    np.testing.assert_array_equal(
        result["tick_sign"].astype("float").to_numpy(), np.array(expected)
    )