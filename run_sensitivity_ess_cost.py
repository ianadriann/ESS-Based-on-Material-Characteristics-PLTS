import copy
import pandas as pd
from pathlib import Path

from src.data_loader import load_config, load_network_data
from src.preprocess import build_load_timeseries, build_pv_profile
from src.ess_scenarios import build_ess_scenarios
from src.milp_model import solve_milp_case
from src.evaluation import summarize_case


OUT_DIR = Path("results/tables")
OUT_DIR.mkdir(parents=True, exist_ok=True)

EVIDENCE_PATH = Path("results/tables/sse_candidates_evidence_based.csv")

cost_factors = {
    "cost_minus_20": 0.80,
    "cost_base": 1.00,
    "cost_plus_20": 1.20,
}

config = load_config()
network = load_network_data()
load_ts = build_load_timeseries(network["bus"], network["load_profile"])
pv_ts = build_pv_profile(network["irradiance"], config["pv"])

if not EVIDENCE_PATH.exists():
    raise FileNotFoundError(
        "File evidence-based SSE belum ditemukan:\n"
        "results/tables/sse_candidates_evidence_based.csv\n\n"
        "Jalankan dulu:\n"
        "python3 result_paper/build_sse_candidates_evidence_based.py"
    )

evidence_sse = pd.read_csv(EVIDENCE_PATH)
base_scenarios = build_ess_scenarios(evidence_sse)

if "generic_ess" not in base_scenarios:
    raise ValueError(
        "generic_ess belum ada di build_ess_scenarios(). "
        "Periksa src/ess_scenarios.py."
    )

summary_rows = []

for factor_name, factor in cost_factors.items():
    print(f"\n=== Running ESS cost sensitivity: {factor_name} ===")

    for scenario_name, scenario in base_scenarios.items():

        # Baseline only needs to be solved once at base cost
        if scenario is None:
            if factor_name != "cost_base":
                continue

            case_name = "baseline_no_ess"
            result = solve_milp_case(
                case_name=case_name,
                config=config,
                network=network,
                load_ts=load_ts,
                pv_ts=pv_ts,
                ess_scenario=None,
            )

        else:
            scenario_mod = copy.deepcopy(scenario)
            scenario_mod["cost_per_kwh"] = scenario_mod["cost_per_kwh"] * factor

            case_name = f"{scenario_name}_{factor_name}"

            result = solve_milp_case(
                case_name=case_name,
                config=config,
                network=network,
                load_ts=load_ts,
                pv_ts=pv_ts,
                ess_scenario=scenario_mod,
            )

        row = summarize_case(result)
        row["sensitivity_type"] = "ESS cost"
        row["sensitivity_case"] = factor_name
        row["cost_factor"] = factor
        summary_rows.append(row)

df = pd.DataFrame(summary_rows)
df.to_csv(OUT_DIR / "sensitivity_ess_cost.csv", index=False)

pd.set_option("display.max_columns", None)
print("\n=== ESS COST SENSITIVITY SUMMARY ===")
print(df)
print("\nSaved to results/tables/sensitivity_ess_cost.csv")