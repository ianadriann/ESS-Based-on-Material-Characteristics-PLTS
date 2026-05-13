from pathlib import Path

from .data_loader import load_config, load_network_data, load_sse_candidates
from .preprocess import build_load_timeseries, build_pv_profile
from .sse_screening import screen_and_rank_sse
from .ess_scenarios import build_ess_scenarios, scenarios_to_frame
from .milp_model import solve_milp_case
from .evaluation import summarize_all
from .plot_results import plot_voltage_profile, plot_ess_soc


def run_all_cases():
    config = load_config()
    network = load_network_data()
    load_ts = build_load_timeseries(network["bus"], network["load_profile"])
    pv_ts = build_pv_profile(network["irradiance"], config["pv"])

    ranked_sse = screen_and_rank_sse(load_sse_candidates(), config)
    Path("results/tables").mkdir(parents=True, exist_ok=True)
    ranked_sse.to_csv("results/tables/ranked_sse_candidates.csv", index=False)

    scenarios = build_ess_scenarios(ranked_sse)
    scenarios_to_frame(scenarios).to_csv("results/tables/ess_scenarios.csv", index=False)

    results = {}
    for case_name, ess_scenario in scenarios.items():
        print(f"Running case: {case_name}")
        results[case_name] = solve_milp_case(case_name, config, network, load_ts, pv_ts, ess_scenario)
        plot_voltage_profile(results[case_name])
        plot_ess_soc(results[case_name])

    summary = summarize_all(results)
    print(summary)
    return results, summary
