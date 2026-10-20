# -*- coding: utf-8 -*-
"""必做② 第4步：地区统计（城市×环节×年龄×规模）+ 全国对照。

口径声明（作业红线）：
  - 环节用老师口径（全覆盖），但已知噪声≈42%（见 review_scoreboard.md），
    结论按"结构画像"使用，不做企业级断言；
  - 注册资本 ≠ 营收，仅作可观测规模代理；缺失/非正值单列"未知"档；
  - 排序维度一律注明来源列。
输出 outputs/stats/ 下 6 张表。
"""
from pathlib import Path

import pandas as pd

REGION = Path(r"C:\Users\宏宇\Downloads\一键换链脚本包+数据包_新链_v1.5_20260922\脚本总包_产业集群聚类与集群指数\02_集群指数\输入数据\02_区域企业数据.csv")
NATIONAL = Path(r"C:\Users\宏宇\Downloads\一键换链脚本包+数据包_新链_v1.5_20260922\脚本总包_产业集群聚类与集群指数\02_集群指数\输入数据\01_全国企业数据.csv")
OUT_DIR = Path(__file__).resolve().parents[1] / "outputs" / "stats"

CURRENT_YEAR = 2026  # 数据截止约2026-08（必做①结论）
CAP_TIERS = [("微型≤100万", -1, 100), ("小型100-1000万", 100, 1000),
             ("中型1000万-1亿", 1000, 10000), ("大型>1亿", 10000, None)]
AGE_BINS = [("<5年", 0, 5), ("5-10年", 5, 10), ("10-20年", 10, 20), ("≥20年", 20, None)]


def bin_value(v, bins):
    """按 [lo, hi) 分档；v 缺失返回 None。"""
    if v is None or pd.isna(v):
        return None
    for name, lo, hi in bins:
        if v >= lo and (hi is None or v < hi):
            return name
    return None


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(REGION, encoding="utf-8-sig", low_memory=False)
    df["_环节"] = df["产业链完整路径"].astype(str).str.split(" > ").str[1]
    df["_年龄"] = CURRENT_YEAR - pd.to_datetime(df["成立时间"], errors="coerce").dt.year
    cap = pd.to_numeric(df["注册资本"], errors="coerce")
    df["_规模档"] = cap.apply(lambda v: bin_value(v, CAP_TIERS) if pd.notna(v) and v > 0 else "未知")
    df["_年龄档"] = df["_年龄"].apply(lambda v: bin_value(v, AGE_BINS))
    n = len(df)

    # 1. 城市×环节 交叉表
    ct = pd.crosstab(df["所属城市"], df["_环节"], margins=True, margins_name="合计")
    ct.to_csv(OUT_DIR / "city_segment_crosstab.csv", encoding="utf-8-sig")

    # 2. 城市总表：企业数/年龄/规模/主导环节
    rows = []
    for city, g in df.groupby("所属城市"):
        top_seg = g["_环节"].value_counts()
        rows.append({
            "城市": city, "企业数": len(g), "占区域比": f"{len(g) / n:.1%}",
            "年龄中位数": g["_年龄"].median(), "注册资本中位数(万元)": g.loc[cap > 0, "注册资本"].median() if (cap.loc[g.index] > 0).any() else None,
            "第一环节": top_seg.index[0], "第一环节占比": f"{top_seg.iloc[0] / len(g):.1%}",
            "第二环节": top_seg.index[1] if len(top_seg) > 1 else "",
        })
    summ = pd.DataFrame(rows).sort_values("企业数", ascending=False)
    summ.to_csv(OUT_DIR / "city_summary.csv", index=False, encoding="utf-8-sig")

    # 3. 年龄结构（整体 + 分城市档分布）
    age_tab = pd.crosstab(df["所属城市"], df["_年龄档"], normalize="index").round(3)
    age_tab.to_csv(OUT_DIR / "age_structure_by_city.csv", encoding="utf-8-sig")

    # 4. 规模结构（城市×规模档占比）
    cap_tab = pd.crosstab(df["所属城市"], df["_规模档"], normalize="index").round(3)
    cap_tab.to_csv(OUT_DIR / "capital_tiers_by_city.csv", encoding="utf-8-sig")

    # 5. 典型企业：每市注册资本前5（注明：注册资本≠营收）
    valid = df[cap > 0].copy()
    typical = (valid.sort_values("注册资本", ascending=False)
               .groupby("所属城市").head(5)
               [["所属城市", "企业名称", "_环节", "注册资本", "成立时间", "综合能力评分"]]
               .rename(columns={"_环节": "环节", "注册资本": "注册资本(万元·排序维度)"}))
    typical.to_csv(OUT_DIR / "typical_enterprises.csv", index=False, encoding="utf-8-sig")

    # 6. 全国对照：环节占比 京津冀 vs 全国
    nat = pd.read_csv(NATIONAL, usecols=["产业链完整路径"], encoding="utf-8-sig", low_memory=False)
    nat_seg = nat["产业链完整路径"].astype(str).str.split(" > ").str[1].value_counts(normalize=True)
    reg_seg = df["_环节"].value_counts(normalize=True)
    cmp_df = pd.DataFrame({"京津冀占比": reg_seg.round(4), "全国占比": nat_seg.round(4)})
    cmp_df["占比比(区位熵式)"] = (cmp_df["京津冀占比"] / cmp_df["全国占比"]).round(2)
    cmp_df.to_csv(OUT_DIR / "regional_vs_national.csv", encoding="utf-8-sig")

    print("== 城市总表 ==")
    print(summ.to_string(index=False))
    print("\n== 年龄档整体分布 ==")
    print(df["_年龄档"].value_counts().to_string())
    print("\n== 规模档整体分布 ==")
    print(df["_规模档"].value_counts().to_string())
    print("\n== 京津冀 vs 全国 环节对照 ==")
    print(cmp_df.to_string())
    print(f"\n已写入 {OUT_DIR}")


if __name__ == "__main__":
    main()
