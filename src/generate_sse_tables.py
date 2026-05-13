import pandas as pd
from pathlib import Path

TABLE_DIR = Path("results/tables")
TABLE_DIR.mkdir(parents=True, exist_ok=True)

# =========================
# Load data
# =========================
sse_candidates = pd.read_csv("data/sse_candidates.csv")
ranked_sse = pd.read_csv("results/tables/ranked_sse_candidates.csv")
ess_scenarios = pd.read_csv("results/tables/ess_scenarios.csv")

# =========================
# Table 1: Kandidat SSE dan karakteristik material
# =========================
table1 = ranked_sse[
    [
        "material_id",
        "formula",
        "energy_above_hull",
        "band_gap",
        "ionic_conductivity_s_cm",
        "electrochemical_stability",
        "interface_stability",
        "maturity",
    ]
].copy()

table1 = table1.rename(columns={
    "material_id": "Materials Project ID",
    "formula": "Material",
    "energy_above_hull": "Energy Above Hull (eV/atom)",
    "band_gap": "Band Gap (eV)",
    "ionic_conductivity_s_cm": "Ionic Conductivity (S/cm)",
    "electrochemical_stability": "Electrochemical Stability Score",
    "interface_stability": "Interface Stability Score",
    "maturity": "Maturity Score",
})

table1.insert(0, "No", range(1, len(table1) + 1))

table1 = table1[
    [
        "No",
        "Material",
        "Materials Project ID",
        "Energy Above Hull (eV/atom)",
        "Band Gap (eV)",
        "Ionic Conductivity (S/cm)",
        "Electrochemical Stability Score",
        "Interface Stability Score",
        "Maturity Score",
    ]
]

table1.to_csv(TABLE_DIR / "table_1_sse_material_characteristics.csv", index=False)

# =========================
# Table 2: Hasil ranking SSE
# =========================
table2 = ranked_sse.copy()

table2.insert(0, "Rank", range(1, len(table2) + 1))

table2 = table2.rename(columns={
    "material_id": "Materials Project ID",
    "formula": "Material",
    "score_stability": "Stability Score",
    "score_band_gap": "Band Gap Score",
    "score_ionic": "Ionic Conductivity Score",
    "score_ec_stability": "Electrochemical Stability Score",
    "score_interface": "Interface Stability Score",
    "score_maturity": "Maturity Score",
    "weighted_score": "Weighted Score",
})

table2 = table2[
    [
        "Rank",
        "Material",
        "Materials Project ID",
        "Stability Score",
        "Band Gap Score",
        "Ionic Conductivity Score",
        "Electrochemical Stability Score",
        "Interface Stability Score",
        "Maturity Score",
        "Weighted Score",
    ]
]

table2.to_csv(TABLE_DIR / "table_2_sse_ranking_results.csv", index=False)

# =========================
# Table 3: Mapping SSE ke skenario ESS
# =========================
table3 = ess_scenarios.copy()

# Hapus baseline jika hanya ingin tabel skenario ESS
table3 = table3[table3["scenario"] != "baseline_no_ess"].copy()

table3 = table3.rename(columns={
    "scenario": "ESS Scenario",
    "basis": "Scenario Basis",
    "linked_material": "Linked SSE Material",
    "linked_material_id": "Materials Project ID",
    "sse_score": "SSE Weighted Score",
    "round_trip_eff": "Round-trip Efficiency",
    "soc_min": "SOC Min",
    "soc_max": "SOC Max",
    "power_energy_ratio": "Power-to-Energy Ratio",
    "cost_per_kwh": "Cost ($/kWh)",
})

table3 = table3[
    [
        "ESS Scenario",
        "Scenario Basis",
        "Linked SSE Material",
        "Materials Project ID",
        "SSE Weighted Score",
        "Round-trip Efficiency",
        "SOC Min",
        "SOC Max",
        "Power-to-Energy Ratio",
        "Cost ($/kWh)",
    ]
]

table3.to_csv(TABLE_DIR / "table_3_sse_to_ess_mapping.csv", index=False)

# =========================
# Print output
# =========================
pd.set_option("display.max_columns", None)

print("\n=== TABLE 1: SSE MATERIAL CHARACTERISTICS ===")
print(table1)

print("\n=== TABLE 2: SSE RANKING RESULTS ===")
print(table2)

print("\n=== TABLE 3: SSE TO ESS SCENARIO MAPPING ===")
print(table3)

print("\nTabel berhasil dibuat:")
print(TABLE_DIR / "table_1_sse_material_characteristics.csv")
print(TABLE_DIR / "table_2_sse_ranking_results.csv")
print(TABLE_DIR / "table_3_sse_to_ess_mapping.csv")