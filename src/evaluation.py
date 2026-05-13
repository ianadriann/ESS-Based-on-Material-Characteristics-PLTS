from pathlib import Path
from typing import Dict
import pandas as pd


def summarize_case(result: dict) -> dict:
    pv = result["pv"]
    voltage = result["voltage"]
    line = result["line"]
    ess = result["ess"]

    total_pv_avail = pv["PV_available_kW"].sum()
    total_curt = pv["Curtailment_kW"].sum()
    curt_pct = 100.0 * total_curt / total_pv_avail if total_pv_avail > 1e-9 else 0.0

    return {
        "case": result["case"],
        "objective": result["objective"],
        "total_pv_available_kWh": total_pv_avail,
        "total_curtailment_kWh": total_curt,
        "curtailment_pct": curt_pct,
        "v_min_pu": voltage["V_pu"].min(),
        "v_max_pu": voltage["V_pu"].max(),
        "max_line_loading_pct": line["Loading_pct"].max(),
        "ess_total_energy_kWh": ess.drop_duplicates("Bus")["E_kWh"].sum() if not ess.empty else 0.0,
        "ess_total_power_kW": ess.drop_duplicates("Bus")["Pcap_kW"].sum() if not ess.empty else 0.0,
        "ess_buses": ",".join(map(str, sorted(ess["Bus"].unique()))) if not ess.empty else "-",
    }


def summarize_all(results: Dict[str, dict], out_path: str | Path = "results/tables/summary_cases.csv") -> pd.DataFrame:
    df = pd.DataFrame([summarize_case(r) for r in results.values()])
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)
    return df
