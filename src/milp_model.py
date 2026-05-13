from __future__ import annotations

from typing import Dict, Optional, Any
from pathlib import Path

import pandas as pd
from gurobipy import Model, GRB, quicksum


def solve_milp_case(
    case_name: str,
    config: Dict[str, Any],
    network: Dict[str, pd.DataFrame],
    load_ts: pd.DataFrame,
    pv_ts: pd.DataFrame,
    ess_scenario: Optional[Dict[str, float]],
    output_dir: str | Path = "results/model_outputs",
) -> Dict[str, pd.DataFrame | float | str]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    bus_df = network["bus"]
    line_df = network["line"]

    hours = list(range(int(config["simulation"]["hours"])))
    buses = [int(x) for x in bus_df["Bus"].tolist()]
    slack = int(config["simulation"]["slack_bus"])
    sbase_kw = float(config["simulation"]["base_mva"]) * 1000.0
    vmin2 = float(config["simulation"]["v_min"]) ** 2
    vmax2 = float(config["simulation"]["v_max"]) ** 2

    edges_by_from = {i: [] for i in buses}
    edges_by_to = {i: [] for i in buses}
    for _, r in line_df.iterrows():
        e = int(r["Line"])
        edges_by_from[int(r["From"])].append(e)
        edges_by_to[int(r["To"])].append(e)

    load = {(int(r.Bus), int(r.Hour)): float(r.Load_kW) for r in load_ts.itertuples()}
    pv_avail = {(int(r.Bus), int(r.Hour)): float(r.PV_available_kW) for r in pv_ts.itertuples()}
    pv_buses = sorted(set(k[0] for k in pv_avail.keys()))

    has_ess = ess_scenario is not None
    ess_candidates = [int(x) for x in config["ess"]["candidate_buses"]]
    max_locations = int(config["ess"]["max_locations"])
    e_max = float(config["ess"]["e_max_kwh_per_bus"])
    e_min = float(config["ess"]["e_min_kwh_if_installed"])
    p_max = float(config["ess"]["p_max_kw_per_bus"])
    p_min = float(config["ess"]["p_min_kw_if_installed"])
    soc0_frac = float(config["ess"]["initial_soc_fraction"])

    if has_ess:
        eta_rt = float(ess_scenario["round_trip_eff"])
        eta_ch = eta_rt ** 0.5
        eta_dis = eta_rt ** 0.5
        soc_min_frac = float(ess_scenario["soc_min"])
        soc_max_frac = float(ess_scenario["soc_max"])
        ess_cost = float(ess_scenario["cost_per_kwh"])
    else:
        eta_ch = eta_dis = 1.0
        soc_min_frac = soc_max_frac = 0.0
        ess_cost = 0.0

    grid_cost = float(config["cost"]["grid_energy_cost_per_kwh"])
    curt_cost = float(config["pv"]["curtailment_cost_per_kwh"])

    m = Model(f"MILP_{case_name}")
    m.setParam("OutputFlag", 0)

    P_grid = m.addVars(hours, lb=0.0, name="P_grid_kW")
    V2 = m.addVars(buses, hours, lb=vmin2, ub=vmax2, name="V2")
    P_line = m.addVars(line_df["Line"].astype(int).tolist(), hours, lb=-GRB.INFINITY, name="P_line_kW")
    P_pv_used = m.addVars(pv_buses, hours, lb=0.0, name="P_pv_used_kW")
    P_curt = m.addVars(pv_buses, hours, lb=0.0, name="P_curt_kW")

    if has_ess:
        y = m.addVars(ess_candidates, vtype=GRB.BINARY, name="ESS_install")
        E = m.addVars(ess_candidates, lb=0.0, ub=e_max, name="ESS_energy_kWh")
        Pcap = m.addVars(ess_candidates, lb=0.0, ub=p_max, name="ESS_power_kW")
        P_ch = m.addVars(ess_candidates, hours, lb=0.0, name="P_charge_kW")
        P_dis = m.addVars(ess_candidates, hours, lb=0.0, name="P_discharge_kW")
        SOC = m.addVars(ess_candidates, hours, lb=0.0, name="SOC_kWh")
        u_ch = m.addVars(ess_candidates, hours, vtype=GRB.BINARY, name="u_charge")
        u_dis = m.addVars(ess_candidates, hours, vtype=GRB.BINARY, name="u_discharge")
    else:
        y = E = Pcap = P_ch = P_dis = SOC = u_ch = u_dis = None

    pv_reward = float(config["cost"].get("pv_reward_per_kwh", 0.0))
    planning_years = float(config["simulation"].get("planning_years", 15))
    E_h = 8760 / 24

    obj = (
        quicksum(grid_cost * P_grid[t] * E_h * planning_years for t in hours)
        + quicksum(curt_cost * P_curt[i, t] * E_h * planning_years for i in pv_buses for t in hours)
        - quicksum(pv_reward * P_pv_used[i, t] * E_h * planning_years for i in pv_buses for t in hours)
    )

    if has_ess:
        obj += quicksum(ess_cost * E[i] for i in ess_candidates)
    m.setObjective(obj, GRB.MINIMIZE)

    for i in pv_buses:
        for t in hours:
            m.addConstr(P_pv_used[i, t] + P_curt[i, t] == pv_avail.get((i, t), 0.0), name=f"pv_split_{i}_{t}")

    for t in hours:
        m.addConstr(V2[slack, t] == 1.0, name=f"slack_v_{t}")

    for _, r in line_df.iterrows():
        e = int(r["Line"])
        u = int(r["From"])
        v = int(r["To"])
        R = float(r["R_pu"])
        P_lim = float(r["P_limit_kW"])
        for t in hours:
            m.addConstr(V2[v, t] == V2[u, t] - 2.0 * R * (P_line[e, t] / sbase_kw), name=f"vdrop_{e}_{t}")
            m.addConstr(P_line[e, t] <= P_lim, name=f"line_up_{e}_{t}")
            m.addConstr(P_line[e, t] >= -P_lim, name=f"line_lo_{e}_{t}")

    if has_ess:
        m.addConstr(quicksum(y[i] for i in ess_candidates) <= max_locations, name="max_ess_locations")
        for i in ess_candidates:
            m.addConstr(E[i] <= e_max * y[i], name=f"E_up_{i}")
            m.addConstr(E[i] >= e_min * y[i], name=f"E_lo_{i}")
            m.addConstr(Pcap[i] <= p_max * y[i], name=f"Pcap_up_{i}")
            m.addConstr(Pcap[i] >= p_min * y[i], name=f"Pcap_lo_{i}")
            for t in hours:
                m.addConstr(P_ch[i, t] <= Pcap[i] * u_ch[i, t], name=f"Pch_up_{i}_{t}")
                m.addConstr(P_dis[i, t] <= Pcap[i] * u_dis[i, t], name=f"Pdis_up_{i}_{t}")
                m.addConstr(u_ch[i, t] + u_dis[i, t] <= y[i], name=f"no_simul_{i}_{t}")
                m.addConstr(SOC[i, t] >= soc_min_frac * E[i], name=f"soc_min_{i}_{t}")
                m.addConstr(SOC[i, t] <= soc_max_frac * E[i], name=f"soc_max_{i}_{t}")
            for t in hours:
                if t == 0:
                    m.addConstr(SOC[i, t] == soc0_frac * E[i] + eta_ch * P_ch[i, t] - (1.0 / eta_dis) * P_dis[i, t], name=f"soc_dyn_{i}_{t}")
                else:
                    m.addConstr(SOC[i, t] == SOC[i, t - 1] + eta_ch * P_ch[i, t] - (1.0 / eta_dis) * P_dis[i, t], name=f"soc_dyn_{i}_{t}")
            if bool(config["ess"].get("final_soc_equal_initial", True)):
                m.addConstr(SOC[i, hours[-1]] == soc0_frac * E[i], name=f"soc_final_{i}")

    for i in buses:
        for t in hours:
            inflow = quicksum(P_line[e, t] for e in edges_by_to.get(i, []))
            outflow = quicksum(P_line[e, t] for e in edges_by_from.get(i, []))
            grid_term = P_grid[t] if i == slack else 0.0
            pv_term = P_pv_used[i, t] if i in pv_buses else 0.0
            ch_term = P_ch[i, t] if (has_ess and i in ess_candidates) else 0.0
            dis_term = P_dis[i, t] if (has_ess and i in ess_candidates) else 0.0
            m.addConstr(inflow + grid_term + pv_term + dis_term == load.get((i, t), 0.0) + ch_term + outflow, name=f"balance_{i}_{t}")

    m.optimize()

    if m.status != GRB.OPTIMAL:
        m.write(str(output_dir / f"{case_name}_model.lp"))
        if m.status == GRB.INFEASIBLE:
            m.computeIIS()
            m.write(str(output_dir / f"{case_name}_iis.ilp"))
        raise RuntimeError(f"Gurobi did not find optimal solution for {case_name}. Status={m.status}")

    rows_grid = [{"Hour": t, "Grid_kW": P_grid[t].X} for t in hours]
    rows_voltage = [{"Bus": i, "Hour": t, "V_pu": V2[i, t].X ** 0.5} for i in buses for t in hours]
    rows_pv = [{"Bus": i, "Hour": t, "PV_available_kW": pv_avail.get((i, t), 0.0), "PV_used_kW": P_pv_used[i, t].X, "Curtailment_kW": P_curt[i, t].X} for i in pv_buses for t in hours]
    rows_line = [{"Line": int(r["Line"]), "From": int(r["From"]), "To": int(r["To"]), "Hour": t, "P_line_kW": P_line[int(r["Line"]), t].X, "P_limit_kW": float(r["P_limit_kW"]), "Loading_pct": abs(P_line[int(r["Line"]), t].X) / float(r["P_limit_kW"]) * 100.0} for _, r in line_df.iterrows() for t in hours]

    if has_ess:
        rows_ess = []
        for i in ess_candidates:
            if y[i].X > 0.5:
                for t in hours:
                    rows_ess.append({"Bus": i, "Hour": t, "E_kWh": E[i].X, "Pcap_kW": Pcap[i].X, "P_charge_kW": P_ch[i, t].X, "P_discharge_kW": P_dis[i, t].X, "SOC_kWh": SOC[i, t].X})
        ess_df = pd.DataFrame(rows_ess)
    else:
        ess_df = pd.DataFrame(columns=["Bus", "Hour", "E_kWh", "Pcap_kW", "P_charge_kW", "P_discharge_kW", "SOC_kWh"])

    result = {
        "case": case_name,
        "objective": float(m.ObjVal),
        "grid": pd.DataFrame(rows_grid),
        "voltage": pd.DataFrame(rows_voltage),
        "pv": pd.DataFrame(rows_pv),
        "line": pd.DataFrame(rows_line),
        "ess": ess_df,
    }
    for key, val in result.items():
        if isinstance(val, pd.DataFrame):
            val.to_csv(output_dir / f"{case_name}_{key}.csv", index=False)
    return result
