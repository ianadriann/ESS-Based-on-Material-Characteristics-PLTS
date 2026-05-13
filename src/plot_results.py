from pathlib import Path
import matplotlib.pyplot as plt


def plot_voltage_profile(result: dict, out_dir: str | Path = "results/figures") -> None:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    df = result["voltage"]
    vmin_by_bus = df.groupby("Bus")["V_pu"].min()
    vmax_by_bus = df.groupby("Bus")["V_pu"].max()

    plt.figure(figsize=(9, 4))
    plt.plot(vmin_by_bus.index, vmin_by_bus.values, marker="o", label="Minimum voltage")
    plt.plot(vmax_by_bus.index, vmax_by_bus.values, marker="o", label="Maximum voltage")
    plt.axhline(0.95, linestyle="--", linewidth=1)
    plt.axhline(1.05, linestyle="--", linewidth=1)
    plt.xlabel("Bus")
    plt.ylabel("Voltage (p.u.)")
    plt.title(f"Voltage envelope - {result['case']}")
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_dir / f"{result['case']}_voltage.png", dpi=150)
    plt.close()


def plot_ess_soc(result: dict, out_dir: str | Path = "results/figures") -> None:
    if result["ess"].empty:
        return
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    df = result["ess"]

    plt.figure(figsize=(9, 4))
    for bus, g in df.groupby("Bus"):
        plt.plot(g["Hour"], g["SOC_kWh"], marker="o", label=f"Bus {bus}")
    plt.xlabel("Hour")
    plt.ylabel("SOC (kWh)")
    plt.title(f"ESS SOC - {result['case']}")
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_dir / f"{result['case']}_soc.png", dpi=150)
    plt.close()
