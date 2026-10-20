# -*- coding: utf-8 -*-
"""必做② 第2步：人工抽查样本框（给"基线/老师分歧"找裁判）。

分层抽样（随机种子固定，可复现）：
  - 不一致 50 家：基线 v2 覆盖但与老师标签不同 → 看"谁对"
  - 一致 20 家：两边相同 → 检验"一致"是否真对
  - 未覆盖 30 家：基线盲区 → 看这些企业实际属于什么环节
输出 outputs/review_sample.csv：
  原始列 + 分层 + 大模型建议环节/大模型理由/人工认定（空列待填）。
"""
from pathlib import Path

import pandas as pd

PRED = Path(__file__).resolve().parents[1] / "outputs" / "segment_predictions.csv"
OUT_DIR = Path(__file__).resolve().parents[1] / "outputs"

N_DIS, N_AGREE, N_UNCOV = 50, 20, 30
SEED = 42

SEG7 = ["上游-原材料", "中游-关键零部件", "下游-整车制造", "配套服务支撑",
        "智能汽车技术", "基础支撑技术", "信息交互技术"]


def main() -> None:
    df = pd.read_csv(PRED, encoding="utf-8-sig")
    dis = df[df["基线环节"].notna() & (df["基线环节"] != df["老师环节"])]
    agree = df[df["基线环节"].notna() & (df["基线环节"] == df["老师环节"])]
    uncov = df[df["基线环节"].isna()]

    s = pd.concat([
        dis.sample(n=N_DIS, random_state=SEED).assign(分层="不一致"),
        agree.sample(n=N_AGREE, random_state=SEED).assign(分层="一致"),
        uncov.sample(n=N_UNCOV, random_state=SEED).assign(分层="未覆盖"),
    ]).sample(frac=1, random_state=SEED).reset_index(drop=True)  # 打乱顺序防批改偏见

    s.insert(0, "序号", range(1, len(s) + 1))
    for col in ["大模型建议环节", "大模型理由", "人工认定", "备注"]:
        s[col] = ""
    keep = ["序号", "企业名称", "所属城市", "产业链完整路径",
            "老师环节", "基线环节", "分层",
            "大模型建议环节", "大模型理由", "人工认定", "备注"]
    out = OUT_DIR / "review_sample.csv"
    s[keep].to_csv(out, index=False, encoding="utf-8-sig")
    print(f"样本 {len(s)} 家：不一致 {len(s[s['分层']=='不一致'])}, "
          f"一致 {len(s[s['分层']=='一致'])}, 未覆盖 {len(s[s['分层']=='未覆盖'])}")
    print(f"已写入 {out}")


if __name__ == "__main__":
    main()
