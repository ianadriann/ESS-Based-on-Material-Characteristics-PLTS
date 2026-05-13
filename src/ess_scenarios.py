import pandas as pd


def build_ess_scenarios(ranked_sse: pd.DataFrame) -> dict:
    top_formula = ranked_sse.iloc[0]["formula"] if not ranked_sse.empty else "generic_SSE"

    return {
        "baseline_no_ess": None,
        "ESS_1_conservative": {
            "basis": "conservative",
            "linked_material": top_formula,
            "round_trip_eff": 0.85,
            "soc_min": 0.20,
            "soc_max": 0.90,
            "power_energy_ratio": 0.25,
            "cost_per_kwh": 250.0,
        },
        "ESS_2_moderate": {
            "basis": "moderate",
            "linked_material": top_formula,
            "round_trip_eff": 0.90,
            "soc_min": 0.15,
            "soc_max": 0.90,
            "power_energy_ratio": 0.33,
            "cost_per_kwh": 300.0,
        },
        "ESS_3_advanced": {
            "basis": "advanced",
            "linked_material": top_formula,
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
            rows.append({"scenario": name, "basis": "no ESS"})
        else:
            rows.append({"scenario": name, **sc})
    return pd.DataFrame(rows)
