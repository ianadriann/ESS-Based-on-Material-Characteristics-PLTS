import pandas as pd


def _get_material_by_class(evidence_sse: pd.DataFrame, class_name: str):
    matched = evidence_sse[
        evidence_sse["evidence_based_class"].astype(str).str.lower() == class_name
    ]

    if matched.empty:
        raise ValueError(
            f"Tidak ada material dengan evidence_based_class = {class_name}. "
            "Periksa results/tables/sse_candidates_evidence_based.csv"
        )

    return matched.iloc[0]


def _get_scenario_level_params(scenario_type: str) -> dict:
    """
    Parameter ESS di bawah ini adalah parameter skenario level sistem,
    bukan hasil perhitungan langsung dari material SSE.

    Parameter ini TIDAK dihitung dari weighted_score, interface_stability,
    maturity, atau variabel asumsi lain.

    Dalam paper, wajib dijelaskan sebagai:
    'scenario-level operational and techno-economic assumptions'.
    """

    scenario_params = {
        "conservative": {
            "round_trip_eff": 0.8900,
            "soc_min": 0.25,
            "soc_max": 0.85,
            "power_energy_ratio": 0.3500,
            "cost_per_kwh": 315.0,
        },
        "moderate": {
            "round_trip_eff": 0.9282,
            "soc_min": 0.20,
            "soc_max": 0.91,
            "power_energy_ratio": 0.3804,
            "cost_per_kwh": 270.0,
        },
        "advanced": {
            "round_trip_eff": 0.9240,
            "soc_min": 0.15,
            "soc_max": 0.95,
            "power_energy_ratio": 0.3400,
            "cost_per_kwh": 402.5,
        },
    }

    if scenario_type not in scenario_params:
        raise ValueError(f"Unknown ESS scenario type: {scenario_type}")

    return scenario_params[scenario_type]


def build_ess_scenarios(evidence_sse: pd.DataFrame) -> dict:
    """
    Membentuk skenario ESS berdasarkan evidence-based screening class.

    Tidak menggunakan:
    - weighted_score
    - score_ionic
    - score_interface
    - score_maturity
    - interface_stability
    - maturity

    Mapping:
    - conservative -> ESS_1_conservative
    - moderate     -> ESS_2_moderate
    - advanced     -> ESS_3_advanced
    """

    if evidence_sse.empty:
        raise ValueError(
            "Data evidence-based SSE kosong. "
            "Periksa results/tables/sse_candidates_evidence_based.csv."
        )

    required_cols = [
        "material_id",
        "formula",
        "evidence_based_class",
    ]

    missing_cols = [c for c in required_cols if c not in evidence_sse.columns]
    if missing_cols:
        raise ValueError(f"Kolom berikut tidak ada pada evidence_sse: {missing_cols}")

    conservative = _get_material_by_class(evidence_sse, "conservative")
    moderate = _get_material_by_class(evidence_sse, "moderate")
    advanced = _get_material_by_class(evidence_sse, "advanced")

    ess1_params = _get_scenario_level_params("conservative")
    ess2_params = _get_scenario_level_params("moderate")
    ess3_params = _get_scenario_level_params("advanced")

    mapping_note = (
        "ESS parameters are scenario-level operational assumptions informed by "
        "evidence-based SSE screening class, not direct battery-cell design values."
    )

    return {
        "baseline_no_ess": None,

        "ESS_1_conservative": {
            "basis": "conservative",
            "linked_material": conservative["formula"],
            "linked_material_id": conservative["material_id"],
            "screening_class": "conservative",
            "mapping_note": mapping_note,
            **ess1_params,
        },

        "ESS_2_moderate": {
            "basis": "moderate",
            "linked_material": moderate["formula"],
            "linked_material_id": moderate["material_id"],
            "screening_class": "moderate",
            "mapping_note": mapping_note,
            **ess2_params,
        },

        "ESS_3_advanced": {
            "basis": "advanced",
            "linked_material": advanced["formula"],
            "linked_material_id": advanced["material_id"],
            "screening_class": "advanced",
            "mapping_note": mapping_note,
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
                "screening_class": "-",
                "round_trip_eff": "",
                "soc_min": "",
                "soc_max": "",
                "power_energy_ratio": "",
                "cost_per_kwh": "",
                "mapping_note": "Baseline case without ESS.",
            })
        else:
            rows.append({"scenario": name, **sc})

    return pd.DataFrame(rows)