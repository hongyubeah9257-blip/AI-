# -*- coding: utf-8 -*-
"""新链（新一代信息技术/网络安全与工业互联网）必做①：京津冀主表构建。

从全国企业数据（139,263 行）筛出京津冀子集，做字段规范化、去重、坐标核查，
产出：
  outputs/master_clean.csv          —— 模块自用工作主表（utf-8-sig）
  outputs/司马台总数据_新一代信息技术.xlsx —— 一键换链工具包接口格式（15 列）
  outputs/quality_report.md         —— 质量报告 v1
口径：京津冀=所属省份∈{北京市,天津市,河北省}（省份字段 100% 非空）；坐标包围盒
35.5–42.7°N / 113.3–120.0°E 仅作交叉核查标记，不作过滤依据。
"""
import re
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT.parent / "原料" / "新一代信息技术全国企业数据.csv"
OUT = ROOT / "outputs"

JJJ_PROV = ["北京市", "天津市", "河北省"]
LAT_LO, LAT_HI = 35.5, 42.7
LON_LO, LON_HI = 113.3, 120.0

TOOLKIT_COLS = ["企业名称", "法定代表人", "行业门类", "企业类型", "成立时间", "经营状态",
                "注册资本", "注册资本币种", "经营期限自", "经营期限至", "登记机关", "核准日期",
                "经纬度坐标", "地址", "统一社会信用代码"]


def norm_date(s: str) -> str:
    s = str(s).strip()
    if not s:
        return ""
    m = re.match(r"^(\d{4})[/-](\d{1,2})[/-](\d{1,2})", s)
    if m:
        y, mo, d = m.groups()
        return f"{y}-{int(mo):02d}-{int(d):02d}"
    return s


def parse_coord(s: str):
    try:
        a, b = str(s).split(",")
        return float(a), float(b)
    except Exception:
        return None, None


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(RAW, encoding="gb18030", dtype=str, keep_default_na=False)
    n_raw = len(df)

    jjj = df[df["所属省份"].isin(JJJ_PROV)].copy()
    n_jjj = len(jjj)

    # 字段规范化
    jjj["成立时间"] = jjj["成立时间"].map(norm_date)
    coord = jjj["经纬度坐标"].map(parse_coord)
    jjj["纬度"] = [c[0] for c in coord]
    jjj["经度"] = [c[1] for c in coord]
    jjj["地址"] = (jjj["所属省份"] + jjj["所属城市"]).str.strip()

    # 质量标记（先打标后去重，去重另记）
    def flags(r):
        f = []
        code = r["统一社会信用代码"].strip()
        if not re.fullmatch(r"[0-9A-Z]{18}", code):
            f.append("信用代码缺失或格式异常")
        if r["纬度"] is None:
            f.append("坐标解析失败")
        elif r["纬度"] == 0.0 and r["经度"] == 0.0:
            f.append("坐标为(0,0)无效")
        elif not (LAT_LO <= r["纬度"] <= LAT_HI and LON_LO <= r["经度"] <= LON_HI):
            f.append("坐标超出京津冀包围盒")
        if not r["经营状态"].strip():
            f.append("经营状态缺失")
        return ";".join(f)

    jjj["质量标记"] = jjj.apply(flags, axis=1)

    # 去重：信用代码有效者按键去重，无效者按企业名称；组内保留非空字段最多的一行
    jjj["_key"] = jjj.apply(
        lambda r: "C:" + r["统一社会信用代码"].strip()
        if re.fullmatch(r"[0-9A-Z]{18}", r["统一社会信用代码"].strip())
        else "N:" + r["企业名称"].strip(), axis=1)
    jjj["_completeness"] = (jjj.drop(columns=["质量标记"]) != "").sum(axis=1)
    jjj = jjj.sort_values("_completeness", ascending=False)
    dup_mask = jjj.duplicated("_key", keep="first")
    n_dup = int(dup_mask.sum())
    dup_sources = jjj.loc[dup_mask, "数据来源"].value_counts().head(5).to_dict()
    jjj = jjj[~dup_mask].copy()

    # 企业标识列（与 NEV 主表口径一致：C:信用代码 / N:名称）
    jjj["企业标识"] = jjj["_key"]

    work_cols = ["企业标识", "企业名称", "统一社会信用代码", "所属省份", "所属城市", "纬度", "经度",
                 "地址", "产业链环节", "产业链完整路径", "一级产业", "注册资本", "注册资本币种",
                 "成立时间", "经营状态", "创新能力评分", "合法合规评分", "综合能力评分",
                 "数据来源", "质量标记"]
    master = jjj[work_cols].sort_values(["所属省份", "所属城市", "企业名称"])
    master.to_csv(OUT / "master_clean.csv", index=False, encoding="utf-8-sig")

    # 工具包接口格式（15 列 xlsx）
    tk = pd.DataFrame({
        "企业名称": jjj["企业名称"], "法定代表人": "", "行业门类": "", "企业类型": "",
        "成立时间": jjj["成立时间"], "经营状态": jjj["经营状态"],
        "注册资本": jjj["注册资本"], "注册资本币种": jjj["注册资本币种"],
        "经营期限自": "", "经营期限至": "", "登记机关": "", "核准日期": "",
        "经纬度坐标": jjj["经纬度坐标"], "地址": jjj["地址"],
        "统一社会信用代码": jjj["统一社会信用代码"],
    })[TOOLKIT_COLS].sort_values("企业名称")
    tk.to_excel(OUT / "司马台总数据_新一代信息技术.xlsx", index=False)

    # 统计
    n_final = len(master)
    flag_counts = {}
    for s in master["质量标记"]:
        for f in str(s).split(";"):
            if f:
                flag_counts[f] = flag_counts.get(f, 0) + 1
    prov_dist = master["所属省份"].value_counts().to_dict()
    seg_counts = master["产业链环节"].replace("", "(空)").value_counts().head(8).to_dict()
    multi_seg = int(master["产业链环节"].str.contains("/").sum())
    status_fill = master["经营状态"].ne("").mean()
    date_min = master.loc[master["成立时间"] > "", "成立时间"].min()
    date_max = master.loc[master["成立时间"] > "", "成立时间"].max()

    report = f"""# 质量报告 v1 · 新链京津冀主表（新一代信息技术/网络安全与工业互联网）

生成：scripts/build_jjj_master.py ｜ 数据：原料/新一代信息技术全国企业数据.csv

- 全国原始行数：{n_raw:,}
- 京津冀子集（省份口径）：{n_jjj:,}
- 去重合并：-{n_dup:,}（重复来源 Top5：{dup_sources}）
- **最终主表：{n_final:,} 家**（信用代码键 C: 优先，缺失按企业名称 N:）

## 分省分布
{chr(10).join(f'- {k}：{v:,}' for k, v in prov_dist.items())}

## 质量标记统计（一家可多标）
{chr(10).join(f'- {k}：{v:,}（{v/n_final:.1%}）' for k, v in sorted(flag_counts.items(), key=lambda x: -x[1]))}

## 字段口径
- 成立时间：{date_min} ~ {date_max}（缺失 {(master['成立时间'] == '').sum():,}）
- 经营状态：非空率 {status_fill:.1%}（全国源 68% 缺失，属源数据边界，不作剔除依据）
- 产业链环节：多标签（含"/"）{multi_seg:,} 家；环节分布 Top：{seg_counts}
- 坐标：纬度在前经度在后（抽查：北京 39.9N/116.4E 合理）；包围盒仅作标记不过滤

## 产物
- master_clean.csv（{n_final:,} 行 × {len(work_cols)} 列，utf-8-sig）
- 司马台总数据_新一代信息技术.xlsx（工具包 15 列接口格式，法定代表人/行业门类等源数据没有的列留空）
"""
    (OUT / "quality_report.md").write_text(report, encoding="utf-8")
    print(report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
