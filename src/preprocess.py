from typing import Dict, Tuple
import pandas as pd


def build_load_timeseries(bus: pd.DataFrame, load_profile: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, b in bus.iterrows():
        for _, h in load_profile.iterrows():
            rows.append({
                "Bus": int(b["Bus"]),
                "Hour": int(h["Hour"]),
                "Load_kW": float(b["P_base_kW"]) * float(h["LoadMultiplier"]),
            })
    return pd.DataFrame(rows)


def build_pv_profile(irradiance: pd.DataFrame, pv_config: Dict) -> pd.DataFrame:
    eff = float(pv_config.get("efficiency", 0.18))
    area_per_kw = float(pv_config.get("area_per_kw", 5.0))
    pv_buses = [int(x) for x in pv_config["buses"]]
    cap_map = {int(k): float(v) for k, v in pv_config["capacity_kw"].items()}

    rows = []
    for _, r in irradiance.iterrows():
        hour = int(r["Hour"])
        irr = float(r["Irradiance_Wm2"])
        factor = irr * area_per_kw * eff / 1000.0
        factor = max(0.0, min(factor, 1.0))
        for bus in pv_buses:
            rows.append({
                "Bus": bus,
                "Hour": hour,
                "PV_available_kW": cap_map[bus] * factor,
                "PV_factor": factor,
                "Irradiance_Wm2": irr,
            })
    return pd.DataFrame(rows)


def build_adjacency(line: pd.DataFrame) -> Tuple[dict, dict]:
    buses = sorted(set(line["From"]).union(set(line["To"])))
    edges_by_from = {int(b): [] for b in buses}
    edges_by_to = {int(b): [] for b in buses}
    for _, r in line.iterrows():
        e = int(r["Line"])
        edges_by_from[int(r["From"])].append(e)
        edges_by_to[int(r["To"])].append(e)
    return edges_by_from, edges_by_to
