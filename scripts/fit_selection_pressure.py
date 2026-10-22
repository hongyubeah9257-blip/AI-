# -*- coding: utf-8 -*-
"""选做⑤ 第2步：选择压力函数估计 + 朴素基线对比（时间切分，禁用未来信息）。

目标变量：下一期新设率 = 当年新设/存量（集群的"被选择强度"）。
特征（t 年可观测）：log(累计存量)、上游占比、中游占比、近5年新设占比、年份趋势。
模型：朴素基线（下一期=本期率）vs  pooled OLS（19 个核心集群；培育型面积缺失不参与拟合）。
切分：目标年 ≤2021 训练，2022–2025 测试。误差以"新设数"计（率×存量还原）。
输出 outputs/selection_pressure_model.md（系数+判读）与 forecast_metrics.csv
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"
FEATURES = ["log存量", "环节占比_上游", "环节占比_中游", "近5年新设占比", "年份"]
TRAIN_END, TEST_START = 2021, 2022


def build_samples(panel: pd.DataFrame) -> pd.DataFrame:
    p = panel.sort_values(["集群编号", "年份"]).copy()
    p["log存量"] = np.log10(p["累计存量"].clip(lower=1))
    p["目标率_下一年"] = p.groupby("集群编号")["新设率(当年/存量)"].shift(-1)
    p["目标新设_下一年"] = p.groupby("集群编号")["当年新设"].shift(-1)
    p["目标年份"] = p["年份"] + 1
    return p[p["目标率_下一年"].notna() & (p["累计存量"] > 0)]


def ols(X: np.ndarray, y: np.ndarray):
    X1 = np.column_stack([np.ones(len(X)), X])
    beta, *_ = np.linalg.lstsq(X1, y, rcond=None)
    return beta


def main() -> None:
    panel = pd.read_csv(OUT / "cluster_year_panel.csv", encoding="utf-8-sig")
    core = panel[panel["集群层级"] == "核心集群"].copy()
    s = build_samples(core)

    train = s[s["目标年份"] <= TRAIN_END]
    test = s[s["目标年份"] >= TEST_START]

    beta = ols(train[FEATURES].values.astype(float), train["目标率_下一年"].values.astype(float))
    FEATURES_B = ["新设率(当年/存量)"] + FEATURES
    beta_b = ols(train[FEATURES_B].values.astype(float), train["目标率_下一年"].values.astype(float))
    # 模型 C：水平量 AR（对数刻度）log1p(下年新设) ~ log1p(当年新设) + 状态 + 年份
    FEAT_C = ["log当年新设", "log存量", "环节占比_上游", "环节占比_中游", "近5年新设占比", "年份"]
    for df in (train, test):
        df["log当年新设"] = np.log1p(df["当年新设"].astype(float))
        df["log目标新设"] = np.log1p(df["目标新设_下一年"].astype(float))
    beta_c = ols(train[FEAT_C].values.astype(float), train["log目标新设"].values.astype(float))

    def predict(df, beta, feats):
        X1 = np.column_stack([np.ones(len(df)), df[feats].values.astype(float)])
        return (X1 @ beta).clip(0)  # 率不为负

    def predict_c(df):
        X1 = np.column_stack([np.ones(len(df)), df[FEAT_C].values.astype(float)])
        return np.expm1(X1 @ beta_c).clip(0)

    for name, df in [("train", train), ("test", test)]:
        df["预测率_模型"] = predict(df, beta, FEATURES)
        df["预测率_AR状态"] = predict(df, beta_b, FEATURES_B)
        df["预测新设_模型"] = df["预测率_模型"] * df["累计存量"]
        df["预测新设_AR状态"] = df["预测率_AR状态"] * df["累计存量"]
        df["预测新设_logAR"] = predict_c(df)
        df["预测新设_朴素"] = df["新设率(当年/存量)"] * df["累计存量"]  # 下一期=本期

    def metrics(df):
        y = df["目标新设_下一年"].astype(float)
        out = {}
        for m in ["模型", "AR状态", "logAR", "朴素"]:
            e = (df[f"预测新设_{m}"] - y).abs()
            out[m + "_MAE"] = round(e.mean(), 1)
            out[m + "_RMSE"] = round(float(np.sqrt((e ** 2).mean())), 1)
        return out

    m_tr, m_te = metrics(train), metrics(test)
    met = pd.DataFrame([
        {"期间": f"训练(–{TRAIN_END})", **m_tr},
        {"期间": f"测试({TEST_START}–2025)", **m_te},
    ])
    met.to_csv(OUT / "forecast_metrics.csv", index=False, encoding="utf-8-sig")

    r2 = 1 - ((train["目标率_下一年"] - train["预测率_模型"]) ** 2).sum() / \
        ((train["目标率_下一年"] - train["目标率_下一年"].mean()) ** 2).sum()
    r2_b = 1 - ((test["目标率_下一年"] - test["预测率_AR状态"]) ** 2).sum() / \
        ((test["目标率_下一年"] - test["目标率_下一年"].mean()) ** 2).sum()

    coef_lines = [f"- {name}：{b:+.5f}" for name, b in zip(["截距"] + FEAT_C, beta_c)]
    read = {
        "log当年新设": "AR(1) 水平惯性（接近 1=强路径依赖）",
        "log存量": "规模效应（负=拥挤/增长放缓，正=累积优势）",
        "环节占比_上游": "上游吸引力（正=环境奖励上游集聚）",
        "环节占比_中游": "中游吸引力（相对下游/配套参照系）",
        "近5年新设占比": "集群年轻化（正=年轻集群继续高增长）",
        "年份": "区域时间趋势（负=全区域新设退潮）",
    }
    winner = min([(m_te["朴素_MAE"], "朴素基线"), (m_te["AR状态_MAE"], "率AR+状态模型"),
                  (m_te["logAR_MAE"], "对数水平AR+状态模型")], key=lambda x: x[0])[1]
    md = [
        "# 选择压力函数 · 估计结果（pooled OLS，19 核心集群）\n",
        "> 目标：下一年（新设率或新设数）。特征均为当年可观测，不用未来信息。",
        "> 模型 A＝仅状态特征（率）；模型 B＝率 AR(1)+状态；模型 C＝对数水平 AR(1)+状态（最终采用 C 的系数刻画选择压力方向）。",
        f"> 训练：目标年 ≤{TRAIN_END}（{len(train)} 样本）；测试：{TEST_START}–2025（{len(test)} 样本）\n",
        "## 系数与判读（模型 C）",
        *coef_lines,
        "",
        *[f"  · {k}：{v}" for k, v in read.items()],
        f"\n模型 A 训练期 R² = {r2:.3f}；模型 B 测试期 R² = {r2_b:.3f}",
        "\n## 误差（新设数口径，MAE/RMSE）",
        met.to_string(index=False),
        "\n## 与朴素基线对比",
        f"- 测试期：朴素 MAE {m_te['朴素_MAE']}｜模型A(率-状态) {m_te['模型_MAE']}｜模型B(率AR) {m_te['AR状态_MAE']}｜模型C(对数水平AR) {m_te['logAR_MAE']}",
        f"- **预测骨架采用：{winner}**（选择压力方向仍以模型 C 系数作结构性判读，不作精确点预测）。",
    ]
    (OUT / "selection_pressure_model.md").write_text("\n".join(md), encoding="utf-8")
    # 供情景模拟：落盘系数（模型 C）
    pd.DataFrame({"项": ["截距"] + FEAT_C, "系数": beta_c}).to_csv(
        OUT / "selection_pressure_coefficients.csv", index=False, encoding="utf-8-sig")
    print("\n".join(md))


if __name__ == "__main__":
    main()
