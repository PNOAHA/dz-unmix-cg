# -*- coding: utf-8 -*-
"""
QN2025106 数据平台 MVP — 统一 CLI 入口
=====================================

把所有实验脚本组织成一个可调用的命令行工具,对应任务书指标 #2「沉积地质学大数据分析平台」.

子命令:
  run-experiment    跑首跑 (5 折 CV, supervised + unsupervised NMF)
  sensitivity       跑 75-config 敏感性扫描 (5 seed × 3 α × 5 bandwidth)
  figures           生成 3 张报告配图 (R1 源区密度 / R2 敏感性热图 / R3 α 影响)
  report            构建中文实验报告 docx (需先有 results)
  design            构建中文实验设计 docx
  build-manuscript  构建英文 manuscript docx (走 Node)
  test              跑单元测试
  status            打印项目状态摘要
  all               跑 experiment → sensitivity → figures → report 全流程
  list              列出所有可调用子命令

跑法:
  & "C:/Users/Administrator/miniconda3/python.exe" qn2025106_cli.py <subcommand>

例:
  python qn2025106_cli.py all          # 全流程一键跑 (~3 min)
  python qn2025106_cli.py status       # 看当前状态
  python qn2025106_cli.py test         # 跑单元测试

作者: 潘路加 - 2026-05-12
"""

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PY = sys.executable

# ----------------------------------------------------------------------------
# Subcommand implementations
# ----------------------------------------------------------------------------

def _run_py(script: str, label: str) -> int:
    """Run a sibling Python script with current python interpreter."""
    path = ROOT / script
    if not path.exists():
        print(f"[ERROR] 找不到脚本: {path}")
        return 1
    print(f"\n[CLI] -> {label}: {script}")
    t0 = time.time()
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    rc = subprocess.call([PY, str(path)], cwd=ROOT, env=env)
    dt = time.time() - t0
    status = "[OK]" if rc == 0 else "[X]"
    print(f"[CLI] {status} {label} 完成 (rc={rc}, {dt:.1f}s)")
    return rc


def _run_node(script: str, label: str) -> int:
    """Run a sibling node .js script. Uses NODE_PATH from global npm root."""
    path = ROOT / script
    if not path.exists():
        print(f"[ERROR] 找不到脚本: {path}")
        return 1
    print(f"\n[CLI] -> {label}: {script}")
    # Detect npm root
    try:
        npm_root = subprocess.check_output(
            ["npm", "root", "-g"], text=True, shell=(os.name == "nt")
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        npm_root = ""
    env = os.environ.copy()
    if npm_root:
        env["NODE_PATH"] = npm_root
    t0 = time.time()
    rc = subprocess.call(["node", str(path)], cwd=ROOT, env=env,
                         shell=(os.name == "nt"))
    dt = time.time() - t0
    status = "[OK]" if rc == 0 else "[X]"
    print(f"[CLI] {status} {label} 完成 (rc={rc}, {dt:.1f}s)")
    return rc


def cmd_run_experiment(args):
    """跑首跑实验 (5 折 CV, supervised + unsupervised NMF, ~30s)"""
    return _run_py("dz_unmixing_experiment.py", "首跑 NMF 实验 (5 折 CV)")


def cmd_sensitivity(args):
    """跑 75-config 敏感性扫描 (~110s)"""
    return _run_py("sensitivity_scan.py", "敏感性扫描 (75-config)")


def cmd_figures(args):
    """出 3 张报告配图 (R1 源区密度 / R2 热图 / R3 α 影响)"""
    # figures 依赖 sensitivity_results.csv
    if not (ROOT / "sensitivity_results.csv").exists():
        print("[WARN] 找不到 sensitivity_results.csv,先跑 sensitivity")
        rc = cmd_sensitivity(args)
        if rc != 0:
            return rc
    return _run_py("fig_experiment_report.py", "出 3 张配图")


def cmd_case_study(args):
    """跑 NE 亚 K1 case study demo (4 个 literature-grounded 样品 + 出 Fig_CS_overview)"""
    rc = _run_py("case_study_demo.py", "NE 亚 K1 case study demo")
    if rc != 0:
        return rc
    if (ROOT / "case_study_results.json").exists() and (ROOT / "第一篇_MG_DZ方法" / "Fig_CS_overview.png").exists():
        return _run_node("build_case_study_report.js", "构建 case study 中文 docx 报告")
    return rc


def cmd_report(args):
    """构建中文实验报告 docx (需 results + figures)"""
    # report 依赖三张图 + sensitivity_results.csv + dz_unmixing_results.json
    for needed in ["dz_unmixing_results.json", "sensitivity_results.csv",
                   "第一篇_MG_DZ方法/Fig_R1_sources.png", "第一篇_MG_DZ方法/Fig_R2_sensitivity.png", "第一篇_MG_DZ方法/Fig_R3_alpha_effect.png"]:
        if not (ROOT / needed).exists():
            print(f"[ERROR] 缺少依赖: {needed} — 先跑 'all' 或对应子命令")
            return 2
    return _run_node("build_experiment_report.js", "构建中文实验报告 docx")


def cmd_design(args):
    """构建中文实验设计 docx (13 章)"""
    return _run_node("build_experiment_design.js", "构建中文实验设计 docx")


def cmd_build_manuscript(args):
    """构建英文 manuscript docx (MG 投稿稿 v23)"""
    return _run_node("build_mg_manuscript.js", "构建英文 manuscript docx (MG 投稿稿)")


def cmd_test(args):
    """跑 tests/ 下单元测试"""
    test_path = ROOT / "tests" / "test_dz_unmixing.py"
    if not test_path.exists():
        print(f"[ERROR] 找不到测试: {test_path}")
        return 1
    print("\n[CLI] -> 跑单元测试")
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONPATH"] = str(ROOT) + os.pathsep + env.get("PYTHONPATH", "")
    rc = subprocess.call([PY, "-m", "unittest", "tests.test_dz_unmixing", "-v"],
                         cwd=ROOT, env=env)
    status = "[OK]" if rc == 0 else "[X]"
    print(f"[CLI] {status} 单元测试完成 (rc={rc})")
    return rc


def cmd_all(args):
    """跑实验 → 敏感性扫描 → 配图 → 报告 全流程。约 3 min。"""
    print("=" * 64)
    print("QN2025106 全流程一键跑")
    print("=" * 64)
    t0 = time.time()
    for fn, label in [
        (cmd_run_experiment, "首跑实验"),
        (cmd_sensitivity,    "敏感性扫描"),
        (cmd_figures,        "出配图"),
        (cmd_report,         "出报告"),
    ]:
        rc = fn(args)
        if rc != 0:
            print(f"\n[CLI] [X] 在 {label} 步骤失败 (rc={rc}),终止")
            return rc
    total = time.time() - t0
    print()
    print("=" * 64)
    print(f"[OK] 全流程完成,总耗时 {total/60:.1f} 分钟")
    print("=" * 64)
    return 0


def cmd_status(args):
    """打印当前项目交付物状态."""
    print("=" * 64)
    print("QN2025106 项目状态摘要")
    print("=" * 64)

    deliverables = [
        ("学术论文 (指标 #1)", [
            ("第一篇_MG_DZ方法/QN2025106_MG_manuscript_v23.docx", "投稿主稿 v23"),
            ("第一篇_MG_DZ方法/MATG-S-26-00174.pdf",              "EM 合成投稿 PDF"),
            ("第一篇_MG_DZ方法/QN2025106_MG_cover_letter.docx",   "Cover letter"),
        ]),
        ("实验脚本 (指标 #3 平台部分)", [
            ("dz_unmixing_experiment.py", "主实验"),
            ("sensitivity_scan.py",       "敏感性扫描"),
            ("fig_experiment_report.py",  "配图生成"),
            ("qn2025106_cli.py",          "CLI 统一入口"),
        ]),
        ("实验结果 (指标 #3 数据)", [
            ("dz_unmixing_results.json",  "首跑结果"),
            ("sensitivity_results.csv",   "75-config 扫描表"),
            ("sensitivity_results.json",  "75-config 结构化"),
            ("第一篇_MG_DZ方法/sensitivity_summary.md",    "扫描摘要"),
        ]),
        ("配图 (指标 #3 可视化)", [
            ("第一篇_MG_DZ方法/Fig_R1_sources.png",        "图 R1 三源区密度"),
            ("第一篇_MG_DZ方法/Fig_R2_sensitivity.png",    "图 R2 敏感性热图"),
            ("第一篇_MG_DZ方法/Fig_R3_alpha_effect.png",   "图 R3 α 影响"),
        ]),
        ("Case study (指标 #4 应用研究)", [
            ("case_study_demo.py",                 "case study 主脚本"),
            ("case_study_data/Songliao_Yingcheng_K1.csv", "样品 CSV 1/4"),
            ("case_study_data/Hailar_Damoguaihe_K1.csv",  "样品 CSV 2/4"),
            ("case_study_data/Erlian_Bayanhua_K1.csv",    "样品 CSV 3/4"),
            ("case_study_data/NCC_NorthMargin_K1.csv",    "样品 CSV 4/4"),
            ("case_study_results.json",            "解混结果"),
            ("第一篇_MG_DZ方法/Fig_CS_overview.png",                "4 样品综合图"),
        ]),
        ("文档 (指标 #3/#4 结项材料)", [
            ("第一篇_MG_DZ方法/QN2025106_模型验证实验设计.docx", "实验设计 (13 章)"),
            ("第一篇_MG_DZ方法/QN2025106_模型验证实验报告.docx", "实验报告 (7 章 + 附录)"),
            ("第一篇_MG_DZ方法/QN2025106_case_study_NEAsia_K1.docx", "case study 报告 (指标 #4)"),
            ("第一篇_MG_DZ方法/QN2025106_考核指标完成度自查表_v4.docx", "自查表 v4 (当前,6/6 就绪)"),
        ]),
        ("软著申请源 docx (指标 #5)", [
            ("软著_DZ-Unmix_V1.0/DZ-Unmix_V1.0_软件设计说明书.docx",       "源 docx - 设计说明书"),
            ("软著_DZ-Unmix_V1.0/DZ-Unmix_V1.0_用户操作手册.docx",         "源 docx - 用户手册"),
            ("软著_DZ-Unmix_V1.0/DZ-Unmix_V1.0_源代码.docx",               "源 docx - 源代码"),
            ("软著_DZ-Unmix_V1.0/DZ-Unmix_V1.0_软件著作权申请清单.docx",   "源 docx - 申请清单"),
            ("软著_DZ-Unmix_V1.0/DZ-Unmix_V1.0_提交分步指引.docx",         "源 docx - 提交指引"),
        ]),
        ("软著提交 PDF (软著提交_2026-05/)", [
            ("软著_DZ-Unmix_V1.0/软著提交_2026-05/0_README.txt",                                     "* 先看 — 文件夹说明"),
            ("软著_DZ-Unmix_V1.0/软著提交_2026-05/00_打开我_提交分步指引.pdf",                        "* 操作时打开"),
            ("软著_DZ-Unmix_V1.0/软著提交_2026-05/要上传的_3个PDF/03_源代码.pdf",                     "→ 程序鉴别材料槽(法定主鉴别)"),
            ("软著_DZ-Unmix_V1.0/软著提交_2026-05/要上传的_3个PDF/01_软件设计说明书.pdf",              "→ 文档鉴别材料槽"),
            ("软著_DZ-Unmix_V1.0/软著提交_2026-05/要上传的_3个PDF/02_用户操作手册.pdf",                "→ 其他相关证明文件槽"),
            ("软著_DZ-Unmix_V1.0/软著提交_2026-05/99_自留_申请清单.pdf",                             "自留参考"),
        ]),
        ("项目元数据", [
            ("PROJECT_STATUS.md",  "项目状态单一事实源"),
            ("README.md",          "仓库 README"),
            ("requirements.txt",   "Python 依赖"),
        ]),
    ]

    primary_metric = None
    if (ROOT / "dz_unmixing_results.json").exists():
        try:
            with open(ROOT / "dz_unmixing_results.json", "r", encoding="utf-8") as f:
                results = json.load(f)
            primary_metric = results.get("primary_metric_top1_dominant_supervised")
        except Exception:
            pass

    if primary_metric is not None:
        flag = "[OK]" if primary_metric >= 0.85 else "[X]"
        print(f"\n指标 #3 主指标 (Top-1 dominant): {primary_metric:.4f}  vs 阈值 0.85  {flag}")
    else:
        print("\n指标 #3 主指标: 未跑过 (运行 'python qn2025106_cli.py run-experiment')")

    print()
    for group_name, items in deliverables:
        print(f"--- {group_name} ---")
        for fn, desc in items:
            path = ROOT / fn
            mark = "[OK]" if path.exists() else "[X]"
            size = f"({path.stat().st_size} B)" if path.exists() else "(missing)"
            print(f"  {mark}  {fn:42s} {size:>12s}  {desc}")
        print()
    return 0


def cmd_list(args):
    """列出所有可调用子命令."""
    print("可调用子命令:")
    for name, fn in SUBCMDS.items():
        doc = (fn.__doc__ or "").strip().split("\n")[0] or "(无描述)"
        print(f"  {name:18s} {doc}")
    return 0


# ----------------------------------------------------------------------------
# Dispatch
# ----------------------------------------------------------------------------

SUBCMDS = {
    "run-experiment":    cmd_run_experiment,
    "sensitivity":       cmd_sensitivity,
    "figures":           cmd_figures,
    "report":            cmd_report,
    "case-study":        cmd_case_study,
    "design":            cmd_design,
    "build-manuscript":  cmd_build_manuscript,
    "test":              cmd_test,
    "all":               cmd_all,
    "status":            cmd_status,
    "list":              cmd_list,
}


def main():
    parser = argparse.ArgumentParser(
        prog="qn2025106",
        description="QN2025106 河北省高等学校科学研究项目  数据平台 MVP CLI",
        epilog="例: python qn2025106_cli.py all   |   python qn2025106_cli.py status",
    )
    parser.add_argument("subcommand", nargs="?", default="list",
                        choices=list(SUBCMDS.keys()),
                        help="要执行的子命令; 默认 'list'")
    args = parser.parse_args()
    return SUBCMDS[args.subcommand](args)


if __name__ == "__main__":
    sys.exit(main())
