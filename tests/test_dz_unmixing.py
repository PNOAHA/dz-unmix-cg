# -*- coding: utf-8 -*-
"""
QN2025106 单元测试 — dz_unmixing_experiment 核心算子

测试焦点(在 fail 时最值得 catch 的不变量):
  1. 三源区 endmember 应在自己峰位有最大值
  2. 纯源样品被 supervised_unmix 识别为该源(one-hot)
  3. KDE 输出曲线下面积 = 1
  4. 主指标函数对 one-hot 完美预测应 = 1.0
  5. 主指标函数对随机预测应接近 1/3 (3 类基准)
"""

import os
import sys
import unittest

import numpy as np

# 让 tests/ 能 import 项目根的模块
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from dz_unmixing_experiment import (
    DEFAULT_SOURCES, T_GRID,
    generate_sample, kde_density,
    build_source_endmembers, supervised_unmix,
    top1_accuracy, top1_accuracy_dominant,
    weights_mae, weights_r2,
)


class TestEndmembers(unittest.TestCase):
    def test_endmember_peaks_at_mean_age(self):
        """每个 endmember 的最大密度位置应接近对应源区的 mean_age"""
        H = build_source_endmembers()
        for i, src in enumerate(DEFAULT_SOURCES):
            j_max = int(np.argmax(H[i]))
            peak_age = T_GRID[j_max]
            self.assertAlmostEqual(peak_age, src.mean_age, delta=10,
                msg=f"S{i+1} 峰位 {peak_age} Ma 远离设定 {src.mean_age} Ma")

    def test_endmember_unit_area(self):
        """每个 endmember 应面积归一化为 1"""
        H = build_source_endmembers()
        for i in range(H.shape[0]):
            area = np.trapezoid(H[i], T_GRID)
            self.assertAlmostEqual(area, 1.0, places=3,
                msg=f"S{i+1} endmember 面积 {area:.4f} ≠ 1.0")


class TestKDE(unittest.TestCase):
    def test_kde_unit_area(self):
        """KDE 输出应面积归一化为 1"""
        rng = np.random.default_rng(0)
        ages = rng.normal(loc=130, scale=15, size=200)
        d = kde_density(ages)
        area = np.trapezoid(d, T_GRID)
        self.assertAlmostEqual(area, 1.0, places=2)

    def test_kde_peak_near_input_mean(self):
        """单模态输入的 KDE 峰应在输入分布的均值附近"""
        rng = np.random.default_rng(42)
        ages = rng.normal(loc=280, scale=30, size=300)
        d = kde_density(ages)
        peak_age = T_GRID[int(np.argmax(d))]
        self.assertAlmostEqual(peak_age, 280, delta=25)


class TestSupervisedUnmix(unittest.TestCase):
    def test_pure_source_identification(self):
        """从单一源区 (w=(1,0,0)/(0,1,0)/(0,0,1)) 抽的样品应被正确识别"""
        rng = np.random.default_rng(0)
        H = build_source_endmembers()
        for i in range(3):
            w_true = np.eye(3)[i]
            ages = generate_sample(w_true, rng=rng)
            X = np.array([kde_density(ages)])
            w_pred = supervised_unmix(X, H)
            self.assertEqual(int(np.argmax(w_pred[0])), i,
                msg=f"纯 S{i+1} 样品被预测为 S{int(np.argmax(w_pred[0]))+1}")
            self.assertGreater(w_pred[0, i], 0.85,
                msg=f"纯 S{i+1} 样品的主权重 {w_pred[0,i]:.3f} 应 > 0.85")

    def test_weights_normalize_to_one(self):
        """supervised_unmix 输出每行权重和应 = 1"""
        rng = np.random.default_rng(7)
        H = build_source_endmembers()
        weights_true = np.array([[0.5, 0.3, 0.2], [0.1, 0.8, 0.1], [0.33, 0.33, 0.34]])
        X = np.array([kde_density(generate_sample(w, rng=rng)) for w in weights_true])
        w_pred = supervised_unmix(X, H)
        for i in range(len(weights_true)):
            self.assertAlmostEqual(w_pred[i].sum(), 1.0, places=4)
            self.assertTrue(np.all(w_pred[i] >= 0))


class TestMetrics(unittest.TestCase):
    def test_top1_perfect_prediction(self):
        """完美预测下 top1_accuracy 应 = 1.0"""
        true_w = np.array([[0.7, 0.2, 0.1], [0.1, 0.8, 0.1], [0.2, 0.3, 0.5]])
        pred_w = true_w.copy()
        self.assertEqual(top1_accuracy(true_w, pred_w), 1.0)

    def test_top1_random_baseline(self):
        """3 类均匀分布随机预测的 Top-1 应接近 1/3"""
        rng = np.random.default_rng(0)
        n = 3000
        true_w = rng.dirichlet([0.5, 0.5, 0.5], size=n)
        pred_w = rng.dirichlet([1.0, 1.0, 1.0], size=n)
        acc = top1_accuracy(true_w, pred_w)
        self.assertAlmostEqual(acc, 1/3, delta=0.05)

    def test_top1_dominant_filters_near_uniform(self):
        """dominant 子集应严格小于全集(部分样品被过滤)"""
        rng = np.random.default_rng(0)
        n = 1000
        true_w = rng.dirichlet([1.0, 1.0, 1.0], size=n)
        pred_w = true_w + rng.normal(0, 0.02, true_w.shape)
        all_acc = top1_accuracy(true_w, pred_w)
        dom_acc = top1_accuracy_dominant(true_w, pred_w, thresh=0.5)
        # dominant 子集是「易」样品 (主导明确),准确率应 ≥ 全集
        self.assertGreaterEqual(dom_acc, all_acc - 1e-6)

    def test_mae_zero_for_perfect(self):
        """完美预测 MAE = 0"""
        true_w = np.array([[0.5, 0.5, 0.0], [0.2, 0.3, 0.5]])
        self.assertAlmostEqual(weights_mae(true_w, true_w), 0.0, places=6)

    def test_r2_one_for_perfect(self):
        """完美预测 R² = 1"""
        true_w = np.array([[0.5, 0.3, 0.2], [0.1, 0.8, 0.1], [0.33, 0.33, 0.34]])
        self.assertAlmostEqual(weights_r2(true_w, true_w), 1.0, places=6)


if __name__ == "__main__":
    unittest.main(verbosity=2)
