import numpy as np
import pandas as pd


def build_volume_buckets(
    classified: pd.DataFrame,
    bucket_volume: float,
) -> pd.DataFrame:
    if not np.isfinite(bucket_volume) or bucket_volume <= 0:
        raise ValueError("bucket_volume должен быть положительным")

    required = [
        "minute_start",
        "available_at",
        "volume_btc",
        "tick_sign",
        "is_classified",
    ]

    missing = set(required) - set(classified.columns)
    if missing:
        raise ValueError(f"Отсутствуют колонки: {sorted(missing)}")

    data = classified.loc[
        classified["is_classified"], required
    ].copy()

    if data.empty:
        raise ValueError("Нет классифицированного объёма")

    if not data["minute_start"].is_monotonic_increasing:
        raise ValueError("Нарушен порядок минут")

    if not data["minute_start"].is_unique:
        raise ValueError("Повторяются минутные метки")

    volumes = data["volume_btc"].to_numpy(dtype=float)

    if not np.isfinite(volumes).all() or (volumes <= 0).any():
        raise ValueError("Некорректные объёмы")

    if not data["tick_sign"].isin([-1, 1]).all():
        raise ValueError("Некорректные знаки")

    records = []
    space = float(bucket_volume)
    buy = 0.0
    sell = 0.0
    first_minute = None
    last_available = None

    for row in data.itertuples(index=False):
        remaining = float(row.volume_btc)
        sign = int(row.tick_sign)

        while remaining > 0:
            if first_minute is None:
                first_minute = row.minute_start

            completes_bucket = remaining >= space
            piece = space if completes_bucket else remaining

            if sign == 1:
                buy += piece
            else:
                sell += piece

            last_available = row.available_at

            if completes_bucket:
                records.append({
                    "bucket_id": len(records),
                    "first_source_minute": first_minute,
                    "available_at": last_available,
                    "buy_volume_btc": buy,
                    "sell_volume_btc": sell,
                    "is_complete": True,
                })

                remaining -= piece
                space = float(bucket_volume)
                buy = 0.0
                sell = 0.0
                first_minute = None

            else:
                space -= piece
                remaining = 0.0

    if first_minute is not None:
        records.append({
            "bucket_id": len(records),
            "first_source_minute": first_minute,
            "available_at": last_available,
            "buy_volume_btc": buy,
            "sell_volume_btc": sell,
            "is_complete": False,
        })

    buckets = pd.DataFrame(records)

    buckets["volume_btc"] = (
        buckets["buy_volume_btc"]
        + buckets["sell_volume_btc"]
    )

    return buckets


def calculate_tr_vpin(
    buckets: pd.DataFrame,
    bucket_volume: float,
    window: int = 50,
) -> pd.DataFrame:
    if not isinstance(window, int) or window < 1:
        raise ValueError("window должен быть положительным целым числом")

    result = buckets.loc[buckets["is_complete"]].copy()

    if not np.allclose(
        result["volume_btc"],
        bucket_volume,
        rtol=1e-10,
        atol=1e-8,
    ):
        raise ValueError("Объём полного бакета не равен заданному")

    result["oi"] = (
        result["buy_volume_btc"] - result["sell_volume_btc"]
    ).abs() / bucket_volume

    result["tr_vpin"] = (
        result["oi"]
        .rolling(window=window, min_periods=window)
        .mean()
    )

    return result

def calculate_u2_benchmark(
    classified: pd.DataFrame,
    buckets: pd.DataFrame,
    bucket_volume: float,
    window: int = 50,
) -> pd.DataFrame:
    if not np.isfinite(bucket_volume) or bucket_volume <= 0:
        raise ValueError("Некорректный размер бакета")

    if not isinstance(window, int) or window < 1:
        raise ValueError("Некорректное окно")

    data = classified.loc[
        classified["is_classified"],
        ["minute_start", "volume_btc"],
    ].copy()

    if not data["minute_start"].is_monotonic_increasing:
        raise ValueError("Нарушен порядок минут")

    volumes = data["volume_btc"].to_numpy(dtype=float)

    if not np.isfinite(volumes).all() or (volumes <= 0).any():
        raise ValueError("Некорректные объёмы")

    ends = np.cumsum(volumes)
    starts = np.concatenate(([0.0], ends[:-1]))

    full = buckets.loc[buckets["is_complete"]].copy()
    rows = []

    for bucket_id in full["bucket_id"]:
        left = int(bucket_id) * bucket_volume
        right = left + bucket_volume

        first = np.searchsorted(ends, left, side="right")
        stop = np.searchsorted(starts, right, side="left")

        pieces = (
            np.minimum(ends[first:stop], right)
            - np.maximum(starts[first:stop], left)
        )

        pieces = pieces[pieces > 0]

        if not np.isclose(
            pieces.sum(),
            bucket_volume,
            rtol=1e-9,
            atol=1e-7,
        ):
            raise ValueError(
                f"Не сохранился объём в бакете {bucket_id}"
            )

        weights = pieces / bucket_volume

        rows.append({
            "bucket_id": int(bucket_id),
            "q_blocks": len(pieces),
            "u2": float(np.sqrt(np.sum(weights ** 2))),
        })

    result = pd.DataFrame(rows)

    result["u2_vpin"] = (
        result["u2"]
        .rolling(window=window, min_periods=window)
        .mean()
    )

    return result