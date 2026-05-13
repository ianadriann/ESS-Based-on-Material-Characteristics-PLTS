import pandas as pd


def build_ess_scenarios(ranked_sse: pd.DataFrame) -> dict:
    """
    Membentuk skenario ESS berdasarkan ranking kandidat SSE.
    ESS-1 konservatif menggunakan kandidat ranking 3,
    ESS-2 moderat menggunakan kandidat ranking 2,
    ESS-3 advanced menggunakan kandidat ranking 1.
    """

    if ranked_sse.empty:
        raise ValueError("Ranking SSE kosong. Periksa data sse_candidates.csv.")

    # Ambil kandidat sesuai ranking.
    # Jika kandidat kurang dari 3, gunakan kandidat terakhir yang tersedia.
    rank_1 = ranked_sse.iloc[0]
    rank_2 = ranked_sse.iloc[1] if len(ranked_sse) > 1 else ranked_sse.iloc[0]
    rank_3 = ranked_sse.iloc[2] if len(ranked_sse) > 2 else ranked_sse.iloc[-1]

    return {
        "baseline_no_ess": None,

        "ESS_1_conservative": {
            "basis": "conservative",
            "linked_material": rank_3["formula"],
            "linked_material_id": rank_3["material_id"],
            "sse_score": float(rank_3["weighted_score"]),
            "round_trip_eff": 0.85,
            "soc_min": 0.20,
            "soc_max": 0.90,
            "power_energy_ratio": 0.25,
            "cost_per_kwh": 250.0,
        },

        "ESS_2_moderate": {
            "basis": "moderate",
            "linked_material": rank_2["formula"],
            "linked_material_id": rank_2["material_id"],
            "sse_score": float(rank_2["weighted_score"]),
            "round_trip_eff": 0.90,
            "soc_min": 0.15,
            "soc_max": 0.90,
            "power_energy_ratio": 0.33,
            "cost_per_kwh": 300.0,
        },

        "ESS_3_advanced": {
            "basis": "advanced",
            "linked_material": rank_1["formula"],
            "linked_material_id": rank_1["material_id"],
            "sse_score": float(rank_1["weighted_score"]),
            "round_trip_eff": 0.95,
            "soc_min": 0.10,
            "soc_max": 0.95,
            "power_energy_ratio": 0.50,
            "cost_per_kwh": 400.0,
        },
    }


def scenarios_to_frame(scenarios: dict) -> pd.DataFrame:
    rows = []
    for name, sc in scenarios.items():
        if sc is None:
            rows.append({
                "scenario": name,
                "basis": "no ESS",
                "linked_material": "-",
                "linked_material_id": "-",
                "sse_score": "-",
            })
        else:
            rows.append({"scenario": name, **sc})
    return pd.DataFrame(rows)