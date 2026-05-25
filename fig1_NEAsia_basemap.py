#!/usr/bin/env python3
"""Fig 1 for the MG manuscript (Section 5.4) — tectonic basemap of NE Asia
showing the Cretaceous basins Songliao, Hailar, and Erlian in their
post-collisional / back-arc tectonic context.

Tectonic elements:
  - Cratons:  Siberian Craton (north, only southern margin shown);
              North China Craton (south).
  - Orogens:  Central Asian Orogenic Belt (CAOB) between cratons.
  - Sutures:  Mongol-Okhotsk suture (Late Jurassic-Early Cretaceous closure);
              Solonker suture (Permian, northern NCC margin) for context.
  - Major fault: Tanlu Fault Zone (sinistral strike-slip, Cretaceous-active).
  - Plate motion: Palaeo-Pacific subduction NW-ward under the eastern margin.

Outputs PDF + PNG + SVG via save_three_formats(), plus an EPS for MG.

History:
  - v1 (2026-05-11): first cut for QN2025106 MG submission.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Polygon as MplPolygon
import numpy as np

SKILL_SCRIPTS = Path.home() / ".claude" / "skills" / "geo-figures" / "scripts"
sys.path.insert(0, str(SKILL_SCRIPTS))
from geo_primitives import (        # noqa: E402
    apply_journal_rcparams, geographic_aspect, chaikin_smooth,
    add_polygon_collection, label_polygons, polygon_centroid,
    plot_fault, draw_scale_bar, draw_north_arrow,
    plate_motion_arrow, case_study_star, save_three_formats,
    OKABE_ITO, BASIN_FAMILY_PALETTE,
)


# ── 1. Map extent ───────────────────────────────────────────────────────────
LON_MIN, LON_MAX = 105.0, 135.0
LAT_MIN, LAT_MAX = 38.0, 55.0
MID_LAT = (LAT_MIN + LAT_MAX) / 2  # 46.5

# ── 2. Coastline (E Asia / Sea of Japan eastern margin) ─────────────────────
# Hand-digitised, schematic; runs as a closed polygon for "land" fill.
# Going clockwise starting at SW corner of land mass.
COASTLINE = [
    (LON_MIN, LAT_MIN),                  # SW corner of frame
    (LON_MIN, LAT_MAX),                  # NW corner
    (130.0, LAT_MAX),                    # follow north margin
    (132.0, 53.0),                       # NE land margin start (entering Russian Far East)
    (135.0, 51.0),
    (135.0, 47.0),                       # eastern margin (off-frame ocean to E)
    (132.0, 44.0),
    (130.5, 42.5),                       # Sea of Japan W margin
    (129.5, 41.0),                       # NE Korea
    (130.0, 38.5),                       # E Korea coast (off SE corner)
    (130.0, LAT_MIN),                    # to SE corner of frame
    (124.0, LAT_MIN),                    # bottom margin of frame, follow back
    (122.5, 39.0),                       # Bohai bay W corner
    (121.0, 38.5),                       # W coast of Bohai
    (LON_MIN, LAT_MIN),                  # close at SW corner
]

# ── 3. Basin polygons — all three are wide-rift / post-collisional family ───
BASINS_WIDE_RIFT = {
    "Songliao": [
        (122.7, 42.0), (123.5, 42.5), (124.5, 43.5), (125.5, 44.5),
        (126.5, 45.5), (127.3, 46.5), (127.5, 47.5), (127.0, 48.7),
        (125.7, 49.2), (124.5, 48.5), (123.7, 47.5), (123.2, 46.5),
        (122.7, 45.5), (122.3, 44.0), (122.5, 43.0),
    ],
    "Hailar": [
        (117.0, 48.5), (117.5, 49.3), (118.3, 50.0), (119.5, 50.5),
        (120.7, 50.5), (121.7, 50.0), (122.0, 49.3), (121.7, 48.7),
        (120.5, 48.3), (118.7, 48.3), (117.5, 48.4),
    ],
    "Erlian": [
        (109.5, 43.2), (110.5, 43.5), (111.7, 43.7), (113.0, 43.7),
        (114.5, 43.8), (116.0, 44.2), (117.2, 44.7), (117.0, 45.4),
        (116.0, 45.2), (114.5, 44.7), (113.0, 44.5), (111.7, 44.3),
        (110.3, 43.8),
    ],
}

# ── 4. Faults ───────────────────────────────────────────────────────────────
FAULTS = {
    # Tanlu Fault Zone — sinistral strike-slip, Cretaceous-active
    "Tanlu": [
        (122.0, 38.5), (123.0, 40.0), (124.0, 41.5), (125.5, 43.5),
        (127.5, 45.5), (129.5, 47.5), (131.0, 50.0), (132.0, 52.5),
    ],
    # Mongol-Okhotsk Suture — closed Late Jurassic / Early Cretaceous
    "MOS": [
        (LON_MIN, 51.0), (109.0, 51.5), (113.0, 52.5), (118.0, 53.0),
        (123.0, 53.0), (128.0, 52.5), (132.0, 52.0),
    ],
    # Solonker Suture (Permian) — northern margin of NCC
    "Solonker": [
        (LON_MIN, 42.5), (108.0, 42.5), (112.0, 42.7), (115.0, 42.7),
        (118.0, 42.5), (121.0, 42.5), (123.5, 42.0),
    ],
}
FAULT_KINEMATIC = {
    "Tanlu":    "sinistral",
    "MOS":      "thrust",        # suture, with thrust polarity
    "Solonker": "thrust",
}
FAULT_CERTAINTY = {
    "Tanlu":    "certain",
    "MOS":      "approximate",
    "Solonker": "approximate",
}

# ── 5. Case-study basins (red star overlay) ─────────────────────────────────
CASE_STUDY_BASINS = ["Songliao", "Hailar", "Erlian"]

# ── 6. Regional labels ──────────────────────────────────────────────────────
# Positions chosen to avoid overlap; "CAOB" abbreviated, spelled out in caption.
REGION_LABELS = [
    (115.0, 54.2, "Siberian Craton",       9),
    (113.0, 47.6, "CAOB",                  9),
    (115.0, 39.6, "North China Craton",    9),
]

# Fault / suture labels (placed manually along trace)
FAULT_LABELS = [
    (124.0, 39.5, "Tanlu Fault Zone",            "Tanlu",    "italic"),
    (115.0, 53.5, "Mongol-Okhotsk Suture",       "MOS",      "italic"),
    (110.5, 41.7, "Solonker Suture",             "Solonker", "italic"),
]


def build_figure() -> plt.Figure:
    apply_journal_rcparams("GJ")
    # Override font.sans-serif chain to put Arial first per MG spec.
    plt.rcParams["font.sans-serif"] = [
        "Arial", "Helvetica", "DejaVu Sans", "Liberation Sans",
    ]
    # svg.fonttype='none' → text stays as editable <text> SVG elements for
    # Illustrator handoff (校级课题 phase_n technique). Override whatever
    # apply_journal_rcparams set for SVG so the .svg below opens as
    # editable text in Illustrator.
    plt.rcParams["svg.fonttype"] = "none"

    # Landscape canvas. Map on left ~70%, legend on right ~28%.
    fig = plt.figure(figsize=(6.85, 4.8))
    ax = fig.add_axes([0.055, 0.075, 0.66, 0.90])
    legend_ax = fig.add_axes([0.735, 0.075, 0.255, 0.90])

    # Map frame
    ax.set_xlim(LON_MIN, LON_MAX)
    ax.set_ylim(LAT_MIN, LAT_MAX)
    ax.set_aspect(geographic_aspect(MID_LAT))
    ax.set_facecolor(BASIN_FAMILY_PALETTE["ocean"])

    # Land
    ax.add_patch(MplPolygon(
        chaikin_smooth(COASTLINE, iterations=4, closed=True),
        closed=True,
        facecolor=BASIN_FAMILY_PALETTE["land"],
        edgecolor="#888888", lw=0.6, zorder=1,
    ))

    # Basins
    add_polygon_collection(
        ax, BASINS_WIDE_RIFT,
        facecolor=BASIN_FAMILY_PALETTE["wide_rift"],
        edgecolor="#5E3F87", lw=0.6, zorder=4, alpha=1.0,
    )
    label_polygons(
        ax, BASINS_WIDE_RIFT,
        color="#1A1A1A", fontsize=8, weight="bold",
    )

    # Faults
    for name, xy in FAULTS.items():
        plot_fault(
            ax, xy,
            color=BASIN_FAMILY_PALETTE["fault"], lw=1.6,
            certainty=FAULT_CERTAINTY[name],
            kinematic=FAULT_KINEMATIC[name],
            zorder=7,
        )

    # Plate-motion arrow: Palaeo-Pacific subduction NW-ward
    plate_motion_arrow(ax, start=(133.5, 41.5), end=(130.0, 44.0))
    ax.text(134.5, 40.0, "Palaeo-Pacific\nsubduction",
            fontsize=7.5, ha="right", va="top", style="italic",
            color="#2B4F8F", zorder=10,
            bbox=dict(facecolor="white", edgecolor="none", pad=1.0))

    # Case-study stars on basin centroids
    for name, verts in BASINS_WIDE_RIFT.items():
        if name in CASE_STUDY_BASINS:
            cx, cy = polygon_centroid(verts)
            case_study_star(ax, cx, cy, size=140, lw=0.6)

    # Regional labels (opaque white bbox for EPS compatibility)
    for lon, lat, txt, fsize in REGION_LABELS:
        ax.text(lon, lat, txt, fontsize=fsize, weight="bold",
                color="#333333", ha="center", va="center",
                zorder=10,
                bbox=dict(facecolor="white", edgecolor="none", pad=1.5))

    # Fault labels
    for lon, lat, txt, _, style in FAULT_LABELS:
        ax.text(lon, lat, txt, fontsize=7.5, style=style,
                color="#1A1A1A", ha="center", va="center",
                zorder=10,
                bbox=dict(facecolor="white", edgecolor="none", pad=1.2))

    # Graticule
    ax.set_xticks(np.arange(105, 136, 5))
    ax.set_yticks(np.arange(40, 56, 5))
    ax.set_xticklabels([f"{x}°E" for x in ax.get_xticks()], fontsize=7.5)
    ax.set_yticklabels([f"{y}°N" for y in ax.get_yticks()], fontsize=7.5)
    ax.grid(True, color="#BFBFBF", lw=0.3, ls=":", zorder=0)
    ax.set_xlabel("Longitude", fontsize=8)
    ax.set_ylabel("Latitude", fontsize=8)

    # FGDC marginalia
    draw_scale_bar(ax, anchor_x=106.5, anchor_y=39.0,
                   length_km=400, mid_lat=MID_LAT, fontsize=7)
    draw_north_arrow(ax, x=107.0, y=52.5, size=1.0, fontsize=8)

    # ── Side legend ──
    legend_ax.axis("off")
    legend_ax.set_xlim(0, 1)
    legend_ax.set_ylim(0, 1)
    y = 0.93

    def L(s, **kw):
        nonlocal y
        legend_ax.text(0.02, y, s, va="top", ha="left", **kw)
        y -= 0.045

    def patch_row(label, color, edge, alpha=1.0):
        nonlocal y
        rect = Rectangle((0.02, y - 0.035), 0.10, 0.035,
                         facecolor=color, edgecolor=edge,
                         lw=0.6, alpha=alpha,
                         transform=legend_ax.transAxes, clip_on=False)
        legend_ax.add_patch(rect)
        legend_ax.text(0.16, y - 0.018, label, fontsize=7.8,
                       va="center", ha="left")
        y -= 0.055

    def line_row(label, ls, kinematic_text=""):
        nonlocal y
        legend_ax.plot([0.02, 0.13], [y - 0.018, y - 0.018],
                       color="#1A1A1A", lw=1.4, ls=ls, solid_capstyle="round",
                       transform=legend_ax.transAxes, clip_on=False)
        legend_ax.text(0.16, y - 0.018, label + kinematic_text, fontsize=7.5,
                       va="center", ha="left")
        y -= 0.055

    L("Legend", fontsize=10, weight="bold")
    y -= 0.012

    L("Cretaceous basins", fontsize=8.5, weight="bold")
    patch_row("Wide-rift / back-arc",
              BASIN_FAMILY_PALETTE["wide_rift"], "#5E3F87")
    legend_ax.scatter([0.07], [y - 0.01], marker="*", s=110,
                      facecolor="#B32020", edgecolor="#400000", lw=0.6,
                      transform=legend_ax.transAxes, clip_on=False)
    legend_ax.text(0.16, y - 0.01, "Case-study basin", fontsize=7.5,
                   va="center", ha="left")
    y -= 0.06

    L("Faults / sutures", fontsize=8.5, weight="bold")
    line_row("Certain (solid)", "-")
    line_row("Approximate (long-dash)", (0, (6, 3)))

    L("Kinematic indicator", fontsize=8.5, weight="bold")
    legend_ax.text(0.05, y - 0.02,
                   "→  ←   sinistral\n▲       thrust / suture",
                   fontsize=7.5, va="top", ha="left", linespacing=1.6)
    y -= 0.10

    L("Plate motion", fontsize=8.5, weight="bold")
    legend_ax.annotate("",
                       xy=(0.13, y - 0.018), xytext=(0.02, y - 0.018),
                       xycoords=legend_ax.transAxes,
                       arrowprops=dict(arrowstyle="-|>",
                                       color="#2B4F8F", lw=2.2,
                                       mutation_scale=14))
    legend_ax.text(0.16, y - 0.018, "Palaeo-Pacific\nplate vector",
                   fontsize=7.5, va="center", ha="left", linespacing=1.2)
    y -= 0.075

    L("Tectonic units", fontsize=8.5, weight="bold")
    patch_row("Land (continental)",
              BASIN_FAMILY_PALETTE["land"], "#888888")
    patch_row("Ocean / sea",
              BASIN_FAMILY_PALETTE["ocean"], "#888888")

    # Bottom note
    legend_ax.text(0.02, 0.02,
                   "FGDC TM 11A02 line styles\nOkabe-Ito categorical palette",
                   fontsize=7.0, color="#666666",
                   va="bottom", ha="left", style="italic",
                   linespacing=1.4)

    return fig


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--output-dir", default="figures")
    ap.add_argument("--stem", default="Fig1_NEAsia_basemap")
    ap.add_argument("--audit", action="store_true")
    args = ap.parse_args()

    fig = build_figure()

    if args.audit:
        from layout_check import audit_figure
        issues = audit_figure(fig, journal="GJ")
        if issues:
            for i in issues:
                print("!! ", i)
            print(f"-- {len(issues)} layout issue(s)")

    written = save_three_formats(fig, args.output_dir, args.stem)
    # Also save EPS for MG submission (Springer canonical for line art).
    eps_path = Path(args.output_dir) / f"{args.stem}.eps"
    fig.savefig(eps_path, format="eps", bbox_inches="tight", facecolor="white")
    written.append(eps_path)
    # SVG with editable text for Illustrator handoff.
    svg_path = Path(args.output_dir) / f"{args.stem}.svg"
    fig.savefig(svg_path, format="svg", bbox_inches="tight", facecolor="white")
    written.append(svg_path)

    for p in written:
        print(f"wrote {p}")
    plt.close(fig)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
