# -*- coding: utf-8 -*-
"""必做② 第4步：三张统计图 + 图说（fig1 城市×环节热力 / fig2 成立年份直方 / fig3 规模结构堆叠）。"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from seg_rules import MASTER, OUT_DIR, CURRENT_YEAR, CAP_TIERS, norm_city, primary_seg

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei"]
plt.rcParams["axes.unicode_minus"] = False
OUT = OUT_DIR / "figures"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(MASTER, encoding="utf-8-sig", dtype=str)
    df["_市"] = df.apply(lambda r: norm_city(r["所属省份"], r["所属城市"]), axis=1)
    df["_环节"] = df["产业链环节"].map(primary_seg)
    df["_年"] = pd.to_datetime(df["成立时间"], errors="coerce").dt.year
    cap = pd.to_numeric(df["注册资本"], errors="coerce")
    is_rmb = df["注册资本币种"].isin(["人民币", ""])
    cap_valid = cap.where(is_rmb & (cap > 0))

    # fig1 城市×环节热力
    ct = pd.crosstab(df["_市"], df["_环节"])
    ct = ct.loc[ct.sum(axis=1).sort_values(ascending=False).index]
    fig, ax = plt.subplots(figsize=(8, 6))
    im = ax.imshow(ct.values, cmap="YlOrRd", aspect="auto")
    ax.set_xticks(range(len(ct.columns)), ct.columns)
    ax.set_yticks(range(len(ct.index)), ct.index)
    for i in range(len(ct.index)):
        for j in range(len(ct.columns)):
            ax.text(j, i, f"{ct.values[i, j]:,}", ha="center", va="center", fontsize=8)
    ax.set_title("京津冀各市 × 环节 企业数（新一代信息技术/网络安全与工业互联网）")
    fig.colorbar(im, label="企业数（家）")
    fig.tight_layout()
    fig.savefig(OUT / "fig1_city_segment_heatmap.png", dpi=150)
    plt.close(fig)

    # fig2 成立年份直方
    fig, ax = plt.subplots(figsize=(9, 4.5))
    years = df["_年"].dropna()
    ax.hist(years, bins=range(1990, CURRENT_YEAR + 2), color="#4472C4")
    ax.set_title("企业成立年份分布（数据快照 2026-08-10）")
    ax.set_xlabel("成立年份")
    ax.set_ylabel("企业数（家）")
    fig.tight_layout()
    fig.savefig(OUT / "fig2_founding_year_hist.png", dpi=150)
    plt.close(fig)

    # fig3 规模档堆叠（城市×规模档占比，仅人民币有效值）
    def tier(v):
        if pd.isna(v):
            return "未知"
        for name, lo, hi in CAP_TIERS:
            if v >= lo and (hi is None or v < hi):
                return name
        return "未知"
    df["_规模档"] = cap_valid.apply(tier)
    order = [t[0] for t in CAP_TIERS] + ["未知"]
    tab = pd.crosstab(df["_市"], df["_规模档"], normalize="index")[order]
    tab = tab.loc[ct.index]
    fig, ax = plt.subplots(figsize=(9, 5.5))
    bottom = None
    colors = ["#A6CEE3", "#1F78B4", "#08306B", "#08519C", "#BDBDBD"]
    for k, col in enumerate(order):
        vals = tab[col].values
        ax.bar(tab.index, vals, bottom=bottom, label=col, color=colors[k])
        bottom = vals if bottom is None else bottom + vals
    ax.set_title("各市注册资本规模结构（占比；注册资本≠营收，非人民币与缺失计'未知'）")
    ax.set_ylabel("占比")
    ax.legend(fontsize=8)
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
    fig.tight_layout()
    fig.savefig(OUT / "fig3_capital_tiers_stack.png", dpi=150)
    plt.close(fig)

    caps = {
        "fig1_city_segment_heatmap.caption.md":
            "画什么：京津冀各市×4 环节的企业数热力图，颜色越深企业越多，格内数字为具体家数。\n"
            "怎么读：看每市的主导环节（最深格子）与环节的城市分工（北京全环节 dominant，河北各市以配套服务/下游为主）。\n"
            "说明：环节为数据原生标签（主口径），已知'工业互联网平台''检测评估'两桶口径偏宽，结构画像可用、企业级断言需抽查。\n"
            "局限：未覆盖/多标签企业按主环节计；北京天津按直辖市归并区县级。\n",
        "fig2_founding_year_hist.caption.md":
            "画什么：38,553 家链上企业的成立年份直方图（1990 年至数据快照 2026-08-10）。\n"
            "怎么读：看创业潮节奏——峰值对应政策与市场周期；近 5 年（<5 年档 6,949 家）为新进入力量。\n"
            "说明：成立时间 0 缺失（必做①）；年份按公历年计，未做存续筛选（经营状态 90.7% 缺失为源数据边界）。\n"
            "局限：注册成立≠实际开始经营；快照日前当年新设存在滞后登记低估。\n",
        "fig3_capital_tiers_stack.caption.md":
            "画什么：各市注册资本规模档占比堆叠图（微型≤100万/小型100-1000万/中型1000万-1亿/大型>1亿/未知）。\n"
            "怎么读：深色段越长中大型企业越多；'未知'段为非人民币或注册资本缺失/非正值。\n"
            "说明：注册资本≠营收，仅作可观测规模代理（课程红线）；非人民币 789 家（美元为主）计入'未知'未折算。\n"
            "局限：注册资本认缴制下虚高常见；规模档边界为分析约定而非官方标准。\n",
    }
    for name, text in caps.items():
        (OUT / name).write_text(text, encoding="utf-8")
    print("3 张图 + 3 图说 已写入", OUT)


if __name__ == "__main__":
    main()
