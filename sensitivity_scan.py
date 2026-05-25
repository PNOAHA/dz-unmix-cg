# -*- coding: utf-8 -*-
"""
QN2025106 指标 #3  敏感性扫描
=============================

固定主模型 (supervised NMF) + 主指标 (Top-1 dominant),
扫超参 (seed, dirichlet_alpha, bandwidth) 三维笛卡尔积,
看主指标对各超参的稳健性.

输出:
  - sensitivity_results.csv       (机器可读, 装文档表)
  - sensitivity_summary.md        (人读)
  - sensitivity_results.json      (结构化, 装结项材料)

跑法 (≈ 5–10 分钟):
  & "C:/Users/Administrator/miniconda3/python.exe" sensitivity_scan.py

作者: 潘路加 — 2026-05-12
"""

import csv
import json
import time
from itertools import product

import numpy as np
from sklearn.model_selection import KFold

from dz_unmixing_experiment import (
    DEFAULT_SOURCES, T_GRID,
    generate_dataset, kde_density,
    build_source_endmembers, supervised_unmix,
    report,
)

# ----------------------------------------------------------------------------
# 扫描格点
# ----------------------------------------------------------------------------

SEEDS      = [7, 13, 21, 42, 99]
ALPHAS     = [0.3, 0.5, 1.0]
BANDWIDTHS = [8.0, 10.0, 12.0, 15.0, 20.0]
N_SAMPLES  = 1000
N_FOLDS    = 5


def run_one(seed: int, alpha: float, bandwidth: float) -> dict:
    """单一 config 的 5 折 CV 平均 — 重生成数据, 重算 KDE."""
    ages_list, true_w = generate_dataset(
        n_samples=N_SAMPLES, dirichlet_alpha=alpha, seed=seed
    )
    X = np.array([kde_density(a, bandwidth=bandwidth) for a in ages_list])
    H = build_source_endmembers()

    kf = KFold(n_splits=N_FOLDS, shuffle=True, random_state=seed)
    top1_all, top1_dom, mae, r2 = [], [], [], []
    for tr_idx, te_idx in kf.split(X):
        pred = supervised_unmix(X[te_idx], H)
        r = report(true_w[te_idx], pred)
        top1_all.append(r["top1_accuracy"])
        top1_dom.append(r["top1_accuracy_dominant"])
        mae.append(r["weights_MAE"])
        r2.append(r["weights_R2"])
    return {
        "seed": seed, "alpha": alpha, "bandwidth": bandwidth,
        "top1_all_mean":  float(np.mean(top1_all)),
        "top1_all_std":   float(np.std(top1_all)),
        "top1_dom_mean":  float(np.mean(top1_dom)),
        "top1_dom_std":   float(np.std(top1_dom)),
        "mae_mean":       float(np.mean(mae)),
        "r2_mean":        float(np.mean(r2)),
        "threshold_met":  bool(np.mean(top1_dom) >= 0.85),
    }


# ----------------------------------------------------------------------------
# Run scan
# ----------------------------------------------------------------------------

def main() -> None:
    configs = list(product(SEEDS, ALPHAS, BANDWIDTHS))
    print(f"将跑 {len(configs)} 个 config × {N_FOLDS}-fold CV  ≈ {len(configs)*8/60:.1f} 分钟")
    print(f"  seeds = {SEEDS}")
    print(f"  alphas = {ALPHAS}")
    print(f"  bandwidths = {BANDWIDTHS} (Ma)")
    print(f"  model = Supervised NMF (主模型)")
    print()

    t0 = time.time()
    results = []
    for i, (seed, alpha, bw) in enumerate(configs, start=1):
        t_i = time.time()
        r = run_one(seed, alpha, bw)
        results.append(r)
        flag = "✓" if r["threshold_met"] else "✗"
        elapsed = time.time() - t_i
        print(f"  [{i:3d}/{len(configs)}] seed={seed:2d}  α={alpha:.1f}  bw={bw:5.1f}Ma  "
              f"→ Top1_dom={r['top1_dom_mean']:.4f} ± {r['top1_dom_std']:.4f}  "
              f"{flag}  ({elapsed:.1f}s)")

    total = time.time() - t0
    print(f"\n总耗时 {total:.1f}s ({total/60:.1f} min)")

    # CSV
    with open("sensitivity_results.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(results[0].keys()))
        w.writeheader()
        for r in results:
            w.writerow(r)
    print("写  sensitivity_results.csv")

    # JSON
    with open("sensitivity_results.json", "w", encoding="utf-8") as f:
        json.dump({
            "experiment": "QN2025106-IND3-Sensitivity",
            "date": "2026-05-12",
            "model": "Supervised NMF",
            "primary_metric": "Top1_dominant (≥ 0.85 = pass)",
            "grid_size": len(configs),
            "seeds": SEEDS,
            "alphas": ALPHAS,
            "bandwidths": BANDWIDTHS,
            "results": results,
        }, f, ensure_ascii=False, indent=2)
    print("写  sensitivity_results.json")

    # ---- Aggregate summaries (collapse along seeds) ----
    print()
    print("=" * 72)
    print("敏感性摘要 1: (α, bandwidth) 网格 — 按 seed 求均值")
    print("=" * 72)

    # collapse: for each (alpha, bw), mean across seeds
    summary_2d = {}
    for r in results:
        key = (r["alpha"], r["bandwidth"])
        summary_2d.setdefault(key, []).append(r["top1_dom_mean"])

    header = f"  α \\ bw " + "".join([f"  bw={bw:>4.1f}Ma " for bw in BANDWIDTHS])
    print(header)
    for alpha in ALPHAS:
        row = f"  α={alpha:.1f}    "
        for bw in BANDWIDTHS:
            vals = summary_2d.get((alpha, bw), [])
            m = np.mean(vals) if vals else float("nan")
            marker = " " if m >= 0.85 else "✗"
            row += f"  {m:.4f}{marker} "
        print(row)

    # 失败计数
    failed = [r for r in results if not r["threshold_met"]]
    print()
    print(f"未达阈值 ≥ 0.85 的 config 数: {len(failed)} / {len(configs)}")
    for r in failed:
        print(f"  seed={r['seed']:2d}  α={r['alpha']:.1f}  bw={r['bandwidth']:5.1f}Ma  "
              f"→ Top1_dom = {r['top1_dom_mean']:.4f}")

    # ---- Markdown summary ----
    md = []
    md.append("# QN2025106 指标 #3 敏感性扫描结果\n")
    md.append(f"日期: 2026-05-12   主模型: Supervised NMF\n")
    md.append(f"扫描格点: seeds × alphas × bandwidths = {len(SEEDS)} × {len(ALPHAS)} × {len(BANDWIDTHS)} = {len(configs)}\n\n")
    md.append("## 主指标平均(按 5 个 seed 求均值)\n\n")
    md.append("| α \\ bandwidth (Ma) | " + " | ".join([f"{bw:.1f}" for bw in BANDWIDTHS]) + " |\n")
    md.append("|---|" + "|".join(["---"] * len(BANDWIDTHS)) + "|\n")
    for alpha in ALPHAS:
        row_cells = [f"α = {alpha:.1f}"]
        for bw in BANDWIDTHS:
            vals = summary_2d.get((alpha, bw), [])
            m = np.mean(vals) if vals else float("nan")
            mark = "" if m >= 0.85 else " ⚠"
            row_cells.append(f"{m:.4f}{mark}")
        md.append("| " + " | ".join(row_cells) + " |\n")
    md.append(f"\n**未达 ≥ 0.85 的 config 数: {len(failed)} / {len(configs)}**\n\n")
    if failed:
        md.append("\n### 未达阈值 config:\n")
        for r in failed:
            md.append(f"- seed={r['seed']}, α={r['alpha']:.1f}, bw={r['bandwidth']:.1f}Ma → Top1_dom = {r['top1_dom_mean']:.4f}\n")
    md.append("\n## 推荐默认超参\n\n")
    # 找最佳 (alpha, bw) 平均
    best_key = max(summary_2d.keys(), key=lambda k: np.mean(summary_2d[k]))
    best_mean = np.mean(summary_2d[best_key])
    md.append(f"- α = {best_key[0]:.1f}, bandwidth = {best_key[1]:.1f} Ma → 平均 Top1_dom = {best_mean:.4f}\n")
    md.append(f"- 首跑设定 (α=0.5, bw=12 Ma) → 平均 Top1_dom = {np.mean(summary_2d[(0.5, 12.0)]):.4f}\n")

    with open("第一篇_MG_DZ方法/sensitivity_summary.md", "w", encoding="utf-8") as f:
        f.writelines(md)
    print("\n写  sensitivity_summary.md")


if __name__ == "__main__":
    main()
