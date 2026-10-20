# -*- coding: utf-8 -*-
"""必做② 第6步：生成产业环节词表（作业"建议输出"明确要求的独立文件）。

每环节包含：定义（人工）/ 区域企业数 / 路径节点（自动）/ 关键词（沿用基线 RULES v2）/
代表企业（注册资本前3，注明排序维度≠营收）。
输出 outputs/segment_vocabulary.md 与 segment_vocabulary.csv
"""
from pathlib import Path

import pandas as pd

from segment_baseline import CONTEXT_RULES, RULES, classify  # 复用基线词表与分类器，保证口径唯一

REGION = Path(r"C:\Users\宏宇\Downloads\一键换链脚本包+数据包_新链_v1.5_20260922\脚本总包_产业集群聚类与集群指数\02_集群指数\输入数据\02_区域企业数据.csv")
OUT_DIR = Path(__file__).resolve().parents[1] / "outputs"

# 人工定义
DEFINITIONS = {
    "上游-原材料": "新能源汽车的物质投入：传统材料（钢/铝/玻璃/橡胶/涂料等）、锂离子电池材料、燃料电池材料（含制氢）",
    "中游-关键零部件": "整车所需的零部件与工艺装备：传统汽车零部件（模具/行走/传动/制动/冷却/电子/内外饰）与新能源汽车零部件（电池等）",
    "下游-整车制造": "新能源整车制造（轿车/混合动力/专用车/客车）。注意：自动打标把部分经销商混入此桶，读数偏高（见抽查审计）",
    "配套服务支撑": "围绕车辆流通与使用的服务：充换电与储能、出行服务、汽车研发与设计，以及词表规则扩展的销售/维修/租赁",
    "智能汽车技术": "自动驾驶技术：自动驾驶算法、环境感知、智能座舱与操作系统、线控驱动及转向、域控制器、计算芯片、仿真测试",
    "基础支撑技术": "智能网联的使能技术：信息与网络安全、数据标注与模型训练、高精度地图与定位、惯性导航",
    "信息交互技术": "车-路-云通信：车联网信息服务、路端感知、车载通信终端、C-V2X、多接入边缘计算、通信芯片与模块",
}

SEG_ORDER = ["上游-原材料", "中游-关键零部件", "下游-整车制造", "配套服务支撑",
             "智能汽车技术", "基础支撑技术", "信息交互技术"]


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(REGION, encoding="utf-8-sig", low_memory=False)
    parts = df["产业链完整路径"].astype(str).str.split(" > ")
    df["_环节"] = parts.str[1]
    df["_节点"] = parts.str[2]
    df["_评分"] = pd.to_numeric(df["综合能力评分"], errors="coerce")  # 非空约88%

    kw_map = {seg: kws for seg, kws in RULES}
    ctx_map = {seg: [f"{ctx}+{'/'.join(kws)}"] for seg, ctx, kws in CONTEXT_RULES}

    md = ["# 产业环节词表 · 京津冀新能源与智能网联汽车（7 环节）",
          "\n> 口径：环节=产业链完整路径第2层；关键词=分类基线 v2（segment_baseline.py）；",
          "> 代表企业按综合能力评分（老师口径，非空约88%）排序；环节标签存在噪声，",
          "> 代表企业为\"该标签下评分最高者\"，仅作结构参考。生成：scripts/make_segment_vocabulary.py\n"]
    vocab_rows = []
    for seg in SEG_ORDER:
        g = df[df["_环节"] == seg]
        nodes = g["_节点"].value_counts()
        # 代表企业选"双口径一致"（老师标签=基线预测）内评分最高者：
        # 纯评分/纯资本都会被巨型央企的规模带偏，双确认保证链上相关性
        det = g.copy()
        det["_基线"] = det["企业名称"].apply(classify)
        det["_评分2"] = det["_评分"].fillna(-1)
        det["_创新"] = pd.to_numeric(det["创新能力评分"], errors="coerce").fillna(-1)
        both = det[det["_基线"] == seg].sort_values(["_评分2", "_创新"], ascending=False)
        n_both = len(both)
        top = both.head(3)
        kws = kw_map.get(seg, []) + ctx_map.get(seg, [])
        md.append(f"\n## {seg}（{len(g)} 家，占 {len(g) / len(df):.1%}）")
        md.append(f"- **定义**：{DEFINITIONS[seg]}")
        md.append(f"- **路径节点**：{'；'.join(f'{n}({c}家)' for n, c in nodes.items())}")
        md.append(f"- **基线关键词**：{'、'.join(kws) if kws else '（无——靠其他环节排除后兜底）'}")
        md.append(f"- **代表企业**（双口径一致 {n_both} 家中综合能力评分前3）："
                  + "；".join(f"{r['企业名称']}（{r['_评分']:.0f}分）" for _, r in top.iterrows()))
        for node, c in nodes.items():
            vocab_rows.append({"环节": seg, "节点": node, "区域企业数": c,
                               "关键词": "、".join(kws), "定义": DEFINITIONS[seg]})

    pd.DataFrame(vocab_rows).to_csv(OUT_DIR / "segment_vocabulary.csv",
                                    index=False, encoding="utf-8-sig")
    (OUT_DIR / "segment_vocabulary.md").write_text("\n".join(md), encoding="utf-8")
    print("\n".join(md[:40]))
    print(f"\n...\n已写入 {OUT_DIR}")


if __name__ == "__main__":
    main()
