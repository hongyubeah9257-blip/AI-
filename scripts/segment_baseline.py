# -*- coding: utf-8 -*-
"""必做② 第2步：环节关键词分类基线 vs 数据原生标签。

只用一个文本字段（企业名称）做独立基线，与数据环节（主口径）算覆盖率、一致率；
不一致样本导出供人工抽查。
输出 outputs/：segment_keyword_report.md、segment_predictions.csv、segment_disagreement_sample.csv
"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from seg_rules import MASTER, OUT_DIR, classify, primary_seg


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(MASTER, encoding="utf-8-sig", dtype=str)
    df["数据环节"] = df["产业链环节"].map(primary_seg)
    df["基线环节"] = df["企业名称"].map(classify)

    n = len(df)
    covered = df["基线环节"].notna()
    cov = covered.mean()
    agree = (df.loc[covered, "基线环节"] == df.loc[covered, "数据环节"]).mean()

    R = [f"# 环节关键词基线 · 报告（区域企业 {n:,} 家）",
         "- 规则版本：新链 v1（仅企业名称；上游硬件词→中游安全产品词→下游平台词→配套服务词，",
         "  上下文规则：安全+生产/工程/消防/评价/应急→配套服务，防止生产安全公司误入中游）",
         "- 对照口径：数据原生环节（主口径=环节列首个）",
         f"- 关键词覆盖率：{covered.sum():,} 家（{cov:.1%}）",
         f"- 覆盖部分与数据标签一致率：{agree:.1%}",
         "\n## 数据环节 × 基线环节 交叉表（仅覆盖部分）"]
    ct = pd.crosstab(df.loc[covered, "数据环节"], df.loc[covered, "基线环节"])
    R.append(ct.to_string())

    R.append("\n## 未覆盖企业的数据环节分布（基线的盲区）")
    R.append(df.loc[~covered, "数据环节"].value_counts().to_string())

    dis = df[covered & (df["基线环节"] != df["数据环节"])]
    sample = dis.groupby("数据环节", group_keys=False).sample(
        n=min(15, len(dis)), random_state=42) if len(dis) else dis
    sample_cols = ["企业名称", "所属城市", "数据环节", "基线环节", "产业链完整路径"]
    sample[sample_cols].to_csv(OUT_DIR / "segment_disagreement_sample.csv",
                               index=False, encoding="utf-8-sig")
    R.append(f"\n## 不一致情况：{len(dis):,} 家（占覆盖 {len(dis) / covered.sum():.1%}），"
             f"已抽样 {len(sample)} 条 → segment_disagreement_sample.csv")

    df[["企业名称", "统一社会信用代码", "所属省份", "所属城市",
        "数据环节", "基线环节", "产业链完整路径"]].to_csv(
        OUT_DIR / "segment_predictions.csv", index=False, encoding="utf-8-sig")

    report = "\n".join(R)
    (OUT_DIR / "segment_keyword_report.md").write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
