# -*- coding: utf-8 -*-
"""必做① 第4步：来源清单（数据资产盘点 + 人工来源口径合并）。

探针部分：文件是否存在 / 大小 / 行数 / 列名（机器算）；
口径部分：来源、获取方式、覆盖范围、匹配依据（人工写，依据老师《需要提供的数据清单》）。
输出 outputs/source_inventory.csv 与 source_inventory.md。
"""
from pathlib import Path

import pandas as pd

from make_data_dictionary import md_table  # 同目录脚本可直接 import（脚本目录自动进 sys.path）

PKG = Path(r"C:\Users\宏宇\Downloads\一键换链脚本包+数据包_新链_v1.5_20260922\数据包_新链")
OUT_DIR = Path(__file__).resolve().parents[1] / "outputs"

# 相对路径 -> (角色, 来源/获取方式, 覆盖与匹配依据)
ASSETS = {
    "01聚类输入/司马台总数据.xlsx": ("主表·聚类底座", "数据方（老师司马台库）提供",
        "新能源与智能网联汽车链企业 38076 家；匹配键=统一社会信用代码"),
    "01聚类输入/上游企业.xlsx": ("环节子表", "脚本自动打标（主表×全国主库产业链环节）",
        "上游环节企业；打标报告见 01_上中游自动打标报告.json"),
    "01聚类输入/中游企业.xlsx": ("环节子表", "脚本自动打标", "中游环节企业"),
    "01聚类输入/政策及时间.csv": ("时序辅助", "抓取_政策候选.py 自爬（国务院政策库+三地政府 site 检索）+ 人工筛",
        "两列：政策时间,政策名称"),
    "01聚类输入/POI/北京园区类POI.csv": ("空间辅助", "数据方提供（高德 POI 结构）",
        "name/type/location；集群—园区空间关系"),
    "01聚类输入/POI/天津园区类POI.csv": ("空间辅助", "数据方提供", "同上"),
    "01聚类输入/POI/河北园区类POI.csv": ("空间辅助", "数据方提供", "同上"),
    "01聚类输入/龙头企业名单.csv": ("外部名单", "数据方提供", "14_龙头比对；匹配键=企业名称"),
    "02源料/全国企业主库.csv": ("全国主库", "老师从全国工商注册库（1949–2025）按链筛出",
        "含省份/城市/产业链环节/完整路径/评分；区域子集与自动打标的源头"),
    "02源料/专利_京津冀.csv": ("区域专利", "数据方提供", "专利↔企业匹配键=统一社会信用代码"),
    "02源料/新能源汽车与智能网联汽车_汇总统计_全国.csv": ("全国统计", "全国主库汇总", "全国口径对标"),
    "02手动补充/07_全行业基准统计.csv": ("基准分母", "生成全行业企业基准.py 自动产出", "区位熵分母"),
    "02手动补充/08_全国专利基准统计.csv": ("基准分母", "生成专利基准.py 自动产出", "专利区位熵 PLQ 分母"),
    "02手动补充/第1-10批绿色工厂名单匹配数据（2017-2025年）.zip": ("补充名单",
        "数据方名单（工信部第1–10批绿色工厂）", "PDF 已由 抽取PDF名单.py 自动抽表（含扫描件 OCR）；2017–2025"),
}


def probe_csv(path: Path) -> tuple[int, str]:
    """数数据行（不含表头）并取前6个列名。

    用 csv.reader 而非数换行符：专利摘要等字段可能含引号内换行，
    数换行会把多行字段拆成多行，导致行数虚高。
    """
    import csv
    for enc in ("utf-8-sig", "gb18030"):
        try:
            with open(path, encoding=enc, newline="") as f:
                r = csv.reader(f)
                header = next(r, [])
                n = sum(1 for _ in r)
            return n, "/".join(header[:6])
        except UnicodeDecodeError:
            continue
    return -1, "<读取失败>"


def probe(path: Path) -> tuple[str, str, str]:
    """返回 (大小, 行数, 列名摘要)；不可探测的类型给说明。"""
    size_mb = f"{path.stat().st_size / 1048576:.1f}MB"
    if path.suffix in (".xlsx", ".xlsm"):
        df = pd.read_excel(path)
        return size_mb, str(len(df)), "/".join(map(str, df.columns[:6]))
    if path.suffix == ".csv":
        rows, cols = probe_csv(path)
        return size_mb, str(rows), cols
    if path.suffix == ".zip":
        return size_mb, "-", "压缩包（PDF 名单）"
    return size_mb, "-", "-"


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rows = []
    for rel, (role, source, note) in ASSETS.items():
        p = PKG / rel
        if p.exists():
            size, n, cols = probe(p)
        else:
            size, n, cols = "[缺失]", "-", "-"
        rows.append({"文件": rel, "角色": role, "大小": size, "行数": n,
                     "列名摘要": cols, "来源/获取方式": source, "覆盖与匹配依据": note})

    inv = pd.DataFrame(rows)
    inv.to_csv(OUT_DIR / "source_inventory.csv", index=False, encoding="utf-8-sig")
    md = ["# 来源清单 · 数据包_新链（新能源与智能网联汽车 / 京津冀）",
          "\n生成脚本：scripts/build_source_inventory.py（探针自动更新，口径人工维护）\n",
          md_table(inv)]
    (OUT_DIR / "source_inventory.md").write_text("\n".join(md), encoding="utf-8")
    print(inv[["文件", "大小", "行数", "来源/获取方式"]].to_string(index=False))
    print(f"\n已写入 {OUT_DIR}")


if __name__ == "__main__":
    main()
