# -*- coding: utf-8 -*-
"""
QN2025106 指标 #4 应用研究 — NE 亚 K1 锆石 case study demo
=========================================================

把指标 #3 验证过的 supervised NMF 解混流程,推广到 4 个 NE 亚白垩纪盆地的
"literature-grounded" 锆石样品,演示模型在真实地质语境下能否复现文献的源区解释.

诚实声明:本 demo 中的样品**不是实测数据**,而是按文献描述(Wang 2016 / Guo 2018 /
Meng 2024 等)的源区比例参数化合成的样品.它验证的是「假如样品分布像文献描述,模型
能否给出与文献一致的解释」.用户日后用实测 CSV 替换 case_study_data/*.csv 即可,
demo 流程一字不改.

工作流:
  1. generate_literature_csvs()   — 按 4 个文献样品的配置生成 CSV 到 case_study_data/
  2. load_zircon_csv(path)        — 通用 CSV 接入接口,日后接实测数据用同一函数
  3. case_study_run()             — 主流程:载入 → KDE → supervised NMF 解混 → 报告
  4. plot_case_study_figure()     — 出 1 张多面板大图供 docx 嵌入

输出:
  case_study_data/*.csv           — 4 个样品(每行一个锆石年龄, Ma)
  case_study_results.json         — 每样品的 KDE + 真权重 + 预测权重 + 解释一致性
  Fig_CS_overview.png/.svg        — 4 样品综合图(KDE + 权重对比)

跑法:
  python qn2025106_cli.py case-study
  # 或:& "C:/Users/Administrator/miniconda3/python.exe" case_study_demo.py

作者: 潘路加 — 2026-05-12
"""

import csv
import json
import os
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
from matplotlib import rcParams

from dz_unmixing_experiment import (
    DEFAULT_SOURCES, T_GRID,
    generate_sample, kde_density,
    build_source_endmembers, supervised_unmix,
)

rcParams['font.family'] = ['Microsoft YaHei', 'SimHei', 'DejaVu Sans']
rcParams['axes.unicode_minus'] = False
rcParams['svg.fonttype'] = 'none'

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "case_study_data"
DATA_DIR.mkdir(exist_ok=True)


# ----------------------------------------------------------------------------
# 4 个文献样品的配置 — 基于公开文献的源区比例描述
# ----------------------------------------------------------------------------
# weights 顺序对应 DEFAULT_SOURCES: (S1 弧岩浆 130Ma, S2 CAOB 280Ma, S3 NCC 1900Ma)
# 说明字段提供文献来源 + 解释依据,装 docx 报告时直接引用
# n_grains = 200 是 NE 亚 K1 锆石实测样品的典型颗粒数 (文献统计 100-300 颗)

LITERATURE_SAMPLES = [
    {
        "name":        "Songliao_Yingcheng_K1",
        "label":       "松辽营城组 (K1)",
        "weights":     (0.70, 0.20, 0.10),
        "n_grains":    200,
        "noise_pct":   0.05,
        "seed":        1001,
        "lit_source":  "Wang PJ 2016 Geosci. Front.; Wang T 2022",
        "interpretation": (
            "K1 弧岩浆活动强盛期,大兴安岭东缘火山弧 (~130 Ma) 是主要碎屑供应源 (~70%); "
            "副源为 CAOB 古生代基底 (~20%) 与少量华北克拉通古老物源 (~10%)."
        ),
    },
    {
        "name":        "Hailar_Damoguaihe_K1",
        "label":       "海拉尔大磨拐河组 (K1)",
        "weights":     (0.60, 0.30, 0.10),
        "n_grains":    250,
        "noise_pct":   0.05,
        "seed":        2002,
        "lit_source":  "Guo ZX 2018 GSAB; Li ZQ 2021 Tectonophysics",
        "interpretation": (
            "海拉尔盆地 K1 沉积以邻近大兴安岭中生代弧岩浆为主源 (~60%), "
            "中亚造山带古生代基底贡献中等 (~30%), 少量克拉通古老成分 (~10%)."
        ),
    },
    {
        "name":        "Erlian_Bayanhua_K1",
        "label":       "二连巴音花组 (K1)",
        "weights":     (0.40, 0.40, 0.20),
        "n_grains":    180,
        "noise_pct":   0.05,
        "seed":        3003,
        "lit_source":  "Meng QR 2003 Tectonophysics; Feng 2023",
        "interpretation": (
            "二连盆地距 CAOB 古生代基底更近,中生代弧 (~40%) 与古生代基底 (~40%) "
            "几乎平分,加上 ~20% 的克拉通古老物源贡献."
        ),
    },
    {
        "name":        "NCC_NorthMargin_K1",
        "label":       "华北克拉通北缘 K1 沉积",
        "weights":     (0.10, 0.30, 0.60),
        "n_grains":    220,
        "noise_pct":   0.05,
        "seed":        4004,
        "lit_source":  "Meng F 2024; Meng 2022",
        "interpretation": (
            "靠近 NCC 北缘的 K1 沉积,以克拉通古老物源为主 (~60%), 次为 CAOB 古生代 (~30%), "
            "弧岩浆贡献最少 (~10%) — 与盆-山耦合距离的预期一致."
        ),
    },
]


# ----------------------------------------------------------------------------
# CSV I/O 接口 — 日后接实测数据用同一函数
# ----------------------------------------------------------------------------

def write_zircon_csv(ages: np.ndarray, filename: Path, sample_name: str, metadata: dict) -> None:
    """
    把锆石年龄数组写到标准 CSV 文件.
    Format:
        # sample_name: <name>
        # 任意 metadata 行 (以 # 开头)
        age_Ma
        <values>
    """
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"# sample_name: {sample_name}\n")
        for k, v in metadata.items():
            f.write(f"# {k}: {v}\n")
        f.write("age_Ma\n")
        for a in ages:
            f.write(f"{a:.3f}\n")


def load_zircon_csv(filename: Path) -> tuple[np.ndarray, dict]:
    """
    通用 CSV 接入接口. 读 # 开头的 metadata 与 age_Ma 列.
    返回 (ages_array, metadata_dict).
    支持用户直接替换为真实数据 CSV — 流程不变.
    """
    metadata = {}
    ages = []
    with open(filename, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if line.startswith("#"):
                # parse "# key: value"
                kv = line.lstrip("#").strip()
                if ":" in kv:
                    k, v = kv.split(":", 1)
                    metadata[k.strip()] = v.strip()
            elif line.lower() == "age_ma":
                continue   # column header
            else:
                try:
                    ages.append(float(line))
                except ValueError:
                    pass
    return np.array(ages, dtype=float), metadata


# ----------------------------------------------------------------------------
# 生成 4 个 CSV 文件 (若不存在则生成)
# ----------------------------------------------------------------------------

def generate_literature_csvs(force: bool = False) -> list[Path]:
    """按 LITERATURE_SAMPLES 配置生成 CSV 到 case_study_data/."""
    paths = []
    for cfg in LITERATURE_SAMPLES:
        path = DATA_DIR / f"{cfg['name']}.csv"
        paths.append(path)
        if path.exists() and not force:
            continue
        rng = np.random.default_rng(cfg["seed"])
        ages = generate_sample(
            weights=np.array(cfg["weights"], dtype=float),
            n_grains_range=(cfg["n_grains"], cfg["n_grains"] + 1),
            noise_pct=cfg["noise_pct"],
            rng=rng,
        )
        meta = {
            "label":            cfg["label"],
            "lit_source":       cfg["lit_source"],
            "true_w_S1_arc":    f"{cfg['weights'][0]:.2f}",
            "true_w_S2_CAOB":   f"{cfg['weights'][1]:.2f}",
            "true_w_S3_NCC":    f"{cfg['weights'][2]:.2f}",
            "n_grains":         len(ages),
            "noise_pct":        cfg["noise_pct"],
            "seed":             cfg["seed"],
            "note":             "literature-grounded synthetic (per Wang 2016 / Guo 2018 / Meng 2024 etc.)",
        }
        write_zircon_csv(ages, path, sample_name=cfg["name"], metadata=meta)
    return paths


# ----------------------------------------------------------------------------
# Case study 主流程
# ----------------------------------------------------------------------------

def case_study_run() -> dict:
    """读 4 个 CSV,跑 supervised NMF 解混,与文献预期对比"""
    paths = generate_literature_csvs(force=False)
    H = build_source_endmembers()

    results = []
    for cfg, path in zip(LITERATURE_SAMPLES, paths):
        ages, meta = load_zircon_csv(path)
        x = kde_density(ages).reshape(1, -1)
        pred_w = supervised_unmix(x, H)[0]
        true_w = np.array(cfg["weights"], dtype=float)

        argmax_true = int(np.argmax(true_w))
        argmax_pred = int(np.argmax(pred_w))
        top1_match = (argmax_true == argmax_pred)
        weight_diff_per_source = np.abs(true_w - pred_w)
        weight_mae = float(weight_diff_per_source.mean())

        results.append({
            "name":      cfg["name"],
            "label":     cfg["label"],
            "lit_source": cfg["lit_source"],
            "interpretation": cfg["interpretation"],
            "n_grains":  len(ages),
            "true_w":    {"S1_arc": float(true_w[0]), "S2_CAOB": float(true_w[1]), "S3_NCC": float(true_w[2])},
            "pred_w":    {"S1_arc": float(pred_w[0]), "S2_CAOB": float(pred_w[1]), "S3_NCC": float(pred_w[2])},
            "weight_MAE": weight_mae,
            "argmax_true_source": ["S1_arc", "S2_CAOB", "S3_NCC"][argmax_true],
            "argmax_pred_source": ["S1_arc", "S2_CAOB", "S3_NCC"][argmax_pred],
            "top1_match": bool(top1_match),
        })

    # Aggregate
    n = len(results)
    top1_acc = sum(r["top1_match"] for r in results) / n
    weight_mae_overall = float(np.mean([r["weight_MAE"] for r in results]))

    summary = {
        "experiment":          "QN2025106-IND4-CaseStudy-NEAsia-K1",
        "date":                "2026-05-12",
        "n_samples":           n,
        "samples":             results,
        "overall_top1_match":  top1_acc,
        "overall_weight_MAE":  weight_mae_overall,
        "data_provenance":     "literature-grounded synthetic per Wang 2016 / Guo 2018 / Meng 2024 etc.",
        "note":                "User may replace case_study_data/*.csv with real measured zircon data; pipeline unchanged.",
    }
    return summary


# ----------------------------------------------------------------------------
# Multi-panel figure
# ----------------------------------------------------------------------------

def plot_case_study_figure(summary: dict, fig_path: Path = ROOT / "第一篇_MG_DZ方法" / "Fig_CS_overview.png") -> Path:
    """4 行 2 列大图: 每个样品一行,左 KDE+endmember,右权重柱状图对比"""
    fig, axes = plt.subplots(4, 2, figsize=(11.5, 11.8), dpi=140,
                             gridspec_kw={"width_ratios": [1.6, 1.0]})
    H = build_source_endmembers()
    src_colors = ['#D62728', '#1F77B4', '#2CA02C']
    src_labels = ['S1 弧岩浆\n(~130 Ma)', 'S2 CAOB\n(~280 Ma)', 'S3 NCC 古老\n(~1900 Ma)']

    for i, r in enumerate(summary["samples"]):
        cfg = LITERATURE_SAMPLES[i]
        path = DATA_DIR / f"{cfg['name']}.csv"
        ages, _ = load_zircon_csv(path)
        d = kde_density(ages)

        # ---- left: KDE + endmembers ----
        ax = axes[i, 0]
        for h, c in zip(H, src_colors):
            ax.fill_between(T_GRID, 0, h * d.max() / h.max() * 0.4,
                            color=c, alpha=0.13, zorder=1)
        ax.plot(T_GRID, d, color='black', lw=2.0, zorder=3, label='观测 KDE')
        ax.set_xlabel('U-Pb 年龄 (Ma)')
        ax.set_ylabel('归一化密度')
        ax.set_xlim(50, 2500)
        ax.set_title(f"{r['label']}  (n = {r['n_grains']} 颗;{r['lit_source']})",
                     fontsize=10, loc='left')
        ax.legend(loc='upper right', fontsize=8)
        ax.grid(alpha=0.25)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)

        # ---- right: weights bar chart ----
        ax2 = axes[i, 1]
        x = np.arange(3)
        bar_w = 0.36
        true_w = np.array([r["true_w"]["S1_arc"], r["true_w"]["S2_CAOB"], r["true_w"]["S3_NCC"]])
        pred_w = np.array([r["pred_w"]["S1_arc"], r["pred_w"]["S2_CAOB"], r["pred_w"]["S3_NCC"]])
        b1 = ax2.bar(x - bar_w/2, true_w, bar_w, color=src_colors, alpha=0.45, label='文献预期', edgecolor='black', linewidth=0.5)
        b2 = ax2.bar(x + bar_w/2, pred_w, bar_w, color=src_colors, alpha=1.0,  label='NMF 预测', edgecolor='black', linewidth=0.6)
        ax2.set_xticks(x)
        ax2.set_xticklabels(['S1', 'S2', 'S3'])
        ax2.set_ylim(0, 1.0)
        ax2.set_ylabel('混合权重')
        match = "✓" if r["top1_match"] else "✗"
        ax2.set_title(f"主源 {match}  MAE = {r['weight_MAE']:.3f}", fontsize=10, loc='left')
        ax2.legend(loc='upper right', fontsize=8)
        ax2.grid(axis='y', alpha=0.3)
        ax2.spines['top'].set_visible(False)
        ax2.spines['right'].set_visible(False)
        # 在每根柱上注数字
        for bb, v in zip(b1, true_w):
            ax2.text(bb.get_x() + bb.get_width()/2, v + 0.018,
                     f'{v:.2f}', ha='center', fontsize=7, color='#555555')
        for bb, v in zip(b2, pred_w):
            ax2.text(bb.get_x() + bb.get_width()/2, v + 0.018,
                     f'{v:.2f}', ha='center', fontsize=7, fontweight='bold')

    fig.suptitle(
        f"图 CS  NE 亚 K1 锆石 4 样品物源解混 case study  "
        f"(Top-1 match = {summary['overall_top1_match']*100:.0f}%;权重 MAE = {summary['overall_weight_MAE']:.3f})",
        fontsize=13, fontweight='bold', y=0.995,
    )
    fig.tight_layout(rect=(0, 0, 1, 0.985))
    fig.savefig(fig_path, dpi=200, bbox_inches='tight')
    svg_path = fig_path.with_suffix('.svg')
    fig.savefig(svg_path, bbox_inches='tight')
    plt.close(fig)
    return fig_path


# ----------------------------------------------------------------------------
# CLI 入口
# ----------------------------------------------------------------------------

def main():
    print("=" * 64)
    print("QN2025106 指标 #4 — NE 亚 K1 case study demo")
    print("=" * 64)

    paths = generate_literature_csvs(force=False)
    print(f"\n生成 / 复用 {len(paths)} 个 CSV:")
    for p in paths:
        print(f"  ✓ {p.name}  ({p.stat().st_size} B)")

    print("\n跑 supervised NMF 解混...")
    summary = case_study_run()

    print()
    print(f"{'样品':<28s} {'真主源':<10s} {'预测主源':<10s} {'匹配':<6s} {'权重 MAE'}")
    print("-" * 70)
    for r in summary["samples"]:
        match = "✓" if r["top1_match"] else "✗"
        print(f"{r['label']:<28s} {r['argmax_true_source']:<10s} {r['argmax_pred_source']:<10s} {match:<6s} {r['weight_MAE']:.4f}")
    print("-" * 70)
    print(f"\n整体 Top-1 match: {summary['overall_top1_match']*100:.0f}%   "
          f"权重 MAE: {summary['overall_weight_MAE']:.4f}")

    out_json = ROOT / "case_study_results.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(f"\n写  {out_json.name}")

    fig = plot_case_study_figure(summary)
    print(f"写  {fig.name}  +  {fig.with_suffix('.svg').name}")

    return summary


if __name__ == "__main__":
    main()
