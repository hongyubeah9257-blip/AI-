# -*- coding: utf-8 -*-
"""必做② 第1步：环节关键词分类基线 vs 老师口径标签。

7 环节方案（作业要求 4–8 个，来自完整路径第2层）：
  上游-原材料 / 中游-关键零部件 / 下游-整车制造 / 配套服务支撑 /
  智能汽车技术 / 基础支撑技术 / 信息交互技术
规则：按 RULES 顺序首中即停——专用词（零部件/充电）必须排在通用词（汽车）前面。
对照：与老师标签算覆盖率、一致率；不一致样本导出供人工抽查。
输出 outputs/：segment_keyword_report.md、segment_predictions.csv、segment_disagreement_sample.csv
"""
from pathlib import Path

import pandas as pd

REGION = Path(r"C:\Users\宏宇\Downloads\一键换链脚本包+数据包_新链_v1.5_20260922\脚本总包_产业集群聚类与集群指数\02_集群指数\输入数据\02_区域企业数据.csv")
OUT_DIR = Path(__file__).resolve().parents[1] / "outputs"
SEG7 = ["上游-原材料", "中游-关键零部件", "下游-整车制造", "配套服务支撑",
        "智能汽车技术", "基础支撑技术", "信息交互技术"]

# (环节, [关键词]) —— 顺序即优先级，先专用后通用
# v2 新增"上下文规则"：需同时含 上下文词+特征词（如 汽车+销售→配套），
# 解决"汽车销售服务/修理厂被'汽车'通用词错抓去整车"的问题（v1 约 500 家）。
CONTEXT_RULES = [
    ("配套服务支撑", "汽车", ["销售", "维修", "修理", "服务", "租赁"]),
]

RULES = [
    ("配套服务支撑", ["充电", "换电", "储能", "出行", "网约车", "汽车租赁",
                  "二手车", "汽车服务", "汽车维修", "驾校", "停车"]),
    ("上游-原材料", ["材料", "锂", "镍", "钴", "石墨", "电解液", "隔膜", "正极", "负极",
                 "氢能", "燃料电池", "涂料", "橡胶", "玻璃", "铝业", "钢铁", "化工", "新材"]),
    ("中游-关键零部件", ["零部件", "配件", "模具", "底盘", "轴承", "电机", "电控", "线束",
                   "座椅", "车灯", "变速", "轮毂", "车身", "冲压", "铸造", "锻造", "空调"]),
    ("智能汽车技术", ["自动驾驶", "智能驾驶", "激光雷达", "毫米波", "智能座舱", "线控",
                  "域控制", "感知", "无人驾驶"]),
    ("基础支撑技术", ["地图", "定位", "导航", "数据标注", "网络安全", "信息安全", "惯性"]),
    ("信息交互技术", ["车联网", "V2X", "v2x", "通信", "边缘计算", "路侧", "5G", "5g"]),
    ("下游-整车制造", ["汽车", "客车", "轿车", "专用车", "整车", "车辆", "新能源车"]),
]


def classify(name: str):
    """企业名称 → 环节；无命中返回 None。只用一个文本字段：企业名称。"""
    if not isinstance(name, str):
        return None
    for seg, ctx, kws in CONTEXT_RULES:  # v2：先查"上下文+特征"组合规则
        if ctx in name and any(kw in name for kw in kws):
            return seg
    for seg, kws in RULES:
        for kw in kws:
            if kw in name:
                return seg
    return None


def teacher_seg7(path: str):
    """'新能源汽车 > 下游-整车制造 > 新能源轿车' → '下游-整车制造'"""
    parts = str(path).split(" > ")
    return parts[1] if len(parts) > 1 else None


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(REGION, encoding="utf-8-sig", low_memory=False)
    df["老师环节"] = df["产业链完整路径"].apply(teacher_seg7)
    df["基线环节"] = df["企业名称"].apply(classify)

    n = len(df)
    covered = df["基线环节"].notna()
    cov = covered.mean()
    agree = (df.loc[covered, "基线环节"] == df.loc[covered, "老师环节"]).mean()

    R = [f"# 环节关键词基线 · 报告（区域企业 {n} 家）",
         "- 规则版本：v2（新增 汽车+销售/维修/修理/服务/租赁 → 配套 上下文规则）",
         "- v1 对照：覆盖率 31.1%，一致率 70.8%",
         f"- v2 关键词覆盖率：{covered.sum()} 家（{cov:.1%}）",
         f"- v2 覆盖部分与老师标签一致率：{agree:.1%}",
         "\n## 老师环节 × 基线环节 交叉表（仅覆盖部分）"]
    ct = pd.crosstab(df.loc[covered, "老师环节"], df.loc[covered, "基线环节"])
    R.append(ct.to_string())

    # 未覆盖企业的老师环节分布 → 看基线漏了什么
    R.append("\n## 未覆盖企业的老师环节分布（基线的盲区）")
    R.append(df.loc[~covered, "老师环节"].value_counts().to_string())

    # 不一致样本：每个"老师环节"随机抽最多15条供人工抽查
    # 用 GroupBy.sample（每组抽样且保留所有列），不用 groupby.apply（pandas3 会丢分组列）
    dis = df[covered & (df["基线环节"] != df["老师环节"])]
    sample = dis.groupby("老师环节", group_keys=False).sample(n=15, random_state=42)
    sample_cols = ["企业名称", "所属城市", "老师环节", "基线环节", "产业链完整路径"]
    sample[sample_cols].to_csv(OUT_DIR / "segment_disagreement_sample.csv",
                               index=False, encoding="utf-8-sig")
    R.append(f"\n## 不一致情况：{len(dis)} 家（占覆盖 {len(dis) / covered.sum():.1%}），"
             f"已抽样 {len(sample)} 条 → segment_disagreement_sample.csv")

    df[["企业名称", "统一社会信用代码", "所属省份", "所属城市",
        "老师环节", "基线环节", "产业链完整路径"]].to_csv(
        OUT_DIR / "segment_predictions.csv", index=False, encoding="utf-8-sig")

    report = "\n".join(R)
    (OUT_DIR / "segment_keyword_report.md").write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
