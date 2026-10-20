# -*- coding: utf-8 -*-
"""必做① 第1步：盘点《司马台总数据.xlsx》的结构。

只读，不改任何文件。回答三个问题：
1) 表里有哪些列、多少行？
2) 关键字段（信用代码/坐标/经营状态等）长什么样？
3) 每列缺失率多少？
"""
from pathlib import Path

import pandas as pd

XLSX = Path(r"C:\Users\宏宇\Downloads\一键换链脚本包+数据包_新链_v1.5_20260922\数据包_新链\01聚类输入\司马台总数据.xlsx")
SHEET = "筛选后企业信息"  # 脚本包手册指定的主表 sheet；若报错，先看打印出来的 sheets 列表


def probe(df: pd.DataFrame, col: str) -> None:
    """给单列画像：非空率、唯一值数、前3个示例值。列不存在就明说，不崩。"""
    if col not in df.columns:
        print(f"  [缺列] {col}")
        return
    s = df[col]
    print(f"  {col}: 非空 {s.notna().mean():.1%}, 唯一值 {s.nunique()}, 示例 {list(s.dropna().unique()[:3])}")


def main() -> None:
    xl = pd.ExcelFile(XLSX)
    print("sheets =", xl.sheet_names)
    df = xl.parse(SHEET)
    print(f"shape = {df.shape[0]} 行 x {df.shape[1]} 列\n")

    print("== 每列缺失率(%) ==")
    print((df.isna().mean() * 100).round(2).to_string())

    print("\n== 前3行 ==")
    print(df.head(3).to_string())

    print("\n== 关键字段画像 ==")
    for c in ["企业名称", "统一社会信用代码", "经营状态", "经纬度坐标",
              "注册资本", "成立时间", "核准日期", "地址", "登记机关"]:
        probe(df, c)

    code = "统一社会信用代码"
    if code in df.columns:
        dup = int(df[code].duplicated().sum())
        print(f"\n信用代码重复行数: {dup} ({dup / len(df):.2%})")


if __name__ == "__main__":
    main()
