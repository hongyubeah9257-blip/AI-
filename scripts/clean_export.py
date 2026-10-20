# -*- coding: utf-8 -*-
"""必做① 第5步：导出清洗后企业表 outputs/master_clean.csv。

原则：只增不删——原始 15 列全保留，新增 4 个辅助列：
  _纬度 / _经度      坐标解析（本表纬度在前）
  _在京津冀界内      是否落在 01 引擎 bbox 内（出界企业是合法的外地链上企业，标记不删除）
  _疑似重名          同名不同信用代码
  _成立年            供任务①集群-年面板
原始数据不可静默修改；出界/重名只标记，处置权留给分析者。
"""
from pathlib import Path

import pandas as pd

XLSX = Path(r"C:\Users\宏宇\Downloads\一键换链脚本包+数据包_新链_v1.5_20260922\数据包_新链\01聚类输入\司马台总数据.xlsx")
SHEET = "筛选后企业信息"
OUT_DIR = Path(__file__).resolve().parents[1] / "outputs"

LAT_MIN, LAT_MAX = 35.5, 42.7
LON_MIN, LON_MAX = 113.3, 120.0


def parse_coord(s):
    if not isinstance(s, str):
        return None, None
    parts = s.replace("，", ",").split(",")
    if len(parts) != 2:
        return None, None
    try:
        return float(parts[0]), float(parts[1])
    except ValueError:
        return None, None


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    df = pd.read_excel(XLSX, sheet_name=SHEET)

    latlon = df["经纬度坐标"].apply(parse_coord)
    df["_纬度"] = [x[0] for x in latlon]
    df["_经度"] = [x[1] for x in latlon]
    df["_在京津冀界内"] = (df["_纬度"].between(LAT_MIN, LAT_MAX)
                     & df["_经度"].between(LON_MIN, LON_MAX))
    df["_疑似重名"] = df["企业名称"].duplicated(keep=False)
    df["_成立年"] = pd.to_datetime(df["成立时间"], errors="coerce").dt.year

    out = OUT_DIR / "master_clean.csv"
    df.to_csv(out, index=False, encoding="utf-8-sig")
    print(f"行数={len(df)}, 列数={df.shape[1]}（原15列+新增5列）")
    print(f"界内={int(df['_在京津冀界内'].sum())}, 界外={int((~df['_在京津冀界内']).sum())}"
          f"（含坐标缺失 {int(df['_纬度'].isna().sum())}）")
    print(f"疑似重名={int(df['_疑似重名'].sum())} 行")
    print(f"已写入 {out}")


if __name__ == "__main__":
    main()
