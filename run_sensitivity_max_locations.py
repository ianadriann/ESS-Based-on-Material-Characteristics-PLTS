import copy
import pandas as pd
from pathlib import Path

from src.data_loader import load_config, load_network_data, load_sse_candidates
from src.preprocess import build_load_timeseries, build_pv_profile
from src.sse_screening import screen_and_rank_sse
from src.ess_scenarios import build_ess_scenarios
from src.milp_model import solve_milp_case
from src.evaluation import summarize_case


OUT_DIR = Path("results/tables")
OUT_DIR.mkdir(parents=True, exist_ok=True)

max_location_values = [1, 2, 3]

base_config = load_config()
network = load_network_data()
load_ts = build_load_timeseries(network["bus"], network["load_profile"])
pv_ts = build_pv_profile(network["irradiance"], base_config["pv"])

ranked_sse = screen_and_rank_sse(load_sse_candidates(), base_config)
scenarios = build_ess_scenarios(ranked_sse)

summary_rows = []

for max_loc in max_location_values:
    print(f"\n=== Running max_locations sensitivity: {max_loc} ===")

    config = copy.deepcopy(base_config)
    config["ess"]["max_locations"] = max_loc

    for scenario_name, scenario in scenarios.items():
        if scenario is None:
            if max_loc != 3:
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
            case_name = f"{scenario_name}_maxloc_{max_loc}"

            result = solve_milp_case(
                case_name=case_name,
                config=config,
                network=network,
                load_ts=load_ts,
                pv_ts=pv_ts,
                ess_scenario=scenario,
            )

        row = summarize_case(result)
        row["sensitivity_type"] = "Max ESS locations"
        row["sensitivity_case"] = f"maxloc_{max_loc}"
        row["max_locations"] = max_loc
        summary_rows.append(row)

df = pd.DataFrame(summary_rows)
df.to_csv(OUT_DIR / "sensitivity_max_locations.csv", index=False)

pd.set_option("display.max_columns", None)
print("\n=== MAX LOCATION SENSITIVITY SUMMARY ===")
print(df)
print("\nSaved to results/tables/sensitivity_max_locations.csv")