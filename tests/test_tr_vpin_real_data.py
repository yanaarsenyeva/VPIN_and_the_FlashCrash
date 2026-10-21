from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.tr_vpin import (
    build_volume_buckets,
    calculate_tr_vpin,
    calculate_u2_benchmark,
)


ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"


@pytest.fixture(scope="module")
def real_case():
    import json

    data_path = (
        PROCESSED / "btcusdt_1min_classified_2020_q1.csv"
    )

    if not data_path.exists():
        pytest.skip(
            "Prepared real data not found. Run 02_binance_data.ipynb first."
        )

    data = pd.read_csv(data_path)

    for column in ["minute_start", "available_at"]:
        data[column] = pd.to_datetime(data[column], utc=True)

    data["tick_sign"] = pd.to_numeric(
        data["tick_sign"], errors="raise"
    )

    data["is_classified"] = (
        data["volume_btc"].gt(0)
        & data["tick_sign"].isin([-1, 1])
    )

    with (ROOT / "research_config.json").open(
        encoding="utf-8"
    ) as file:
        config = json.load(file)

    volume = float(config["bucket_volume_btc"])
    window = int(config["vpin_window"])

    buckets = build_volume_buckets(data, volume)
    vpin = calculate_tr_vpin(buckets, volume, window)

    return data, volume, window, buckets, vpin


def test_total_and_side_volume_conserved(real_case):
    data, _, _, buckets, _ = real_case

    eligible = data.loc[data["is_classified"]]

    np.testing.assert_allclose(
        buckets["volume_btc"].sum(),
        eligible["volume_btc"].sum(),
        rtol=1e-10,
        atol=1e-8,
    )

    for sign, column in [
        (1, "buy_volume_btc"),
        (-1, "sell_volume_btc"),
    ]:
        expected = eligible.loc[
            eligible["tick_sign"].eq(sign), "volume_btc"
        ].sum()

        np.testing.assert_allclose(
            buckets[column].sum(),
            expected,
            rtol=1e-10,
            atol=1e-8,
        )


def test_complete_buckets_and_residual(real_case):
    _, volume, _, buckets, _ = real_case

    full = buckets.loc[buckets["is_complete"]]
    partial = buckets.loc[~buckets["is_complete"]]

    np.testing.assert_allclose(
        full["volume_btc"],
        volume,
        rtol=1e-10,
        atol=1e-8,
    )

    assert len(partial) <= 1

    if not partial.empty:
        assert partial.index[0] == buckets.index[-1]
        assert 0 < partial["volume_btc"].iloc[0] < volume

    assert buckets["bucket_id"].is_unique
    assert buckets["bucket_id"].diff().dropna().eq(1).all()


def test_first_five_buckets_independently(real_case):
    data, volume, _, buckets, _ = real_case

    eligible = data.loc[data["is_classified"]]

    quantities = eligible["volume_btc"].to_numpy(dtype=float)
    signs = eligible["tick_sign"].to_numpy(dtype=int)

    ends = np.cumsum(quantities)
    starts = np.concatenate(([0.0], ends[:-1]))

    assert len(buckets.loc[buckets["is_complete"]]) >= 5

    for bucket_id in range(5):
        left = bucket_id * volume
        right = (bucket_id + 1) * volume

        overlap = np.maximum(
            0.0,
            np.minimum(ends, right)
            - np.maximum(starts, left),
        )

        actual = buckets.loc[
            buckets["bucket_id"].eq(bucket_id)
        ].iloc[0]

        np.testing.assert_allclose(
            actual["buy_volume_btc"],
            overlap[signs == 1].sum(),
            rtol=1e-10,
            atol=1e-8,
        )

        np.testing.assert_allclose(
            actual["sell_volume_btc"],
            overlap[signs == -1].sum(),
            rtol=1e-10,
            atol=1e-8,
        )


def test_vpin_formula_and_warmup(real_case):
    _, volume, window, _, vpin = real_case

    direct_oi = (
        vpin["buy_volume_btc"]
        - vpin["sell_volume_btc"]
    ).abs().to_numpy() / volume

    np.testing.assert_allclose(
        vpin["oi"],
        direct_oi,
        rtol=1e-12,
        atol=1e-12,
    )

    assert len(vpin) >= window

    expected = np.convolve(
        direct_oi,
        np.ones(window) / window,
        mode="valid",
    )

    assert vpin["tr_vpin"].iloc[:window - 1].isna().all()

    np.testing.assert_allclose(
        vpin["tr_vpin"].iloc[window - 1:],
        expected,
        rtol=1e-10,
        atol=1e-12,
    )

    assert vpin["tr_vpin"].notna().sum() == (
        len(vpin) - window + 1
    )


def test_ranges_and_availability(real_case):
    data, _, _, buckets, vpin = real_case

    tolerance = 1e-10

    assert vpin["oi"].between(
        -tolerance, 1 + tolerance
    ).all()

    assert vpin["tr_vpin"].dropna().between(
        -tolerance, 1 + tolerance
    ).all()

    assert buckets["available_at"].is_monotonic_increasing

    source_times = pd.DatetimeIndex(data["available_at"])

    assert buckets["available_at"].isin(source_times).all()

    assert (
        buckets["available_at"]
        >= buckets["first_source_minute"]
        + pd.Timedelta(minutes=1)
    ).all()


def test_u2_formula_first_five_buckets(real_case):
    data, volume, window, buckets, _ = real_case

    result = calculate_u2_benchmark(
        data,
        buckets,
        volume,
        window,
    )

    eligible = data.loc[data["is_classified"]]
    quantities = eligible["volume_btc"].to_numpy(dtype=float)

    ends = np.cumsum(quantities)
    starts = np.concatenate(([0.0], ends[:-1]))

    for bucket_id in range(5):
        left = bucket_id * volume
        right = (bucket_id + 1) * volume

        overlap = np.maximum(
            0.0,
            np.minimum(ends, right)
            - np.maximum(starts, left),
        )

        expected = np.sqrt(np.sum((overlap / volume) ** 2))

        actual = result.loc[
            result["bucket_id"].eq(bucket_id), "u2"
        ].iloc[0]

        np.testing.assert_allclose(
            actual,
            expected,
            rtol=1e-9,
            atol=1e-9,
        )