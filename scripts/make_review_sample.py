# -*- coding: utf-8 -*-
"""必做② 第5步：100 家人工抽查样本（分层抽样，随机种子 42 可复现）。

  - 不一致 50 家：基线覆盖但与数据标签不同 → 看"谁对"
  - 一致 20 家：两边相同 → 检验"一致"是否真对
  - 未覆盖 30 家：基线盲区 → 看这些企业实际属于什么环节
输出 outputs/review_sample.csv（含 人工认定/备注/大模型建议环节/大模型理由 空列待填）。
"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from seg_rules import OUT_DIR

N_DIS, N_AGREE, N_UNCOV = 50, 20, 30
SEED = 42


def main() -> None:
    df = pd.read_csv(OUT_DIR / "segment_predictions.csv", encoding="utf-8-sig", dtype=str)
    dis = df[df["基线环节"].notna() & (df["基线环节"] != df["数据环节"])]
    agree = df[df["基线环节"].notna() & (df["基线环节"] == df["数据环节"])]
    uncov = df[df["基线环节"].isna()]

    s = pd.concat([
        dis.sample(n=N_DIS, random_state=SEED).assign(分层="不一致"),
        agree.sample(n=N_AGREE, random_state=SEED).assign(分层="一致"),
        uncov.sample(n=N_UNCOV, random_state=SEED).assign(分层="未覆盖"),
    ]).sample(frac=1, random_state=SEED).reset_index(drop=True)  # 打乱顺序防批改偏见

    s.insert(0, "序号", range(1, len(s) + 1))
    for col in ["大模型建议环节", "大模型理由", "人工认定", "备注"]:
        s[col] = ""
    s = s[["序号", "企业名称", "所属城市", "产业链完整路径", "数据环节", "基线环节",
           "分层", "人工认定", "备注", "大模型建议环节", "大模型理由"]]
    s.to_csv(OUT_DIR / "review_sample.csv", index=False, encoding="utf-8-sig")
    print(f"样本 {len(s)} 家：不一致 {(s['分层'] == '不一致').sum()}, "
          f"一致 {(s['分层'] == '一致').sum()}, 未覆盖 {(s['分层'] == '未覆盖').sum()}")
    print("已写入", OUT_DIR / "review_sample.csv")


if __name__ == "__main__":
    main()
