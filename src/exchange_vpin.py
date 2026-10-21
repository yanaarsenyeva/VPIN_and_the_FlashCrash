import numpy as np
import pandas as pd


COLUMNS = [
    "trade_id",
    "price",
    "qty",
    "quote_qty",
    "time",
    "is_buyer_maker",
    "is_best_match",
]


def build_exchange_buckets(
    paths,
    bucket_volume,
    start_time,
    window=50,
    chunksize=500_000,
):
    if not np.isfinite(bucket_volume) or bucket_volume <= 0:
        raise ValueError("Некорректный размер бакета")

    if not isinstance(window, int) or window < 1:
        raise ValueError("Некорректное окно")

    start_time = pd.Timestamp(start_time)

    if start_time.tzinfo is None:
        raise ValueError("start_time должен содержать часовой пояс")

    start_ms = start_time.value // 1_000_000

    total_volume = 0.0
    total_buy = 0.0
    previous_boundary_buy = 0.0
    completed = 0
    records = []
    previous_trade_id = None

    for path in paths:
        print(f"Читаем {path.name}...")

        reader = pd.read_csv(
            path,
            header=None,
            names=COLUMNS,
            usecols=["trade_id", "qty", "time", "is_buyer_maker"],
            dtype={
                "trade_id": "int64",
                "qty": "float64",
                "time": "int64",
                "is_buyer_maker": "string",
            },
            chunksize=chunksize,
        )

        for chunk in reader:
            chunk = chunk.loc[chunk["time"].ge(start_ms)]

            if chunk.empty:
                continue

            ids = chunk["trade_id"].to_numpy()

            if (np.diff(ids) != 1).any():
                raise ValueError("Нарушена последовательность trade_id")

            if (
                previous_trade_id is not None
                and ids[0] != previous_trade_id + 1
            ):
                raise ValueError("Разрыв trade_id между порциями")

            previous_trade_id = int(ids[-1])

            flags = (
                chunk["is_buyer_maker"]
                .str.strip()
                .str.lower()
            )

            if not flags.isin(["true", "false"]).all():
                raise ValueError("Некорректный maker-флаг")

            quantities = chunk["qty"].to_numpy(dtype=float)
            buyer_initiated = flags.eq("false").to_numpy(dtype=bool)

            if (
                not np.isfinite(quantities).all()
                or (quantities <= 0).any()
            ):
                raise ValueError("Некорректный объём")

            local_ends = np.cumsum(quantities)
            global_ends = total_volume + local_ends

            buy_prefix = np.concatenate((
                [0.0],
                np.cumsum(
                    np.where(buyer_initiated, quantities, 0.0)
                ),
            ))

            local_starts = np.concatenate((
                [0.0],
                local_ends[:-1],
            ))

            last_complete = int(
                np.floor(global_ends[-1] / bucket_volume)
            )

            for boundary_number in range(
                completed + 1, last_complete + 1
            ):
                boundary = boundary_number * bucket_volume

                index = int(np.searchsorted(
                    global_ends, boundary, side="left"
                ))

                if index >= len(chunk):
                    raise ValueError("Граница вне текущей порции")

                within_trade = (
                    boundary
                    - total_volume
                    - local_starts[index]
                )

                within_trade = float(np.clip(
                    within_trade, 0.0, quantities[index]
                ))

                buy_at_boundary = (
                    total_buy
                    + buy_prefix[index]
                    + (
                        within_trade
                        if buyer_initiated[index]
                        else 0.0
                    )
                )

                bucket_buy = (
                    buy_at_boundary - previous_boundary_buy
                )
                bucket_sell = bucket_volume - bucket_buy

                records.append({
                    "bucket_id": boundary_number - 1,
                    "completion_time_ms": int(
                        chunk["time"].iloc[index]
                    ),
                    "buy_volume_btc": bucket_buy,
                    "sell_volume_btc": bucket_sell,
                })

                previous_boundary_buy = buy_at_boundary

            completed = last_complete
            total_volume = float(global_ends[-1])
            total_buy += float(buy_prefix[-1])

    if not records:
        raise ValueError("Не сформировано ни одного полного бакета")

    result = pd.DataFrame(records)

    result["completion_time"] = pd.to_datetime(
        result["completion_time_ms"], unit="ms", utc=True
    )

    result["available_at"] = (
        result["completion_time"].dt.floor("min")
        + pd.Timedelta(minutes=1)
    )

    result["oi"] = (
        result["buy_volume_btc"] - result["sell_volume_btc"]
    ).abs() / bucket_volume

    result["exchange_vpin"] = (
        result["oi"]
        .rolling(window, min_periods=window)
        .mean()
    )

    residual_buy = total_buy - previous_boundary_buy
    residual_volume = total_volume - completed * bucket_volume

    accounting = {
        "source_volume_btc": total_volume,
        "source_buy_volume_btc": total_buy,
        "complete_buckets": completed,
        "residual_volume_btc": residual_volume,
        "residual_buy_volume_btc": residual_buy,
        "residual_sell_volume_btc": residual_volume - residual_buy,
    }

    return result, accounting