"""Campaign figures for the manuscript: five-TSA surface grid + threshold overlay.

Figure 1 (``five_tsa_surfaces.pdf``): for each management unit, a row of four panels -
the 3D surface of emission-minimizing utilized harvest volume over the
(half-life, displacement factor) plane plus the three orthographic views, matching the
legacy figure style.

Figure 2 (``tsa_overlay.pdf``): the per-unit flip thresholds (df50 vs half-life, from
``results/cross-tsa/cross_tsa_thresholds.csv``) against the literature ranges
documented in the manuscript repository's ``planning/literature_overlay.md``:
displacement-factor bands (Leskinen et al. 2018: mean 1.2, 95% -0.7 to 5.1;
Sathre & O'Connor 2010 middle estimates 0.4 to 6.0; Canadian LCA weighted 0.45 to 2.2)
and the IPCC half-life defaults (paper 2, panels 25, sawnwood 35 years).

Usage:
    python scripts/tsa_campaign_figures.py [--out-dir results/cross-tsa/figures]
"""

from __future__ import annotations

import argparse
import os

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt

TSAS = [("femic-tsa08", "TSA 08"), ("femic-tsa16", "TSA 16"), ("femic-tsa24", "TSA 24"),
        ("femic-tsa40", "TSA 40"), ("femic-tsa41", "TSA 41")]
COLS = ["3D surface", "Top view (half-life vs displacement)",
        "Side view (half-life vs volume)", "Front view (displacement vs volume)"]


def load_surface(label: str):
    df = pd.read_csv(f"results/{label}/tradeoff_grid/tradeoff_grid_summary.csv")
    half_lives = np.sort(df["half_life"].unique())
    displacements = np.sort(df["displacement_factor"].unique())
    z = (df.pivot(index="displacement_factor", columns="half_life",
                  values="total_harvested_volume_m3")
         .reindex(index=displacements, columns=half_lives).to_numpy())
    x, y = np.meshgrid(half_lives, displacements)
    return x, y, z


def main(out_dir: str) -> None:
    os.makedirs(out_dir, exist_ok=True)

    # --- Figure 1: five rows x four panels ---
    fig = plt.figure(figsize=(16.5, 19.5))
    gs = fig.add_gridspec(len(TSAS), 4, hspace=0.42, wspace=0.30)
    for r, (label, name) in enumerate(TSAS):
        x, y, z = load_surface(label)
        # 3D
        ax = fig.add_subplot(gs[r, 0], projection="3d")
        ax.plot_surface(x, y, z, cmap="viridis", edgecolor="none")
        ax.set_ylim(0, 2.4)
        ax.set_zlim(0, 1.6e9)
        ax.set_zticks(np.arange(0, 1.61e9, 0.4e9))
        ax.tick_params(labelsize=6.5)
        ax.view_init(elev=30, azim=-60)
        if r == 0:
            ax.set_title(COLS[0], fontsize=9)
        ax.set_ylabel("df (tC/tC)", fontsize=7, labelpad=-2)
        ax.set_xlabel("half-life (yr)", fontsize=7, labelpad=-2)
        ax.set_zlabel("volume (m$^3$)", fontsize=7, labelpad=-2)
        # orthographic views (same construction as the legacy figure)
        for c, (a, b, zz, xl, yl) in enumerate([
                (x, y, z, "half-life (yr)", "df (tC/tC)"),
                (x, z, y, "half-life (yr)", "volume (m$^3$)"),
                (y, z, x, "df (tC/tC)", "volume (m$^3$)")], start=1):
            axo = fig.add_subplot(gs[r, c])
            axo.contourf(a, b, zz, cmap="viridis", levels=24)
            axo.set_xlabel(xl, fontsize=7)
            axo.set_ylabel(yl, fontsize=7)
            axo.tick_params(labelsize=6.5)
            if r == 0:
                axo.set_title(COLS[c], fontsize=9)
        if r == 0:
            pass
        fig.text(0.005, 1 - (r + 0.5) / len(TSAS) * 0.96, name, rotation=90,
                 va="center", fontsize=11, fontweight="bold")
    fig.suptitle("Emission-minimizing utilized harvest volume over the HWP parameter "
                 "plane (25 displacement factors x 200 solid-wood half-lives per unit)",
                 fontsize=12, y=0.995)
    fig.savefig(os.path.join(out_dir, "five_tsa_surfaces.pdf"), bbox_inches="tight")
    plt.close(fig)
    print("wrote five_tsa_surfaces.pdf", flush=True)

    # --- Figure 2: threshold overlay ---
    thr = pd.read_csv("results/cross-tsa/cross_tsa_thresholds.csv")
    fig, ax = plt.subplots(figsize=(7.4, 4.8))
    ax.axhspan(-0.7, 5.1, color="0.85", alpha=0.45, zorder=0,
               label="DF 95% range (Leskinen et al. 2018)")
    ax.axhspan(0.4, 6.0, color="0.75", alpha=0.4, zorder=0,
               label="DF middle estimates (Sathre & O'Connor 2010)")
    ax.axhspan(0.45, 2.2, color="0.6", alpha=0.35, zorder=0,
               label="Canadian LCA DFs (Smyth et al. 2014/2017)")
    for hl, txt in [(2, "paper"), (25, "panels"), (35, "sawnwood")]:
        ax.axvline(hl, color="black", ls=":", lw=0.9, zorder=1)
        ax.annotate(f"IPCC {txt}\n{hl} yr", (hl, 2.52), ha="center", va="bottom",
                    fontsize=6.5)
    for label, name in TSAS:
        t = thr[thr.label == label]
        ax.plot(t["half_life"], t["df50"], lw=1.8, label=name)
    ax.set_xlim(1, 200)
    ax.set_ylim(0, 2.4)
    ax.set_xlabel("Solid-wood half-life (yr)")
    ax.set_ylabel("Flip mid-threshold df50 (tC/tC)")
    h, labels = ax.get_legend_handles_labels()
    ax.legend(h, labels, fontsize=7, loc="upper right", ncol=2, framealpha=0.9)
    fig.savefig(os.path.join(out_dir, "tsa_overlay.pdf"), bbox_inches="tight")
    plt.close(fig)
    print("wrote tsa_overlay.pdf", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", default="results/cross-tsa/figures")
    args = parser.parse_args()
    main(args.out_dir)
