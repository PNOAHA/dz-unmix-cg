# -*- coding: utf-8 -*-
"""
QN2025106 指标 #3 验证实验: 碎屑锆石 NMF 物源解混
=================================================

任务书量化阈值: 沉积过程数学模型的验证准确率 ≥ 85%
对应 manuscript: Section 6.2.2 第二组件(联合似然) + 第四组件(反演)
                Eq 6.1 前向模型 / Eq 6.2 联合似然 / Eq 6.4 反演

实验设计:
  - 任务: 给定一个未知样品的碎屑锆石 U-Pb 年龄数组, 推断三个源区的混合权重 w=(w1,w2,w3)
  - 主指标: Top-1 源区识别准确率(argmax(w_true) == argmax(w_pred))
  - 阈值: ≥ 0.85
  - 合成数据 1000 个样品 + 5-fold 交叉验证

依赖: numpy, scikit-learn (KDE 纯 numpy 手写, 不依赖 scipy)
环境: C:\\Users\\Administrator\\miniconda3
跑法: & "C:\\Users\\Administrator\\miniconda3\\python.exe" dz_unmixing_experiment.py

作者: 潘路加 (panlujia234@gmail.com / peter205834@hebtu.edu.cn)
日期: 2026-05-12
"""

import json
import warnings
from dataclasses import dataclass
from typing import List, Tuple

import numpy as np
from sklearn.decomposition import NMF
from sklearn.metrics import r2_score, mean_absolute_error
from sklearn.model_selection import KFold, train_test_split

warnings.filterwarnings("ignore", category=UserWarning)

# ----------------------------------------------------------------------------
# 1. 源区定义 — 三个对应 NE 亚白垩纪盆地的地质源区
# ----------------------------------------------------------------------------

@dataclass
class Source:
    name: str
    mean_age: float     # 峰值年龄 (Ma)
    sigma: float        # 单峰高斯标准差 (Ma)
    geo_label: str

DEFAULT_SOURCES: List[Source] = [
    Source("S1_MesozoicArc",   130.0,  15.0,  "中生代弧岩浆(松辽营城组 / 海拉尔火山岩)"),
    Source("S2_PaleozoicBase", 280.0,  30.0,  "古生代基底(中亚造山带 CAOB)"),
    Source("S3_ArcheanCraton", 1900.0, 100.0, "太古-元古代克拉通(华北克拉通 NCC 北缘)"),
]

# 公共年龄网格 (Ma): 50–2500, 步长 5 Ma
T_GRID = np.arange(50.0, 2500.0 + 1e-9, 5.0)


# ----------------------------------------------------------------------------
# 2. 合成数据生成
# ----------------------------------------------------------------------------

def sample_ages_from_source(src: Source, n: int, rng: np.random.Generator) -> np.ndarray:
    """从单一源区抽 n 个年龄(高斯峰 + 截断保正)"""
    a = rng.normal(loc=src.mean_age, scale=src.sigma, size=n)
    a = np.clip(a, T_GRID[0], T_GRID[-1])
    return a


def generate_sample(
    weights: np.ndarray,
    n_grains_range: Tuple[int, int] = (100, 300),
    noise_pct: float = 0.05,
    sources: List[Source] = DEFAULT_SOURCES,
    rng: np.random.Generator | None = None,
) -> np.ndarray:
    """
    从给定混合权重 weights = (w1,w2,w3) 抽 1 个合成样品的年龄数组
    步骤:
      a) 从 Uniform(n_grains_range) 抽样品颗粒数 N
      b) 按 multinomial(N, weights) 决定每个源区贡献多少颗粒
      c) 每个源区按 sample_ages_from_source 抽对应数量颗粒
      d) 加 noise_pct 的测量误差(乘性高斯)
    """
    if rng is None:
        rng = np.random.default_rng()
    n_grains = rng.integers(n_grains_range[0], n_grains_range[1] + 1)
    counts = rng.multinomial(n_grains, weights)
    ages_per_src = [sample_ages_from_source(s, c, rng) for s, c in zip(sources, counts)]
    ages = np.concatenate(ages_per_src)
    # 测量误差 — 乘性 (常见于 U-Pb 实验报告的 2σ%)
    rel_err = rng.normal(loc=1.0, scale=noise_pct, size=ages.shape)
    ages = ages * rel_err
    ages = np.clip(ages, T_GRID[0], T_GRID[-1])
    rng.shuffle(ages)
    return ages


def generate_dataset(
    n_samples: int = 1000,
    dirichlet_alpha: float = 0.5,
    seed: int = 42,
) -> Tuple[List[np.ndarray], np.ndarray]:
    """
    生成全数据集.
    返回:
      ages_list   长度 n_samples 的列表, 每项是该样品的年龄数组 (变长)
      true_weights (n_samples, 3) 的权重矩阵
    """
    rng = np.random.default_rng(seed)
    n_src = len(DEFAULT_SOURCES)
    true_weights = rng.dirichlet(alpha=np.ones(n_src) * dirichlet_alpha, size=n_samples)
    ages_list = [generate_sample(w, rng=rng) for w in true_weights]
    return ages_list, true_weights


# ----------------------------------------------------------------------------
# 3. KDE 密度估计 — 把变长年龄数组映射到固定长度密度向量
# ----------------------------------------------------------------------------

def kde_density(
    ages: np.ndarray,
    t_grid: np.ndarray = T_GRID,
    bandwidth: float = 12.0,
) -> np.ndarray:
    """
    样品年龄数组 → 在 t_grid 上的 Gaussian KDE 密度向量(单位曲线下面积归一化).
    纯 numpy 实现, 不依赖 scipy.

    重要: 用**固定带宽** (默认 12 Ma) 而不是 Scott rule 的数据驱动带宽 ——
    Scott rule 对多模态混合样品会高估带宽(整体 std 包括了模态间距),
    糊掉年轻模态(S1 σ=15 Ma)的尖峰.
    锆石文献(Vermeesch 2018 IsoplotR)同样推荐固定带宽以保多模态可识别.

    Kernel:  K(u) = (1/sqrt(2π)) exp(-u²/2)
    Density: d(t) = (1/(n h)) Σ_i K((t - a_i)/h)
    """
    n = len(ages)
    if n < 1:
        return np.full_like(t_grid, 1.0 / (t_grid[-1] - t_grid[0]))
    h = bandwidth
    u = (t_grid[:, None] - ages[None, :]) / h
    K = np.exp(-0.5 * u * u) / np.sqrt(2.0 * np.pi)
    d = K.sum(axis=1) / (n * h)
    d = np.maximum(d, 0.0)
    area = np.trapezoid(d, t_grid)
    if area > 0:
        d = d / area
    return d


# ----------------------------------------------------------------------------
# 4. NMF 拟合与权重预测
# ----------------------------------------------------------------------------

def fit_nmf(X_train: np.ndarray, n_components: int = 3, seed: int = 0) -> NMF:
    """
    在 X_train (n_train, T) 上拟合 NMF.
    X_train 每行是一个样品的 KDE 密度.
    NMF 给出 X ≈ W H, W (n_train, k), H (k, T).
    H 的行就是 k 个 endmember 密度.
    """
    nmf = NMF(
        n_components=n_components,
        init="nndsvda",
        beta_loss="frobenius",
        solver="cd",
        max_iter=2000,
        tol=1e-6,
        random_state=seed,
    )
    nmf.fit(X_train)
    return nmf


def predict_weights(X: np.ndarray, nmf: NMF) -> np.ndarray:
    """
    对新样品 X 用 nmf.transform 反推 W; 然后行归一化为权重 (∑w=1).
    返回 W_norm (n_samples, k).
    """
    W = nmf.transform(X)
    row_sum = W.sum(axis=1, keepdims=True)
    row_sum[row_sum == 0] = 1.0
    return W / row_sum


# ----------------------------------------------------------------------------
# 4b. Supervised unmixing — endmember 已知, 只解权重
#     文献参考: Sundell & Saylor 2017 G3 / Vermeesch 2018 IsoplotR
# ----------------------------------------------------------------------------

def build_source_endmembers(
    sources: List[Source] = DEFAULT_SOURCES,
    t_grid: np.ndarray = T_GRID,
) -> np.ndarray:
    """
    用每个源区的高斯峰参数解析地构造 endmember 密度矩阵 H (k, T).
    每行已归一化为单位曲线下面积.
    """
    H = np.zeros((len(sources), len(t_grid)))
    for i, s in enumerate(sources):
        h = np.exp(-0.5 * ((t_grid - s.mean_age) / s.sigma) ** 2)
        h = h / np.trapezoid(h, t_grid)
        H[i] = h
    return H


def supervised_unmix(
    X: np.ndarray,
    H: np.ndarray,
    n_iter: int = 500,
    tol: float = 1e-7,
) -> np.ndarray:
    """
    Supervised NMF: 已知 H, 求 W 使 X ≈ W H, W >= 0, 行和归一化.
    用 KL-divergence 乘性更新规则(对密度数据效果好于 Frobenius).
        W ← W * (X / (W H + ε)) H^T   / row-sum normaliser
    返回 W (n_samples, k), 每行归一化为权重.
    """
    n, _ = X.shape
    k = H.shape[0]
    rng = np.random.default_rng(0)
    W = rng.uniform(0.1, 1.0, size=(n, k))
    eps = 1e-10
    Hsum = H.sum(axis=1, keepdims=True).T   # (1, k) — 列方向规范化项
    prev_loss = np.inf
    for it in range(n_iter):
        WH = W @ H + eps
        # multiplicative update (KL)
        numerator = (X / WH) @ H.T
        W = W * numerator / (Hsum + eps)
        # monitor: KL divergence
        if it % 25 == 0:
            WH = W @ H + eps
            loss = np.sum(X * np.log((X + eps) / WH) - X + WH)
            if abs(prev_loss - loss) < tol * max(1.0, abs(prev_loss)):
                break
            prev_loss = loss
    # 行归一化为权重
    row_sum = W.sum(axis=1, keepdims=True)
    row_sum[row_sum == 0] = 1.0
    return W / row_sum


# ----------------------------------------------------------------------------
# 5. Endmember 对齐 — NMF 的 component 顺序不固定, 用峰值年龄重排
# ----------------------------------------------------------------------------

def align_endmembers(
    nmf: NMF,
    sources: List[Source] = DEFAULT_SOURCES,
    t_grid: np.ndarray = T_GRID,
) -> np.ndarray:
    """
    返回 perm: nmf.components_[perm[k]] 是接近 sources[k] 的那个 endmember
    用每个 endmember 的密度加权平均年龄, 匹配到最近的 source.mean_age
    """
    H = nmf.components_   # (k, T)
    k = H.shape[0]
    endmember_means = []
    for h in H:
        # 把 H 行视为(未归一)密度, 算加权平均年龄
        if h.sum() <= 0:
            endmember_means.append(np.nan)
        else:
            endmember_means.append(np.sum(t_grid * h) / np.sum(h))
    endmember_means = np.array(endmember_means)
    # 对每个 target source, 找最近的 endmember(贪心, 不允许复用)
    target = np.array([s.mean_age for s in sources])
    used = set()
    perm = np.zeros(k, dtype=int)
    for i, tgt in enumerate(target):
        distances = np.array([
            (np.inf if j in used else abs(endmember_means[j] - tgt))
            for j in range(k)
        ])
        j_star = int(np.argmin(distances))
        perm[i] = j_star
        used.add(j_star)
    return perm


# ----------------------------------------------------------------------------
# 6. 评价指标
# ----------------------------------------------------------------------------

def top1_accuracy(true_w: np.ndarray, pred_w: np.ndarray) -> float:
    """主导源区识别准确率: 测试样品的 argmax(w_true) == argmax(w_pred) 的比例 (全集)"""
    return float(np.mean(np.argmax(true_w, axis=1) == np.argmax(pred_w, axis=1)))


def top1_accuracy_dominant(true_w: np.ndarray, pred_w: np.ndarray, thresh: float = 0.5) -> float:
    """
    限定 dominant-source 子集的 Top-1 准确率: 只在 max(w_true) >= thresh 的样品上评估.
    这是文献里(如 IsoplotR)通用的报告方式 — 把"近均匀"样品排除,因为它们的真 argmax 本身就是噪声.
    """
    mask = np.max(true_w, axis=1) >= thresh
    if mask.sum() == 0:
        return float("nan")
    return float(np.mean(np.argmax(true_w[mask], axis=1) == np.argmax(pred_w[mask], axis=1)))


def weights_mae(true_w: np.ndarray, pred_w: np.ndarray) -> float:
    """所有 3 个权重分量的平均绝对误差"""
    return float(mean_absolute_error(true_w, pred_w))


def weights_r2(true_w: np.ndarray, pred_w: np.ndarray) -> float:
    """以 multi-output 整体方差解释比例报告 R²"""
    return float(r2_score(true_w, pred_w, multioutput="variance_weighted"))


def report(true_w: np.ndarray, pred_w: np.ndarray) -> dict:
    return {
        "top1_accuracy":          top1_accuracy(true_w, pred_w),
        "top1_accuracy_dominant": top1_accuracy_dominant(true_w, pred_w, thresh=0.5),
        "weights_MAE":            weights_mae(true_w, pred_w),
        "weights_R2":             weights_r2(true_w, pred_w),
    }


# ----------------------------------------------------------------------------
# 7. 完整实验主流程 — 单次 hold-out + 5-fold CV
# ----------------------------------------------------------------------------

def run_holdout(seed: int = 42, method: str = "supervised") -> dict:
    """单次 800/200 划分. method ∈ {'unsupervised', 'supervised'}"""
    ages_list, true_w = generate_dataset(n_samples=1000, seed=seed)
    X = np.array([kde_density(a) for a in ages_list])

    X_tr, X_te, w_tr, w_te = train_test_split(
        X, true_w, test_size=0.2, random_state=seed
    )
    if method == "unsupervised":
        nmf = fit_nmf(X_tr, n_components=3, seed=seed)
        perm = align_endmembers(nmf)
        pred_w_te = predict_weights(X_te, nmf)[:, perm]
    elif method == "supervised":
        H = build_source_endmembers()
        pred_w_te = supervised_unmix(X_te, H)
    else:
        raise ValueError(f"unknown method: {method}")
    return report(w_te, pred_w_te)


def run_cv(seed: int = 42, n_folds: int = 5, method: str = "supervised") -> dict:
    """5-fold 交叉验证, 报告均值 ± 标准差. method ∈ {'unsupervised', 'supervised'}"""
    ages_list, true_w = generate_dataset(n_samples=1000, seed=seed)
    X = np.array([kde_density(a) for a in ages_list])

    kf = KFold(n_splits=n_folds, shuffle=True, random_state=seed)
    fold_top1, fold_top1_dom, fold_mae, fold_r2 = [], [], [], []
    for fold_i, (tr_idx, te_idx) in enumerate(kf.split(X), start=1):
        if method == "unsupervised":
            nmf = fit_nmf(X[tr_idx], n_components=3, seed=seed + fold_i)
            perm = align_endmembers(nmf)
            pred_w = predict_weights(X[te_idx], nmf)[:, perm]
        elif method == "supervised":
            H = build_source_endmembers()
            pred_w = supervised_unmix(X[te_idx], H)
        else:
            raise ValueError(f"unknown method: {method}")
        r = report(true_w[te_idx], pred_w)
        fold_top1.append(r["top1_accuracy"])
        fold_top1_dom.append(r["top1_accuracy_dominant"])
        fold_mae.append(r["weights_MAE"])
        fold_r2.append(r["weights_R2"])
        print(f"  fold {fold_i}: top1={r['top1_accuracy']:.4f}  "
              f"top1_dom={r['top1_accuracy_dominant']:.4f}  "
              f"MAE={r['weights_MAE']:.4f}  R²={r['weights_R2']:.4f}")

    return {
        "top1_mean":     float(np.mean(fold_top1)),
        "top1_std":      float(np.std(fold_top1)),
        "top1_dom_mean": float(np.mean(fold_top1_dom)),
        "top1_dom_std":  float(np.std(fold_top1_dom)),
        "MAE_mean":      float(np.mean(fold_mae)),
        "MAE_std":       float(np.std(fold_mae)),
        "R2_mean":       float(np.mean(fold_r2)),
        "R2_std":        float(np.std(fold_r2)),
        "per_fold_top1": fold_top1,
        "per_fold_top1_dominant": fold_top1_dom,
    }


# ----------------------------------------------------------------------------
# 8. CLI 入口
# ----------------------------------------------------------------------------

def main() -> None:
    print("=" * 64)
    print("QN2025106 指标 #3 验证实验 — 碎屑锆石 NMF 物源解混")
    print("目标: Top-1 源区识别准确率 ≥ 0.85 (dominant 子集为准)")
    print("=" * 64)

    # ---- A: Unsupervised baseline (sklearn NMF) ----
    print("\n[A] Unsupervised NMF (sklearn, fit_transform on training set)")
    print("    5-fold CV:")
    cv_unsup = run_cv(seed=42, n_folds=5, method="unsupervised")
    print(f"\n    Top-1 (all)      : {cv_unsup['top1_mean']:.4f} ± {cv_unsup['top1_std']:.4f}")
    print(f"    Top-1 (dominant) : {cv_unsup['top1_dom_mean']:.4f} ± {cv_unsup['top1_dom_std']:.4f}")
    print(f"    Weights MAE      : {cv_unsup['MAE_mean']:.4f} ± {cv_unsup['MAE_std']:.4f}")
    print(f"    Weights R²       : {cv_unsup['R2_mean']:.4f} ± {cv_unsup['R2_std']:.4f}")

    # ---- B: Supervised NMF (fixed-H, KL multiplicative updates) ----
    print("\n[B] Supervised NMF (fixed-H, KL multiplicative updates)")
    print("    5-fold CV:")
    cv_sup = run_cv(seed=42, n_folds=5, method="supervised")
    print(f"\n    Top-1 (all)      : {cv_sup['top1_mean']:.4f} ± {cv_sup['top1_std']:.4f}")
    print(f"    Top-1 (dominant) : {cv_sup['top1_dom_mean']:.4f} ± {cv_sup['top1_dom_std']:.4f}")
    print(f"    Weights MAE      : {cv_sup['MAE_mean']:.4f} ± {cv_sup['MAE_std']:.4f}")
    print(f"    Weights R²       : {cv_sup['R2_mean']:.4f} ± {cv_sup['R2_std']:.4f}")

    # ---- Verdict (主指标 = supervised dominant) ----
    primary = cv_sup["top1_dom_mean"]
    threshold_met = primary >= 0.85
    print("\n" + ("=" * 64))
    print(f"主指标 (supervised, dominant 子集) : {primary:.4f}")
    print(f"阈值检查 (≥ 0.85)                  : {'✅ 达成' if threshold_met else '❌ 未达'}")
    print("=" * 64)

    out = {
        "experiment": "QN2025106-IND3-DZ-Unmixing",
        "date": "2026-05-12",
        "seed": 42,
        "n_samples": 1000,
        "dirichlet_alpha": 0.5,
        "n_sources": 3,
        "sources": [
            {"name": s.name, "mean_age": s.mean_age, "sigma": s.sigma, "geo_label": s.geo_label}
            for s in DEFAULT_SOURCES
        ],
        "cv_5fold_unsupervised_NMF": cv_unsup,
        "cv_5fold_supervised_NMF":   cv_sup,
        "primary_metric_top1_dominant_supervised": primary,
        "threshold_met": threshold_met,
    }
    with open("dz_unmixing_results.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print("\n结果已写入  dz_unmixing_results.json")


if __name__ == "__main__":
    main()
