# -*- coding: utf-8 -*-
"""新链必做③：生成标准化集群成员表（作业五要素补齐）。

在引擎产物 05_企业集群归属明细.csv 基础上补齐：
  场所ID    —— 以注册地址为代理，取 "S:" + 统一社会信用代码（一企业一行一注册地）
  数据截止  —— 2026-08-10（必做①数据字典：成立时间最大值，即数据快照日期）
  参数版本  —— dbscan_eps5km_min75_haversine（引擎 内部程序/config.json clustering 段；本组将 min_samples 50→75，理由见验证说明②）
用法：python standardize_membership.py [--input 05明细路径] [--output 输出路径]
"""
import argparse
import sys
from pathlib import Path

import pandas as pd

DEFAULT_INPUT = Path(
    r"C:\Users\宏宇\Downloads\一键换链脚本包+数据包_新链_v1.5_20260922"
    r"\脚本总包_产业集群聚类与集群指数\01_产业集群聚类\产业集群聚类脚本"
    r"\企业名录及简介_全量分析结果\05_企业集群归属明细.csv"
)
DEFAULT_OUTPUT = Path(__file__).resolve().parent.parent / "outputs" / "cluster_membership_standardized.csv"

DATA_SNAPSHOT = "2026-08-10"
PARAM_VERSION = "dbscan_eps5km_min75_haversine"


def main() -> int:
    ap = argparse.ArgumentParser(description="生成标准化集群成员表")
    ap.add_argument("--input", default=str(DEFAULT_INPUT), help="05_企业集群归属明细.csv 路径")
    ap.add_argument("--output", default=str(DEFAULT_OUTPUT), help="输出 csv 路径")
    args = ap.parse_args()

    df = pd.read_csv(args.input, encoding="utf-8-sig", dtype=str, keep_default_na=False)
    n_in = len(df)

    code = df["统一社会信用代码"].where(df["统一社会信用代码"].str.strip() != "", df["企业标识"])
    df["场所ID"] = "S:" + code
    df["数据截止"] = DATA_SNAPSHOT
    df["参数版本"] = PARAM_VERSION

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False, encoding="utf-8-sig")

    noise = int((df["集群编号"] == "NOISE").sum())
    not_in = int((df["集群状态"] == "未参与聚类").sum())
    print(f"读取 {n_in} 行 -> 写出 {len(df)} 行 x {len(df.columns)} 列")
    print(f"其中 NOISE {noise} 行；未参与聚类 {not_in} 行")
    print(f"输出: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
