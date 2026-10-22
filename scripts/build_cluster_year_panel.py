# -*- coding: utf-8 -*-
"""选做⑤ 集群生长模拟与预测 · 第1步：集群—年份面板。

三个状态空间在面板上连接：
  A 结构空间：集群 4 环节构成（当前成员口径，作为结构特征）
  B 规模-年龄空间：每年新设数、累计存量、5 年内新设占比
  C 空间-密度空间：集群最小边界面积（29 号表）、密度=存量/面积
口径：23 个正式集群（19 核心 C01–C19 + 4 培育 E01–E04）；NOISE/Q01/未参与不入面板；
  进入=当年新注册（成立年份）；退出不可得（经营状态 90.7% 缺失，见方法说明）。
输出 outputs/cluster_year_panel.csv（长表：集群×年份）与 panel_summary.md
"""
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
MODULE01 = ROOT.parent / "01_必做_感知模块" / "outputs" / "master_clean.csv"
MEMBER = ROOT.parent / "03_必做_集群识别模块" / "outputs" / "cluster_membership_standardized.csv"
C29 = ROOT.parent / "03_必做_集群识别模块" / "outputs" / "29_核心集群信息汇总与相邻园区.csv"
OUT = ROOT / "outputs"

Y0, Y1 = 1990, 2025
sys.path.insert(0, str(ROOT.parent / "02_必做_企业分析模块" / "scripts"))
from seg_rules import primary_seg  # noqa: E402


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    m = pd.read_csv(MODULE01, encoding="utf-8-sig", dtype=str)
    mem = pd.read_csv(MEMBER, encoding="utf-8-sig", dtype=str)
    c29 = pd.read_csv(C29, encoding="utf-8-sig", dtype=str)

    formal = mem[mem["集群编号"].str.match(r"^(C|E)\d+$") & mem["集群状态"].eq("正式")].copy()
    g = m.merge(formal[["企业标识", "集群编号", "集群层级"]], on="企业标识", how="inner")
    g["_年"] = pd.to_datetime(g["成立时间"], errors="coerce").dt.year
    g["_环节"] = g["产业链环节"].map(primary_seg)
    g = g[g["_年"].between(Y0, Y1)]

    # A 结构空间：集群环节构成（成员口径）
    seg_share = (pd.crosstab(g["集群编号"], g["_环节"], normalize="index")
                 .reindex(columns=["上游", "中游", "下游", "配套服务"], fill_value=0.0)
                 .round(4))
    seg_share.columns = [f"环节占比_{c}" for c in seg_share.columns]

    # C 空间-密度空间：边界面积（29 表仅核心集群；培育型缺记为 NaN）
    area = c29.set_index("集群编号")["最小边界面积(平方公里)"].astype(float)

    # B 规模-年龄：逐年新设与存量
    entry = pd.crosstab(g["集群编号"], g["_年"]).reindex(columns=range(Y0, Y1 + 1), fill_value=0)
    rows = []
    for c in entry.index:
        stock = 0.0
        for y in range(Y0, Y1 + 1):
            e = int(entry.loc[c, y])
            stock += e
            recent5 = int(entry.loc[c, max(Y0, y - 4):y].sum())
            rows.append({
                "集群编号": c, "年份": y, "当年新设": e, "累计存量": int(stock),
                "近5年新设占比": round(recent5 / stock, 4) if stock else None,
                "新设率(当年/存量)": round(e / stock, 4) if stock else None,
            })
    panel = pd.DataFrame(rows)
    tier = formal.drop_duplicates("集群编号").set_index("集群编号")["集群层级"]
    panel["集群层级"] = panel["集群编号"].map(tier)
    panel["面积平方公里"] = panel["集群编号"].map(area)
    panel["密度(存量/面积)"] = (panel["累计存量"] / panel["面积平方公里"]).round(3)
    panel = panel.merge(seg_share, left_on="集群编号", right_index=True, how="left")
    panel.to_csv(OUT / "cluster_year_panel.csv", index=False, encoding="utf-8-sig")

    # 摘要与交叉核验：全区域逐年新设合计 应≈ 必做② fig2 直方图
    tot = panel.groupby("年份")["当年新设"].sum()
    n_clusters = panel["集群编号"].nunique()
    lines = [
        "# 集群—年份面板 · 摘要与核验\n",
        f"- 面板：{n_clusters} 个正式集群 × {Y0}–{Y1}，{len(panel):,} 行（cluster_year_panel.csv）",
        f"- 集群企业合计（1990–2025 新设累计）：{int(tot.sum()):,}（应≈正式成员 32,405 − 1990 前成立者）",
        "\n## 全区域逐年新设（面板合计）",
        tot.to_string(),
        "\n## Top5 集群累计存量轨迹（2015/2020/2025）",
    ]
    for c in ["C01", "C02", "C03", "C04", "C05"]:
        s = panel[panel["集群编号"] == c].set_index("年份")["累计存量"]
        lines.append(f"- {c}（{tier.get(c, '')}）：2015={int(s.get(2015, 0)):,}，"
                     f"2020={int(s.get(2020, 0)):,}，2025={int(s.get(2025, 0)):,}")
    lines += [
        "\n## 结构空间速览（环节占比最高者）",
        seg_share.idxmax(axis=1).value_counts().to_string(),
        "\n备注：退出/迁出不可得（经营状态 90.7% 缺失）；培育型 E01–E04 无 29 表面积，密度列为空。",
    ]
    (OUT / "panel_summary.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
