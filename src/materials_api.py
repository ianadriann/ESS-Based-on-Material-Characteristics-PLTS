"""
Optional Materials Project downloader.

Usage:
1. pip install mp-api
2. export MP_API_KEY="your_key"
3. python -m src.materials_api
"""

from pathlib import Path
import os
import pandas as pd


def download_materials_project_candidates(
    api_key: str,
    output_path: str | Path = "data/mp_candidates.csv",
    elements: list[str] | None = None,
    max_energy_above_hull: float = 0.05,
    min_band_gap: float = 2.0,
) -> pd.DataFrame:
    try:
        from mp_api.client import MPRester
    except ImportError as exc:
        raise ImportError("Install mp-api first: pip install mp-api") from exc

    elements = elements or ["Li"]
    with MPRester(api_key) as mpr:
        docs = mpr.materials.summary.search(
            elements=elements,
            energy_above_hull=(0, max_energy_above_hull),
            band_gap=(min_band_gap, None),
            fields=[
                "material_id",
                "formula_pretty",
                "energy_above_hull",
                "band_gap",
                "formation_energy_per_atom",
                "is_stable",
                "elements",
            ],
        )

    rows = []
    for d in docs:
        rows.append({
            "material_id": str(d.material_id),
            "formula": d.formula_pretty,
            "energy_above_hull": d.energy_above_hull,
            "band_gap": d.band_gap,
            "formation_energy_per_atom": d.formation_energy_per_atom,
            "is_stable": d.is_stable,
            "elements": ",".join([str(e) for e in d.elements]),
        })

    df = pd.DataFrame(rows)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    return df


if __name__ == "__main__":
    key = os.getenv("MP_API_KEY")
    if not key:
        raise SystemExit("Please set MP_API_KEY environment variable.")
    df = download_materials_project_candidates(key)
    print(df.head())
