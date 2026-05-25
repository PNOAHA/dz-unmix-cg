# -*- coding: utf-8 -*-
"""
fig_paper_cg_figures_en.py — English-labelled figures for the C&G manuscript
============================================================================

Generates the English-labelled counterparts of Fig_R1/R2/R3 (which were
originally rendered with Chinese labels for the Chinese 实验报告 docx).
For the C&G submission, all figure text must be in English.

Output (to figures/):
  Fig5_sources_en.png        — three source endmember KDEs (§6 Case Study)
  Fig6_sensitivity_en.png    — α × bandwidth sensitivity heatmap (§5)
  Fig7_alpha_effect_en.png   — Dirichlet α effect bar chart (§5)

Conventions vs Chinese version (fig_experiment_report.py):
  - All labels, legends, axis titles translated to English
  - Embedded plot titles REMOVED (caption goes in build_cg_manuscript.js,
    so duplicating the title in the figure itself is non-standard for
    journal submission)
  - Serif font (DejaVu Serif fallback to Times) matches manuscript body
  - Both .png (200 dpi for embedding) and .svg (vector, for Illustrator
    handoff if needed) are emitted

Run: & "C:/Users/Administrator/miniconda3/python.exe" fig_paper_cg_figures_en.py

Chinese versions (Fig_R1_sources.png etc.) are preserved unchanged for the
Chinese 实验报告 docx.
"""

import csv
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import rcParams

from dz_unmixing_experiment import DEFAULT_SOURCES, T_GRID, build_source_endmembers

# Serif font (no CJK), matching the manuscript Times New Roman body
rcParams['font.family'] = 'serif'
rcParams['font.serif'] = ['DejaVu Serif', 'Liberation Serif', 'Times New Roman']
rcParams['axes.unicode_minus'] = False
rcParams['svg.fonttype'] = 'none'   # editable SVG text for Illustrator handoff
rcParams['mathtext.fontset'] = 'cm'  # Computer Modern for math (μ, σ, α)


# ----------------------------------------------------------------------------
# Fig 5 — Three source endmembers (KDE)
# ----------------------------------------------------------------------------

def fig_sources_en():
    H = build_source_endmembers()
    fig, ax = plt.subplots(figsize=(7.2, 3.6), dpi=300)
    colors = ['#D62728', '#1F77B4', '#2CA02C']
    labels = [r'S1  Mesozoic arc magmatism ($\mu = 130$ Ma, $\sigma = 15$ Ma)',
              r'S2  Palaeozoic CAOB basement ($\mu = 280$ Ma, $\sigma = 30$ Ma)',
              r'S3  Archaean–Proterozoic NCC ($\mu = 1900$ Ma, $\sigma = 100$ Ma)']
    for h, c, lbl in zip(H, colors, labels):
        ax.plot(T_GRID, h, color=c, lw=2.2, label=lbl)
        ax.fill_between(T_GRID, 0, h, color=c, alpha=0.18)
    ax.set_xlabel('U–Pb age (Ma)', fontsize=11)
    ax.set_ylabel('Normalized density (1/Ma)', fontsize=11)
    # Title intentionally omitted — caption supplied by build_cg_manuscript.js
    ax.set_xlim(50, 2500)
    ax.set_ylim(bottom=0)
    ax.legend(loc='upper right', fontsize=9, framealpha=0.92)
    ax.grid(alpha=0.3)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    fig.tight_layout()
    fig.savefig('figures/Fig5_sources_en.png', dpi=600, bbox_inches='tight')
    fig.savefig('figures/Fig5_sources_en.svg', bbox_inches='tight')
    plt.close(fig)
    print("Wrote Fig5_sources_en.png + .svg")


# ----------------------------------------------------------------------------
# Fig 6 — Sensitivity heatmap (α × bandwidth)
# ----------------------------------------------------------------------------

def fig_sensitivity_en():
    with open('sensitivity_results.csv', 'r', encoding='utf-8') as f:
        rows = list(csv.DictReader(f))

    alphas = sorted({float(r['alpha']) for r in rows})
    bws = sorted({float(r['bandwidth']) for r in rows})

    grid = np.zeros((len(alphas), len(bws)))
    for r in rows:
        i = alphas.index(float(r['alpha']))
        j = bws.index(float(r['bandwidth']))
        grid[i, j] += float(r['top1_dom_mean'])
    grid /= 5.0   # 5 seeds per (α, bw) cell

    fig, ax = plt.subplots(figsize=(6.8, 3.4), dpi=300)
    im = ax.imshow(grid, cmap='RdYlGn', vmin=0.85, vmax=1.0, aspect='auto')
    ax.set_xticks(range(len(bws)))
    ax.set_xticklabels([f'{b:.0f}' for b in bws])
    ax.set_yticks(range(len(alphas)))
    ax.set_yticklabels([rf'$\alpha$ = {a:.1f}' for a in alphas])
    ax.set_xlabel('KDE bandwidth (Ma)', fontsize=11)
    # Title intentionally omitted — caption supplied by build_cg_manuscript.js

    for i in range(len(alphas)):
        for j in range(len(bws)):
            v = grid[i, j]
            color = 'white' if v < 0.90 else 'black'
            ax.text(j, i, f'{v:.4f}', ha='center', va='center',
                    color=color, fontsize=10)

    cbar = fig.colorbar(im, ax=ax, shrink=0.85)
    cbar.set_label('Top-1 (dominant) accuracy', fontsize=9)
    cbar.ax.axhline(0.85, color='red', lw=1.5, linestyle='--')

    fig.tight_layout()
    fig.savefig('figures/Fig6_sensitivity_en.png', dpi=600, bbox_inches='tight')
    fig.savefig('figures/Fig6_sensitivity_en.svg', bbox_inches='tight')
    plt.close(fig)
    print("Wrote Fig6_sensitivity_en.png + .svg")


# ----------------------------------------------------------------------------
# Fig 7 — Top-1 vs Dirichlet α (bar chart with error bars)
# ----------------------------------------------------------------------------

def fig_alpha_effect_en():
    with open('sensitivity_results.csv', 'r', encoding='utf-8') as f:
        rows = list(csv.DictReader(f))
    alphas = sorted({float(r['alpha']) for r in rows})
    data_by_alpha = {a: [float(r['top1_dom_mean']) for r in rows if float(r['alpha']) == a] for a in alphas}

    fig, ax = plt.subplots(figsize=(5.2, 3.2), dpi=300)
    positions = np.arange(len(alphas))
    means = [np.mean(data_by_alpha[a]) for a in alphas]
    stds = [np.std(data_by_alpha[a]) for a in alphas]
    ax.bar(positions, means, yerr=stds, capsize=6,
           color=['#A0C4E2', '#5A9BD4', '#2E5A88'], alpha=0.92,
           edgecolor='black', lw=0.8)
    ax.axhline(0.85, color='red', lw=1.4, linestyle='--', label='Threshold 0.85')
    ax.set_xticks(positions)
    ax.set_xticklabels([rf'$\alpha$ = {a:.1f}' for a in alphas])
    ax.set_ylabel('Top-1 (dominant) accuracy', fontsize=11)
    ax.set_ylim(0.80, 1.01)
    # Title intentionally omitted — caption supplied by build_cg_manuscript.js
    ax.legend(loc='lower right', fontsize=9)
    ax.grid(axis='y', alpha=0.3)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    for x, m in zip(positions, means):
        ax.text(x, m + 0.012, f'{m:.4f}', ha='center', fontsize=9)
    fig.tight_layout()
    fig.savefig('figures/Fig7_alpha_effect_en.png', dpi=600, bbox_inches='tight')
    fig.savefig('figures/Fig7_alpha_effect_en.svg', bbox_inches='tight')
    plt.close(fig)
    print("Wrote Fig7_alpha_effect_en.png + .svg")


if __name__ == "__main__":
    fig_sources_en()
    fig_sensitivity_en()
    fig_alpha_effect_en()
    print("\nAll three English figures ready (Fig5/6/7).")
