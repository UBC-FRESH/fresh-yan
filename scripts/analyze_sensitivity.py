#!/usr/bin/env python3
"""Build the sensitivity figures from the trade-off grid summary record.

Produces the 3D surface and orthographic views of total harvested volume over the
(half-life, displacement factor) plane, mirroring the legacy ``sensitivity_analysis.ipynb``
figures (``3d.pdf`` / ``xyz.pdf`` in the manuscript).

Usage:
    python scripts/analyze_sensitivity.py [--summary <summary.csv>]
"""

from __future__ import annotations

import argparse
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def load_grid(summary_path: str):
    """Load the summary record into meshgrid-ready arrays."""
    df = pd.read_csv(summary_path)
    half_lives = np.sort(df["half_life"].unique())
    displacements = np.sort(df["displacement_factor"].unique())
    z = (df.pivot(index="displacement_factor", columns="half_life",
                  values="total_harvested_volume_m3")
         .reindex(index=displacements, columns=half_lives)
         .to_numpy())
    x, y = np.meshgrid(half_lives, displacements)
    return x, y, z


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--summary", default="results/tradeoff_grid/tradeoff_grid_summary.csv")
    parser.add_argument("--out-dir", default="results/tradeoff_grid/figures")
    args = parser.parse_args()

    x, y, z = load_grid(args.summary)
    os.makedirs(args.out_dir, exist_ok=True)

    # 3D surface
    fig = plt.figure(figsize=(12, 10))
    ax = fig.add_subplot(111, projection="3d")
    surf = ax.plot_surface(x, y, z, cmap="viridis", edgecolor="none")
    ax.set_zlim(0, 1.6e9)
    ax.set_zticks(np.arange(0, 1.61e9, 0.2e9))
    ax.set_xlabel("Half-life (years)")
    ax.set_ylabel("Displacement factor (tC/tC)")
    ax.set_zlabel("Total harvested volume (m³)")
    ax.set_yticks(np.arange(0, 2.5, 0.2))
    ax.view_init(elev=30, azim=-60)
    fig.colorbar(surf, shrink=0.5, aspect=5)
    fig.savefig(os.path.join(args.out_dir, "3d.pdf"), bbox_inches="tight")
    plt.close(fig)

    # Orthographic views
    fig, axes = plt.subplots(1, 3, figsize=(20, 6))
    xy = axes[0].contourf(x, y, z, cmap="viridis")
    axes[0].set_title("XY-plane (Top View)")
    axes[0].set_xlabel("Half-life (years)")
    axes[0].set_ylabel("Displacement factor (tC/tC)")
    axes[0].set_yticks(np.arange(0, 2.5, 0.2))
    fig.colorbar(xy, ax=axes[0]).set_label("Total harvested volume (m³)")

    xz = axes[1].contourf(x, z, y, cmap="viridis")
    axes[1].set_title("XZ-plane (Side View)")
    axes[1].set_xlabel("Half-life (years)")
    axes[1].set_ylabel("Total harvested volume (m³)")
    fig.colorbar(xz, ax=axes[1]).set_label("Displacement factor (tC/tC)")

    yz = axes[2].contourf(y, z, x, cmap="viridis")
    axes[2].set_title("YZ-plane (Front View)")
    axes[2].set_xlabel("Displacement factor (tC/tC)")
    axes[2].set_ylabel("Total harvested volume (m³)")
    axes[2].set_xticks(np.arange(0, 2.5, 0.2))
    fig.colorbar(yz, ax=axes[2]).set_label("Half-life (years)")

    fig.savefig(os.path.join(args.out_dir, "xyz.pdf"), bbox_inches="tight")
    plt.close(fig)

    print(f"Wrote sensitivity figures to {args.out_dir}")


if __name__ == "__main__":
    main()
