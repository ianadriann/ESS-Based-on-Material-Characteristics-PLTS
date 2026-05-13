from pathlib import Path
from typing import Any, Dict
import yaml
import pandas as pd


def load_config(path: str | Path = "config.yaml") -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_network_data(data_dir: str | Path = "data") -> Dict[str, pd.DataFrame]:
    data_dir = Path(data_dir)
    return {
        "bus": pd.read_csv(data_dir / "ieee33_bus.csv"),
        "line": pd.read_csv(data_dir / "ieee33_line.csv"),
        "load_profile": pd.read_csv(data_dir / "load_profile_24h.csv"),
        "irradiance": pd.read_csv(data_dir / "nasa_irradiance.csv"),
    }


def load_sse_candidates(data_dir: str | Path = "data") -> pd.DataFrame:
    return pd.read_csv(Path(data_dir) / "sse_candidates.csv")
