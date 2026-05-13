import numpy as np
import pandas as pd


def _minmax(series: pd.Series, benefit: bool = True) -> pd.Series:
    s = series.astype(float)
    if np.isclose(s.max(), s.min()):
        return pd.Series(1.0, index=s.index)
    norm = (s - s.min()) / (s.max() - s.min())
    return norm if benefit else 1.0 - norm


def screen_and_rank_sse(candidates: pd.DataFrame, config: dict) -> pd.DataFrame:
    filters = config["sse_scoring"]["filters"]
    weights = config["sse_scoring"]["weights"]

    df = candidates.copy()
    df = df[df["energy_above_hull"] <= float(filters["max_energy_above_hull"])]
    df = df[df["band_gap"] >= float(filters["min_band_gap"])]

    if df.empty:
        raise ValueError("No SSE candidate passed the initial filters.")

    df["score_stability"] = _minmax(df["energy_above_hull"], benefit=False)
    df["score_band_gap"] = _minmax(df["band_gap"], benefit=True)
    df["score_ionic"] = _minmax(np.log10(df["ionic_conductivity_s_cm"].clip(lower=1e-12)), benefit=True)
    df["score_ec_stability"] = _minmax(df["electrochemical_stability"], benefit=True)
    df["score_interface"] = _minmax(df["interface_stability"], benefit=True)
    df["score_maturity"] = _minmax(df["maturity"], benefit=True)

    df["weighted_score"] = (
        weights["stability"] * df["score_stability"]
        + weights["band_gap"] * df["score_band_gap"]
        + weights["ionic_conductivity"] * df["score_ionic"]
        + weights["electrochemical_stability"] * df["score_ec_stability"]
        + weights["interface_stability"] * df["score_interface"]
        + weights["maturity"] * df["score_maturity"]
    )

    return df.sort_values("weighted_score", ascending=False).reset_index(drop=True)
