# -*- coding: utf-8 -*-
"""必做② 第1步：环节词表（4 环节 → 中类 → 节点）。

输出 outputs/segment_vocabulary.csv 与 .md。
代表企业＝该环节内综合能力评分前 3（排序维度与来源列注明；注册资本不替代营收）。
"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from seg_rules import MASTER, OUT_DIR, SEG4, RULES, path_primary, primary_seg

DEFS = {
    "上游": "网络安全与工业互联网的技术与硬件投入：技术与数据资源（安全算法/密码技术/工业协议/漏洞资源/威胁情报）、基础硬件（工控设备/通信设备/可信计算/基础软件/安全芯片）",
    "中游": "通用安全产品与解决方案：数据安全/边界安全/身份安全/终端安全、安全运营/监测预警/态势感知、安全审计/主机防护/工业网闸",
    "下游": "工业互联网落地主体与行业应用：工业互联网平台/联网工业企业/标识解析、原材料工业/电子信息制造/装备制造、能源电力/交通物流/智能工厂",
    "配套服务": "产业支撑服务：检测评估/安全运维/咨询规划/应急响应/标准科研/集成实施/人才与金融/测评认证",
}
KEYWORDS = {seg: "、".join(kws) for seg, kws in RULES}


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(MASTER, encoding="utf-8-sig", dtype=str)
    n = len(df)
    parsed = df["产业链完整路径"].map(path_primary)
    df["_环节"] = [p[0] for p in parsed]
    df["_中类"] = [p[1] for p in parsed]
    df["_节点"] = [p[2] for p in parsed]
    df["_评分"] = pd.to_numeric(df["综合能力评分"], errors="coerce")

    rows, md = [], ["# 产业环节词表 · 京津冀新一代信息技术/网络安全与工业互联网（4 环节）\n",
                    "> 口径：环节=数据原生标签（路径第 2 层，配套服务=路径中'相关支撑服务'），主环节=环节列首个；",
                    "> 中类/节点=产业链完整路径首条。多标签企业 2,391 家（6.2%）。",
                    "> 已知噪声：'工业互联网平台'(20,062 家)与'检测评估'(8,641 家)两大桶口径偏宽，",
                    "> 结构画像可用、企业级断言需经基线/抽查检验（见基线报告与记分牌）。",
                    "> 生成：scripts/make_segment_vocabulary.py\n"]
    for seg in SEG4:
        g = df[df["_环节"] == seg]
        cnt = len(g)
        md.append(f"## {seg}（{cnt:,} 家，占 {cnt / n:.1%}）")
        md.append(f"- **定义**：{DEFS[seg]}")
        node_line = "；".join(f"{mid}({c:,}家)" for mid, c in
                              g.groupby("_中类").size().sort_values(ascending=False).items())
        md.append(f"- **中类与节点**：{node_line}")
        md.append(f"- **基线关键词**：{KEYWORDS[seg]}")
        top = g.nlargest(3, "_评分")
        rep = "；".join(f"{r['企业名称']}（{r['综合能力评分']}分）" for _, r in top.iterrows())
        md.append(f"- **代表企业**（综合能力评分前 3，来源列=综合能力评分）：{rep}")
        md.append("")
        for (mid, leaf), c in g.groupby(["_中类", "_节点"]).size().sort_values(ascending=False).items():
            rows.append({"环节": seg, "中类": mid, "节点": leaf, "区域企业数": c})

    pd.DataFrame(rows).to_csv(OUT_DIR / "segment_vocabulary.csv", index=False, encoding="utf-8-sig")
    (OUT_DIR / "segment_vocabulary.md").write_text("\n".join(md), encoding="utf-8")
    print("\n".join(md))


if __name__ == "__main__":
    main()
