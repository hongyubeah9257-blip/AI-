# -*- coding: utf-8 -*-
"""选做⑤ 第3步：三情景模拟 2026–2028 + 波动带 + 轨迹图。

骨架：朴素基线（测试期赢家）——各集群新设维持 2025 年水平（基准情景）。
情景分化（规则透明，方向来自选择压力函数模型 C 的系数符号，幅度为分析约定）：
  - 基准：entry 保持 2025 水平
  - 配套增强：上游占比前 1/3 的集群 entry ×1.10/年（复利的政策增强）
  - 容量收紧：密度前 1/3 的集群 entry ×0.80/年（拥挤惩罚；培育型无密度不罚）
波动带：朴素基线测试期相对残差自助抽样（200 条路径），取 10–90% 分位。
输出 outputs/scenario_projection.csv、fig_growth_scenarios.png（+图说）
"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"
plt.rcParams["font.sans-serif"] = ["Microsoft YaHei"]
plt.rcParams["axes.unicode_minus"] = False

YEARS_SIM = [2026, 2027, 2028]
N_PATHS = 200
SEED = 42


def main() -> None:
    panel = pd.read_csv(OUT / "cluster_year_panel.csv", encoding="utf-8-sig")
    p25 = panel[panel["年份"] == 2025].set_index("集群编号")

    # 朴素基线测试期相对残差（复用第2步口径：朴素=下年=当年）
    p = panel.sort_values(["集群编号", "年份"])
    p["上年新设"] = p.groupby("集群编号")["当年新设"].shift(1)
    pt = p[(p["年份"] >= 2022) & p["上年新设"].notna() & (p["集群层级"] == "核心集群")]
    rel_res = ((pt["当年新设"] - pt["上年新设"]) / pt["上年新设"].clip(lower=1)).clip(-0.9, 2.0)

    up_thr = p25["环节占比_上游"].quantile(2 / 3)
    den_thr = p25["密度(存量/面积)"].quantile(2 / 3)
    rng = np.random.default_rng(SEED)

    scenarios = {"基准": 1.0, "配套增强": None, "容量收紧": None}
    rows = []
    for c, r in p25.iterrows():
        entry0 = float(r["当年新设"])
        stock0 = float(r["累计存量"])
        is_up = r["环节占比_上游"] >= up_thr
        is_dense = (not pd.isna(r["密度(存量/面积)"])) and r["密度(存量/面积)"] >= den_thr
        for sc in scenarios:
            entry = entry0
            stock = stock0
            for y in YEARS_SIM:
                if sc == "配套增强" and is_up:
                    entry *= 1.10
                if sc == "容量收紧" and is_dense:
                    entry *= 0.80
                stock += entry
                rows.append({"集群编号": c, "集群层级": r["集群层级"], "情景": sc, "年份": y,
                             "新设": round(entry), "累计存量": round(stock),
                             "触发规则": ("上游占比前1/3×1.10" if sc == "配套增强" and is_up else
                                       "密度前1/3×0.80" if sc == "容量收紧" and is_dense else "")})

        # 波动带（仅基准情景，自助相对残差）
        paths = np.zeros((N_PATHS, len(YEARS_SIM)))
        for k in range(N_PATHS):
            e, s = entry0, stock0
            for j in range(len(YEARS_SIM)):
                e = max(0.0, e * (1 + rng.choice(rel_res)))
                s += e
                paths[k, j] = s
        for j, y in enumerate(YEARS_SIM):
            rows.append({"集群编号": c, "集群层级": r["集群层级"], "情景": "基准_波动带", "年份": y,
                         "新设": None, "累计存量": None,
                         "触发规则": f"p10={np.percentile(paths[:, j], 10):.0f}|"
                                     f"p50={np.percentile(paths[:, j], 50):.0f}|"
                                     f"p90={np.percentile(paths[:, j], 90):.0f}"})

    proj = pd.DataFrame(rows)
    proj.to_csv(OUT / "scenario_projection.csv", index=False, encoding="utf-8-sig")

    # 图：Top4 集群轨迹（2015–2025 实际 + 三情景 + 基准波动带）
    top = ["C01", "C02", "C03", "C04"]
    hist = panel[panel["集群编号"].isin(top) & panel["年份"].between(2015, 2025)]
    fig, axes = plt.subplots(2, 2, figsize=(11, 7), sharex=False)
    colors = {"基准": "#4472C4", "配套增强": "#70AD47", "容量收紧": "#C00000"}
    for ax, c in zip(axes.ravel(), top):
        h = hist[hist["集群编号"] == c]
        ax.plot(h["年份"], h["累计存量"], "k-o", ms=3, label="实际")
        band = proj[(proj["集群编号"] == c) & (proj["情景"] == "基准_波动带")]
        p10 = [float(x.split("|")[0][4:]) for x in band["触发规则"]]
        p90 = [float(x.split("|")[2][4:]) for x in band["触发规则"]]
        ax.fill_between(YEARS_SIM, p10, p90, color="#4472C4", alpha=0.15, label="基准10–90%带")
        for sc, col in colors.items():
            d = proj[(proj["集群编号"] == c) & (proj["情景"] == sc)]
            ax.plot([2025] + YEARS_SIM, [p25.loc[c, "累计存量"]] + d["累计存量"].tolist(),
                    "--o", ms=3, color=col, label=sc)
        ax.set_title(c)
        ax.set_xticks([2015, 2020, 2025, 2028])
        ax.legend(fontsize=7)
    fig.suptitle("核心集群累计存量：实际(2015–2025)与三情景模拟(2026–2028)")
    fig.tight_layout()
    fig.savefig(OUT / "fig_growth_scenarios.png", dpi=150)
    plt.close(fig)

    (OUT / "fig_growth_scenarios.caption.md").write_text(
        "画什么：C01–C04 四个核心集群的累计存量轨迹——2015–2025 实际值（黑线）与 2026–2028 三情景模拟（虚线），蓝色阴影为基准情景 10–90% 自助波动带。\n"
        "怎么读：基准=维持 2025 年新设水平；配套增强=上游占比前 1/3 集群新设 ×1.10/年；容量收紧=密度前 1/3 集群新设 ×0.80/年。\n"
        "说明：骨架为朴素基线（测试期赢家，见 selection_pressure_model.md 模型对比）；情景幅度为分析约定，方向来自选择压力函数系数符号；波动带为测试期相对残差自助抽样（200 路径）。\n"
        "局限：退出不可得（经营状态 90.7% 缺失）；3 年短窗投影，不宣称预测集群存活周期；点预测区间随年限迅速放宽，读趋势不读精确值。\n",
        encoding="utf-8")

    print(f"规则阈值：上游占比前1/3 ≥ {up_thr:.3f}；密度前1/3 ≥ {den_thr:.1f}")
    print("\n== 2028 年三情景累计存量（Top6 集群）==")
    p28 = proj[(proj["年份"] == 2028) & (proj["情景"].isin(colors))]
    piv = p28.pivot_table(index="集群编号", columns="情景", values="累计存量")
    print(piv.head(6).to_string())
    print("\n已写入 scenario_projection.csv 与 fig_growth_scenarios.png(+图说)")


if __name__ == "__main__":
    main()
