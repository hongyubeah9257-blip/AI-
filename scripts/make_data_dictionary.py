# -*- coding: utf-8 -*-
"""必做① 第3步：生成数据字典（机器统计 + 人工口径合并）。

脚本逐列计算 非空率/唯一值/示例值；人工在 DESCRIPTIONS 中写 含义/口径/质量备注。
合并输出到 outputs/：
  - data_dictionary.csv   机读（Excel 可开，utf-8-sig）
  - data_dictionary.md    人读（报告可直接引用）
列改名/增列时：脚本会提示哪些列缺描述，补进 DESCRIPTIONS 重跑即可。
"""
from pathlib import Path

import pandas as pd

XLSX = Path(r"C:\Users\宏宇\Downloads\一键换链脚本包+数据包_新链_v1.5_20260922\数据包_新链\01聚类输入\司马台总数据.xlsx")
SHEET = "筛选后企业信息"
OUT_DIR = Path(__file__).resolve().parents[1] / "outputs"

# 人工口径：列名 -> (含义/口径说明, 质量备注)
DESCRIPTIONS = {
    "统一社会信用代码": ("18 位法定唯一标识，本表主键；连接专利/主库/后续模块的统一 ID",
                     "0 缺失、0 重复"),
    "企业名称": ("工商注册全称",
                 "唯一值 38075；1 对疑似重复登记（同名同址不同代码，见 duplicate_names.csv）"),
    "法定代表人": ("注册法定代表人", "与分析关系弱，仅身份辅助信息"),
    "行业门类": ("国民经济行业分类门类（如：科学研究和技术服务业）", "缺失 1.38%"),
    "企业类型": ("登记类型（国有/外资/民营等）", "0 缺失"),
    "成立时间": ("工商登记成立日期，YYYY-MM-DD",
                 "范围 1949-10-01 ~ 2026-08-10；0 缺失；任务①面板的时间轴"),
    "经营状态": ("登记经营状态",
                 "全表单一值「在营（开业）企业」→ 退出不可观测，生长模拟任务①的硬边界"),
    "注册资本": ("注册资本数值，单位万元",
                 "缺失 3.14%；26 家非正值；是规模代理，≠营收/市值"),
    "注册资本币种": ("注册资本币种",
                     "人民币约 99%；另有美元/欧元/港元/日元等，脚本包内会折算"),
    "经营期限自": ("营业期限起始日", "缺失 0.01%"),
    "经营期限至": ("营业期限截止日",
                   "缺失 62.8%（长期经营此项为空，结构性缺失）——不可用作分析字段"),
    "登记机关": ("注册登记的市场监督管理局", "896 个唯一值；可辅助推断城市/区县归属"),
    "核准日期": ("最近一次核准/变更日期", "0 缺失"),
    "经纬度坐标": ("纬度，经度（纬度在前，解析时注意！）",
                   "缺失 0.55%；5.58% 在京津冀界外（注册地在外地的链上企业，口径待确认）"),
    "地址": ("注册地址",
             "≠生产/研发场所（作业边界，需声明）；可辅助区县归属"),
}

# 列类型识别：按内容语义，不盲信 dtype
TYPE_MAP = {
    "成立时间": "日期", "核准日期": "日期", "经营期限自": "日期", "经营期限至": "日期",
    "注册资本": "数值(万元)",
    "经纬度坐标": "坐标(纬度,经度)",
}


def md_table(df: pd.DataFrame) -> str:
    """把 DataFrame 拼成 Markdown 表格（不引第三方依赖）。"""
    cols = list(df.columns)
    lines = ["| " + " | ".join(cols) + " |",
             "|" + "|".join(["---"] * len(cols)) + "|"]
    for _, r in df.iterrows():
        lines.append("| " + " | ".join(str(r[c]) for c in cols) + " |")
    return "\n".join(lines)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    df = pd.read_excel(XLSX, sheet_name=SHEET)
    n = len(df)

    missing_desc = [c for c in df.columns if c not in DESCRIPTIONS]
    if missing_desc:
        print(f"[提醒] 以下列缺人工描述，已留空：{missing_desc}")

    rows = []
    for col in df.columns:  # 保持原表列顺序
        s = df[col]
        desc, note = DESCRIPTIONS.get(col, ("", ""))
        example = next((str(v) for v in s.dropna().unique()[:1]), "")
        rows.append({
            "列名": col,
            "类型": TYPE_MAP.get(col, "文本"),
            "非空率": f"{s.notna().mean():.2%}",
            "唯一值数": int(s.nunique()),
            "示例值": example[:40],  # 截断长地址
            "含义/口径": desc,
            "质量备注": note,
        })

    dic = pd.DataFrame(rows)
    dic.to_csv(OUT_DIR / "data_dictionary.csv", index=False, encoding="utf-8-sig")

    md = ["# 数据字典 · 司马台总数据.xlsx（筛选后企业信息）",
          f"\n共 {n} 行 × {df.shape[1]} 列。生成脚本：scripts/make_data_dictionary.py",
          "（机器统计+人工口径合并，改表后重跑即更新）\n",
          md_table(dic)]
    (OUT_DIR / "data_dictionary.md").write_text("\n".join(md), encoding="utf-8")
    print(dic.to_string(index=False))
    print(f"\n已写入 {OUT_DIR}")


if __name__ == "__main__":
    main()
