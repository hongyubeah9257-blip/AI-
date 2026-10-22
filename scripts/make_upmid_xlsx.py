# -*- coding: utf-8 -*-
"""新链必做③ 输入准备：从主表生成上/中游企业 xlsx（引擎画图 2-14/15 用，15 列接口格式）。"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from seg_rules import MASTER, primary_seg

TOOLKIT_COLS = ["企业名称", "法定代表人", "行业门类", "企业类型", "成立时间", "经营状态",
                "注册资本", "注册资本币种", "经营期限自", "经营期限至", "登记机关", "核准日期",
                "经纬度坐标", "地址", "统一社会信用代码"]
ENGINE_INPUT = Path(
    r"C:\Users\宏宇\Downloads\一键换链脚本包+数据包_新链_v1.5_20260922"
    r"\脚本总包_产业集群聚类与集群指数\01_产业集群聚类\产业集群聚类脚本"
    r"\输入数据\新一代信息技术"
)


def main() -> None:
    df = pd.read_csv(MASTER, encoding="utf-8-sig", dtype=str)
    df["_环节"] = df["产业链环节"].map(primary_seg)
    for seg, fname in [("上游", "上游企业.xlsx"), ("中游", "中游企业.xlsx")]:
        g = df[df["_环节"] == seg]
        tk = pd.DataFrame({
            "企业名称": g["企业名称"], "法定代表人": "", "行业门类": "", "企业类型": "",
            "成立时间": g["成立时间"], "经营状态": g["经营状态"],
            "注册资本": g["注册资本"], "注册资本币种": g["注册资本币种"],
            "经营期限自": "", "经营期限至": "", "登记机关": "", "核准日期": "",
            "经纬度坐标": g["纬度"].astype(str) + "," + g["经度"].astype(str), "地址": g["地址"],
            "统一社会信用代码": g["统一社会信用代码"],
        })[TOOLKIT_COLS].sort_values("企业名称")
        tk.to_excel(ENGINE_INPUT / fname, index=False)
        print(f"{fname}: {len(tk):,} 行")


if __name__ == "__main__":
    main()
