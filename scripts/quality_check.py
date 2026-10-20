# -*- coding: utf-8 -*-
"""必做① 第2步：主表质量核查 → 质量报告 v1

对应作业要求："经营状态及坐标核查，统计缺失率与异常率"。
输入：司马台总数据.xlsx（只读）
输出：outputs/ 下
  - quality_report.md        人读质量报告
  - coord_out_of_bounds.csv  坐标出界企业清单
  - coord_top_shared.csv     共享企业数最多的坐标点
  - duplicate_names.csv      重名企业（同名不同代码）
"""
from pathlib import Path

import pandas as pd

# ---------- 配置（调参数只动这里） ----------
XLSX = Path(r"C:\Users\宏宇\Downloads\一键换链脚本包+数据包_新链_v1.5_20260922\数据包_新链\01聚类输入\司马台总数据.xlsx")
SHEET = "筛选后企业信息"
OUT_DIR = Path(__file__).resolve().parents[1] / "outputs"  # scripts/ 的上一级 = 模块目录

# 京津冀包围盒（抄自脚本包 01 引擎 config.json）：纬度、经度
LAT_MIN, LAT_MAX = 35.5, 42.7
LON_MIN, LON_MAX = 113.3, 120.0

SHARED_TOP_N = 20      # 报告列出共享企业数最多的前 N 个坐标
SHARED_WARN = 100      # 单点企业数超过此值 → 高度聚集，点名
MAX_SINGLE_SHARE = 0.5  # 老师引擎质检阈值：单坐标企业占比上限

COL = dict(name="企业名称", code="统一社会信用代码", coord="经纬度坐标",
           capital="注册资本", currency="注册资本币种", found="成立时间",
           status="经营状态")


def parse_coord(s):
    """'37.739568,114.460636' → (lat, lon)；解析失败返回 (None, None)。

    本表为纬度在前、经度在后（第1步已验证）。
    """
    if not isinstance(s, str):
        return None, None
    parts = s.replace("，", ",").split(",")  # 兼容中文逗号
    if len(parts) != 2:
        return None, None
    try:
        return float(parts[0]), float(parts[1])
    except ValueError:
        return None, None


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    df = pd.read_excel(XLSX, sheet_name=SHEET)
    n = len(df)
    R = []  # report lines

    def rep(line=""):
        R.append(line)
        print(line)

    rep(f"# 数据质量报告 v1 · 司马台总数据（{n} 行）\n")

    # ---- 1. 坐标核查 ----
    latlon = df[COL["coord"]].apply(parse_coord)
    df["_lat"] = [x[0] for x in latlon]
    df["_lon"] = [x[1] for x in latlon]

    missing = int(df["_lat"].isna().sum())
    inb = df.dropna(subset=["_lat"])
    oob = inb[(inb["_lat"] < LAT_MIN) | (inb["_lat"] > LAT_MAX)
              | (inb["_lon"] < LON_MIN) | (inb["_lon"] > LON_MAX)]
    rep("## 1. 坐标核查")
    rep(f"- 缺失或无法解析：{missing} 家（{missing / n:.2%}）")
    rep(f"- 出京津冀包围盒：{len(oob)} 家（{len(oob) / n:.2%}）→ coord_out_of_bounds.csv")

    shared = (inb.groupby([COL["coord"]], as_index=False)
              .agg(企业数=(COL["code"], "count"),
                   代表企业=(COL["name"], "first"))
              .sort_values("企业数", ascending=False))
    top_share = shared["企业数"].iloc[0] / len(inb)
    crowded = shared[shared["企业数"] >= SHARED_WARN]
    rep(f"- 共享坐标点共 {len(shared)} 个；最挤的点 {shared['企业数'].iloc[0]} 家"
        f"（占比 {top_share:.1%}，阈值 {MAX_SINGLE_SHARE:.0%}）")
    rep(f"- 单点 ≥{SHARED_WARN} 家的高度聚集点：{len(crowded)} 个 → coord_top_shared.csv\n")

    # ---- 2. 重名核查 ----
    dup_mask = df[COL["name"]].duplicated(keep=False)
    dups = df[dup_mask].sort_values(COL["name"])
    rep("## 2. 重名核查")
    rep(f"- 重名企业行：{len(dups)} 行（涉及 {dups[COL['name']].nunique()} 个名字）"
        f"→ duplicate_names.csv\n")

    # ---- 3. 注册资本 ----
    cap = df[COL["capital"]]
    bad_cap = df[cap.notna() & (cap <= 0)]
    rep("## 3. 注册资本")
    rep(f"- 缺失：{int(cap.isna().sum())} 家（{cap.isna().mean():.2%}）")
    rep(f"- 非正值：{len(bad_cap)} 家")
    rep(f"- 币种分布：{df[COL['currency']].value_counts().to_dict()}")
    q = cap.quantile([0.25, 0.5, 0.75, 0.99])
    rep(f"- 分位数(万元)：25%={q.iloc[0]:.0f} / 中位={q.iloc[1]:.0f} / "
        f"75%={q.iloc[2]:.0f} / 99%={q.iloc[3]:.0f}\n")

    # ---- 4. 成立时间 ----
    found = pd.to_datetime(df[COL["found"]], errors="coerce")
    nat = int(found.isna().sum())
    future = int((found > pd.Timestamp.today()).sum())
    years = found.dt.year
    rep("## 4. 成立时间")
    rep(f"- 无法解析：{nat} 家；日期在未来：{future} 家")
    rep(f"- 范围：{found.min():%Y-%m-%d} ~ {found.max():%Y-%m-%d}")
    top_years = years.value_counts().sort_index().tail(5)
    rep("- 近五年新设：" + ", ".join(f"{y}年{c}家" for y, c in top_years.items()) + "\n")

    # ---- 5. 已知边界（继承第1步结论）----
    rep("## 5. 已知边界")
    rep("- 经营状态单一（全部在营）：退出不可观测，不能做退出预测")
    rep("- 经营期限至缺失 62.8%：结构性缺失，不可作为分析字段")
    rep("- 地址=注册地址：无法区分注册地与生产/研发场所（作业边界，需声明）")

    # ---- 写文件（CSV 用 utf-8-sig：Excel 打开中文不乱码）----
    oob.drop(columns=["_lat", "_lon"]).to_csv(
        OUT_DIR / "coord_out_of_bounds.csv", index=False, encoding="utf-8-sig")
    shared.head(SHARED_TOP_N).to_csv(
        OUT_DIR / "coord_top_shared.csv", index=False, encoding="utf-8-sig")
    dups.drop(columns=["_lat", "_lon"]).to_csv(
        OUT_DIR / "duplicate_names.csv", index=False, encoding="utf-8-sig")
    (OUT_DIR / "quality_report.md").write_text("\n".join(R), encoding="utf-8")
    print(f"\n已写入 {OUT_DIR}")


if __name__ == "__main__":
    main()
