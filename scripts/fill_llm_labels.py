# -*- coding: utf-8 -*-
"""必做② 第3步：合并大模型标签，算"裁判结果"。

对照规则（以分层为单位）：
  不一致层：大模型=老师？=基线？=第三答案？难定？
  一致层：大模型是否也认同？
  未覆盖层：大模型能判出环节吗？
并估算：以抽查样本为镜，基线与老师标签的"近似准确率"（剔除"难定"）。
输出 outputs/review_sample_llm.csv 与 outputs/review_scoreboard.md
"""
from pathlib import Path

import pandas as pd

OUT_DIR = Path(__file__).resolve().parents[1] / "outputs"


def main() -> None:
    s = pd.read_csv(OUT_DIR / "review_sample.csv", encoding="utf-8-sig")
    llm = pd.read_csv(OUT_DIR / "llm_labels.csv", encoding="utf-8-sig")
    # review_sample 里的大模型列是空占位，先丢掉再合并，否则同名列会变 _x/_y
    s = s.drop(columns=["大模型建议环节", "大模型理由"])
    s = s.merge(llm, on="序号", how="left", validate="1:1")
    s.to_csv(OUT_DIR / "review_sample_llm.csv", index=False, encoding="utf-8-sig")

    R = ["# 人工抽查·裁判记分牌（大模型标签作为初裁，组内复核为终审）\n"]
    for layer, g in s.groupby("分层"):
        n = len(g)
        R.append(f"## {layer}（{n} 家）")
        if layer == "不一致":
            R.append(f"- 大模型=老师：{(g['大模型建议环节'] == g['老师环节']).sum()} 家")
            R.append(f"- 大模型=基线：{(g['大模型建议环节'] == g['基线环节']).sum()} 家")
            third = ((g["大模型建议环节"] != g["老师环节"])
                     & (g["大模型建议环节"] != g["基线环节"])
                     & (g["大模型建议环节"] != "难定")).sum()
            R.append(f"- 大模型给第三答案：{third} 家")
            R.append(f"- 难定：{(g['大模型建议环节'] == '难定').sum()} 家")
        elif layer == "一致":
            R.append(f"- 大模型也认同：{(g['大模型建议环节'] == g['老师环节']).sum()} 家")
            R.append(f"- 大模型不认同：{((g['大模型建议环节'] != g['老师环节']) & (g['大模型建议环节'] != '难定')).sum()} 家")
            R.append(f"- 难定：{(g['大模型建议环节'] == '难定').sum()} 家")
        else:
            R.append(f"- 大模型能判出环节：{(g['大模型建议环节'] != '难定').sum()} 家")
            R.append(f"- 仍难定：{(g['大模型建议环节'] == '难定').sum()} 家")
        R.append("")

    # 近似准确率：剔除难定后，大模型为镜
    det = s[s["大模型建议环节"] != "难定"]
    R.append("## 以抽查为镜的近似准确率（剔除难定）")
    R.append(f"- 基线命中率：{(det['大模型建议环节'] == det['基线环节']).mean():.1%}（{len(det)} 家）")
    R.append(f"- 老师命中率：{(det['大模型建议环节'] == det['老师环节']).mean():.1%}（{len(det)} 家）")

    out = "\n".join(R)
    (OUT_DIR / "review_scoreboard.md").write_text(out, encoding="utf-8")
    print(out)


if __name__ == "__main__":
    main()
