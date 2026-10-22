# -*- coding: utf-8 -*-
"""必做② 第3步：地区统计（城市×环节×年龄×规模）+ 全国对照。

口径声明（作业红线）：
  - 环节用数据原生口径（全覆盖），已知两大桶口径偏宽（见词表），结论按"结构画像"使用；
  - 注册资本 ≠ 营收，仅作可观测规模代理；非人民币与缺失/非正值单列"未知"档；
  - 北京/天津的区县级"所属城市"归并为直辖市；排序维度一律注明来源列。
输出 outputs/stats/ 下 6 张表。
"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from seg_rules import (MASTER, NATIONAL, OUT_DIR, CURRENT_YEAR, CAP_TIERS,
                       AGE_BINS, norm_city, primary_seg)

OUT = OUT_DIR / "stats"


def bin_value(v, bins):
    if v is None or pd.isna(v):
        return None
    for name, lo, hi in bins:
        if v >= lo and (hi is None or v < hi):
            return name
    return None


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(MASTER, encoding="utf-8-sig", dtype=str)
    df["_市"] = df.apply(lambda r: norm_city(r["所属省份"], r["所属城市"]), axis=1)
    df["_环节"] = df["产业链环节"].map(primary_seg)
    df["_年龄"] = CURRENT_YEAR - pd.to_datetime(df["成立时间"], errors="coerce").dt.year
    cap = pd.to_numeric(df["注册资本"], errors="coerce")
    is_rmb = df["注册资本币种"].isin(["人民币", ""])
    cap_valid = cap.where(is_rmb & (cap > 0))
    df["_规模档"] = cap_valid.apply(lambda v: bin_value(v, CAP_TIERS) if pd.notna(v) else "未知")
    df["_年龄档"] = df["_年龄"].apply(lambda v: bin_value(v, AGE_BINS))
    df["_评分"] = pd.to_numeric(df["综合能力评分"], errors="coerce")
    n = len(df)

    ct = pd.crosstab(df["_市"], df["_环节"], margins=True, margins_name="合计")
    ct.to_csv(OUT / "city_segment_crosstab.csv", encoding="utf-8-sig")

    rows = []
    for city, g in df.groupby("_市"):
        top_seg = g["_环节"].value_counts()
        rows.append({
            "城市": city, "企业数": len(g), "占区域比": f"{len(g) / n:.1%}",
            "年龄中位数": g["_年龄"].median(),
            "注册资本中位数(万元·仅人民币)": cap_valid.loc[g.index].dropna().median() if (cap_valid.loc[g.index] > 0).any() else None,
            "第一环节": top_seg.index[0], "第一环节占比": f"{top_seg.iloc[0] / len(g):.1%}",
            "第二环节": top_seg.index[1] if len(top_seg) > 1 else "",
        })
    summ = pd.DataFrame(rows).sort_values("企业数", ascending=False)
    summ.to_csv(OUT / "city_summary.csv", index=False, encoding="utf-8-sig")

    pd.crosstab(df["_市"], df["_年龄档"], normalize="index").round(3).to_csv(
        OUT / "age_structure_by_city.csv", encoding="utf-8-sig")
    pd.crosstab(df["_市"], df["_规模档"], normalize="index").round(3).to_csv(
        OUT / "capital_tiers_by_city.csv", encoding="utf-8-sig")

    # 典型企业：每市注册资本前 5（注明：注册资本≠营收，仅作可观测规模代理；综合能力评分仅 9.2% 覆盖，列作参考）
    valid = df[cap_valid > 0].copy()
    valid["_capnum"] = pd.to_numeric(valid["注册资本"], errors="coerce")
    typical = (valid.sort_values("_capnum", ascending=False)
               .groupby("_市").head(5)
               [["_市", "企业名称", "_环节", "_capnum", "_评分", "成立时间"]]
               .rename(columns={"_市": "城市", "_环节": "环节",
                             "_capnum": "注册资本(万元·排序维度，≠营收)", "_评分": "综合能力评分(参考·非空率9.2%)"}))
    typical.to_csv(OUT / "typical_enterprises.csv", index=False, encoding="utf-8-sig")

    # 全国对照（同口径：环节列首个）
    nat = pd.read_csv(NATIONAL, usecols=["产业链环节"], encoding="gb18030", dtype=str)
    nat_seg = nat["产业链环节"].map(primary_seg).value_counts(normalize=True)
    reg_seg = df["_环节"].value_counts(normalize=True)
    cmp_df = pd.DataFrame({"京津冀占比": reg_seg.round(4), "全国占比": nat_seg.round(4)})
    cmp_df["占比比(区位熵式)"] = (cmp_df["京津冀占比"] / cmp_df["全国占比"]).round(2)
    cmp_df.to_csv(OUT / "regional_vs_national.csv", encoding="utf-8-sig")

    print("== 城市总表 =="); print(summ.to_string(index=False))
    print("\n== 年龄档整体分布 =="); print(df["_年龄档"].value_counts().to_string())
    print("\n== 规模档整体分布 =="); print(df["_规模档"].value_counts().to_string())
    print("\n== 京津冀 vs 全国 环节对照 =="); print(cmp_df.to_string())
    print("\n评分非空率:", f"{df['_评分'].notna().mean():.1%}", "｜人民币以外币种:",
          df.loc[~is_rmb, "注册资本币种"].value_counts().to_dict())
    print(f"\n已写入 {OUT}")


if __name__ == "__main__":
    main()
