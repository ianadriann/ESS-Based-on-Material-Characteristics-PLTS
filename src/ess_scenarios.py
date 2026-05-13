import pandas as pd


def _clip(value, lower, upper):
    return max(lower, min(value, upper))


def _map_material_to_ess_params(row, scenario_type):
    """
    Mapping sederhana dari skor material SSE ke parameter ESS.

    Catatan:
    - Ini bukan desain baterai final.
    - Mapping ini adalah pendekatan skenario untuk menerjemahkan karakteristik material
      menjadi parameter ESS level sistem.
    """

    weighted_score = float(row["weighted_score"])
    ionic_score = float(row["score_ionic"])
    interface_score = float(row["score_interface"])
    ec_score = float(row["score_ec_stability"])
    maturity_score = float(row["score_maturity"])

    # Efisiensi dipengaruhi oleh weighted score dan ionic conductivity.
    # Semakin tinggi skor material dan konduktivitas ionik, semakin tinggi efisiensi.
    round_trip_eff = 0.84 + 0.12 * weighted_score + 0.02 * ionic_score
    round_trip_eff = _clip(round_trip_eff, 0.84, 0.96)

    # SOC window dipengaruhi oleh interface stability dan electrochemical stability.
    # Material dengan stabilitas lebih baik diberi SOC window lebih lebar.
    soc_min = 0.25 - 0.10 * interface_score
    soc_max = 0.85 + 0.10 * ec_score

    soc_min = _clip(soc_min, 0.10, 0.25)
    soc_max = _clip(soc_max, 0.85, 0.95)

    # Rasio daya terhadap energi dipengaruhi oleh ionic conductivity.
    # Semakin tinggi ionic conductivity, semakin besar kemampuan charge/discharge relatif.
    power_energy_ratio = 0.20 + 0.20 * weighted_score + 0.10 * ionic_score
    power_energy_ratio = _clip(power_energy_ratio, 0.20, 0.50)

    # Biaya relatif.
    # Material dengan maturity lebih tinggi diasumsikan memiliki risiko/biaya lebih rendah.
    # Namun skenario advanced tetap diberi biaya lebih tinggi karena performa tinggi.
    base_cost = 350 - 80 * maturity_score

    if scenario_type == "conservative":
        cost_per_kwh = base_cost * 0.90
    elif scenario_type == "moderate":
        cost_per_kwh = base_cost * 1.00
    elif scenario_type == "advanced":
        cost_per_kwh = base_cost * 1.15
    else:
        cost_per_kwh = base_cost

    cost_per_kwh = _clip(cost_per_kwh, 180, 450)

    return {
        "round_trip_eff": round(round_trip_eff, 4),
        "soc_min": round(soc_min, 4),
        "soc_max": round(soc_max, 4),
        "power_energy_ratio": round(power_energy_ratio, 4),
        "cost_per_kwh": round(cost_per_kwh, 2),
    }


def build_ess_scenarios(ranked_sse: pd.DataFrame) -> dict:
    """
    Membentuk skenario ESS berdasarkan ranking kandidat SSE.

    ESS-1 konservatif menggunakan kandidat ranking 3.
    ESS-2 moderat menggunakan kandidat ranking 2.
    ESS-3 advanced menggunakan kandidat ranking 1.
    """

    if ranked_sse.empty:
        raise ValueError("Ranking SSE kosong. Periksa data sse_candidates.csv.")

    rank_1 = ranked_sse.iloc[0]
    rank_2 = ranked_sse.iloc[1] if len(ranked_sse) > 1 else ranked_sse.iloc[0]
    rank_3 = ranked_sse.iloc[2] if len(ranked_sse) > 2 else ranked_sse.iloc[-1]

    ess1_params = _map_material_to_ess_params(rank_3, "conservative")
    ess2_params = _map_material_to_ess_params(rank_2, "moderate")
    ess3_params = _map_material_to_ess_params(rank_1, "advanced")

    return {
        "baseline_no_ess": None,

        "ESS_1_conservative": {
            "basis": "conservative",
            "linked_material": rank_3["formula"],
            "linked_material_id": rank_3["material_id"],
            "sse_score": float(rank_3["weighted_score"]),
            **ess1_params,
        },

        "ESS_2_moderate": {
            "basis": "moderate",
            "linked_material": rank_2["formula"],
            "linked_material_id": rank_2["material_id"],
            "sse_score": float(rank_2["weighted_score"]),
            **ess2_params,
        },

        "ESS_3_advanced": {
            "basis": "advanced",
            "linked_material": rank_1["formula"],
            "linked_material_id": rank_1["material_id"],
            "sse_score": float(rank_1["weighted_score"]),
            **ess3_params,
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