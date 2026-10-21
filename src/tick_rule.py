import numpy as np
import pandas as pd


def classify_minutes_tick_rule(bars):
    """Classify whole-minute volume by the sign of the close-to-close change
    between consecutive non-empty minutes. Zero change carries the last sign."""
    out = bars.copy()
    observed = out["trade_count"].gt(0)

    price_change = out.loc[observed, "close"].diff()
    observed_sign = np.sign(price_change).replace(0, np.nan).ffill()

    out["tick_sign"] = pd.Series(pd.NA, index=out.index, dtype="Int8")
    out.loc[observed, "tick_sign"] = observed_sign.astype("Int8")

    out["is_classified"] = observed & out["tick_sign"].notna()

    out["buy_volume_btc"] = np.where(
        out["tick_sign"].eq(1).fillna(False), out["volume_btc"], 0.0
    )
    out["sell_volume_btc"] = np.where(
        out["tick_sign"].eq(-1).fillna(False), out["volume_btc"], 0.0
    )
    return out