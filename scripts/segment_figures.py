# -*- coding: utf-8 -*-
"""必做② 第5步：统计图（中文图规范：雅黑 + unicode_minus=False + 每图配 .caption.md）。

三张图进 outputs/figures/：
  fig1_city_segment_heatmap.png   城市×环节企业数热力图
  fig2_founding_year_hist.png     成立年份分布（1978+）
  fig3_capital_tiers_stack.png    各市规模档结构（百分比堆叠条）
"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

REGION = Path(r"C:\Users\宏宇\Downloads\一键换链脚本包+数据包_新链_v1.5_20260922\脚本总包_产业集群聚类与集群指数\02_集群指数\输入数据\02_区域企业数据.csv")
OUT_DIR = Path(__file__).resolve().parents[1] / "outputs" / "figures"

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei"]
plt.rcParams["axes.unicode_minus"] = False

CAP_ORDER = ["微型≤100万", "小型100-1000万", "中型1000万-1亿", "大型>1亿", "未知"]


def write_caption(name: str, text: str) -> None:
    (OUT_DIR / f"{name}.caption.md").write_text(text.strip() + "\n", encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(REGION, encoding="utf-8-sig", low_memory=False)
    df["_环节"] = df["产业链完整路径"].astype(str).str.split(" > ").str[1]
    df["_成立年"] = pd.to_datetime(df["成立时间"], errors="coerce").dt.year
    cap = pd.to_numeric(df["注册资本"], errors="coerce")

    # ---- 图1：城市×环节热力图 ----
    ct = pd.crosstab(df["所属城市"], df["_环节"])
    ct = ct.loc[ct.sum(axis=1).sort_values(ascending=False).index]
    fig, ax = plt.subplots(figsize=(11, 6))
    im = ax.imshow(ct.values, aspect="auto", cmap="YlGnBu")
    ax.set_xticks(range(len(ct.columns)), ct.columns, rotation=30, ha="right")
    ax.set_yticks(range(len(ct.index)), ct.index)
    for i in range(len(ct.index)):
        for j in range(len(ct.columns)):
            ax.text(j, i, ct.values[i, j], ha="center", va="center", fontsize=7)
    ax.set_title("京津冀各市 × 产业链环节 企业数（老师口径标签）")
    fig.colorbar(im, label="企业数")
    fig.tight_layout()
    fig.savefig(OUT_DIR / "fig1_city_segment_heatmap.png", dpi=150)
    plt.close(fig)
    write_caption("fig1_city_segment_heatmap",
                  "画什么：13市×7环节的企业数热力图，颜色越深企业越多，格内数字为具体家数。\n"
                  "怎么读：看每市的主导环节（最深的格子）与环节的城市分工。\n"
                  "说明：环节为老师口径标签，噪声约42%（抽查估计），结构画像可用、企业级断言不可。\n"
                  "局限：未覆盖环节空白处是真零，不是缺数据。")

    # ---- 图2：成立年份分布 ----
    years = df["_成立年"].dropna()
    years = years[years >= 1978]
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.hist(years, bins=range(1978, 2028), color="#4472C4", edgecolor="white", linewidth=0.3)
    ax.set_title("京津冀新能源汽车链企业成立年份分布")
    ax.set_xlabel("成立年份")
    ax.set_ylabel("企业数")
    ax.axvline(2015, color="gray", ls="--", lw=1)
    ax.text(2015.3, ax.get_ylim()[1] * 0.9, "2015", color="gray")
    fig.tight_layout()
    fig.savefig(OUT_DIR / "fig2_founding_year_hist.png", dpi=150)
    plt.close(fig)
    write_caption("fig2_founding_year_hist",
                  "画什么：区域 35,953 家链上企业的成立年份直方图（1978 年起，数据截止 2026-08）。\n"
                  "怎么读：峰的位置=扩张期；2026 年矮柱是部分年（非全年）。\n"
                  "说明：存活者偏差——只有至今仍存续的企业，读不出历年真实新设与退出。\n"
                  "局限：同左。")

    # ---- 图3：各市规模档结构（百分比堆叠） ----
    def tier(v):
        if pd.isna(v) or v <= 0:
            return "未知"
        for name, lo, hi in [("微型≤100万", -1, 100), ("小型100-1000万", 100, 1000),
                             ("中型1000万-1亿", 1000, 10000), ("大型>1亿", 10000, None)]:
            if v > lo and (hi is None or v <= hi):
                return name
    df["_规模档"] = cap.apply(tier)
    ct2 = pd.crosstab(df["所属城市"], df["_规模档"], normalize="index")
    ct2 = ct2.reindex(columns=CAP_ORDER, fill_value=0)
    ct2 = ct2.loc[df["所属城市"].value_counts().index]
    colors = ["#A9D18E", "#4472C4", "#ED7D31", "#C00000", "#BFBFBF"]
    fig, ax = plt.subplots(figsize=(11, 6))
    bottom = pd.Series([0.0] * len(ct2), index=ct2.index)
    for col, c in zip(ct2.columns, colors):
        ax.bar(ct2.index, ct2[col], bottom=bottom, label=col, color=c)
        bottom += ct2[col]
    ax.set_title("各市注册资本规模档结构（占比）——注册资本≠营收")
    ax.set_ylabel("占比")
    ax.legend(title="规模档（按注册资本）", bbox_to_anchor=(1.01, 1), loc="upper left")
    plt.setp(ax.get_xticklabels(), rotation=30, ha="right")
    fig.tight_layout()
    fig.savefig(OUT_DIR / "fig3_capital_tiers_stack.png", dpi=150)
    plt.close(fig)
    write_caption("fig3_capital_tiers_stack",
                  "画什么：各市企业按注册资本分档（微/小/中/大/未知）的占比堆叠条。\n"
                  "怎么读：红色（大型>1亿）越厚，该市资本密集度越高；灰色=注册资本缺失或非正。\n"
                  "说明：注册资本是规模代理，不等于营收或市值（作业红线）。\n"
                  "局限：约3%企业注册资本缺失，计入未知档。")

    print("已生成 3 图 + 3 图说 →", OUT_DIR)


if __name__ == "__main__":
    main()
