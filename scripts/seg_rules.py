# -*- coding: utf-8 -*-
"""必做② 公共规则：新链（新一代信息技术/网络安全与工业互联网）4 环节口径与关键词基线规则。

环节方案（课程要求 4–8 个）：采用数据原生 4 环节——
  上游 / 中游 / 下游 / 配套服务（路径中作"相关支撑服务"，同一口径）
数据环节主口径：产业链环节列首个值（多标签 2,391 家，6.2%，见 quality_report）。
节点口径：产业链完整路径首条（" | "分隔多路径）。
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MASTER = ROOT.parent / "01_必做_感知模块" / "outputs" / "master_clean.csv"
NATIONAL = ROOT.parent / "原料" / "新一代信息技术全国企业数据.csv"
OUT_DIR = ROOT / "outputs"

SEG4 = ["上游", "中游", "下游", "配套服务"]
# 路径 L2 与环节列的别名统一（数据内 1:1，见 10/21 探查）
SEG_ALIAS = {"相关支撑服务": "配套服务"}

# 关键词基线规则（仅看企业名称；顺序即优先级，先专用后通用）
# 上游＝技术与数据资源+基础硬件；中游＝通用安全产品/解决方案；下游＝工业互联网主体与行业应用；配套服务＝检测/咨询等支撑
RULES = [
    ("上游", ["芯片", "半导体", "集成电路", "密码", "工控", "传感器", "模组",
           "通信设备", "电子元器件", "仪器仪表", "变频器", "伺服", "PLC", "DCS",
           "SCADA", "可信计算", "威胁情报"]),
    ("中游", ["网络安全", "信息安全", "数据安全", "数字安全", "网安", "态势感知", "终端安全",
           "身份认证", "身份安全", "安全审计", "网闸", "防火墙", "入侵检测",
           "防病毒", "漏洞", "安全产品", "安全技术有限公司", "安全技术", "安全科技"]),
    ("下游", ["工业互联网", "产业互联网", "智能制造", "智能工厂", "智慧工厂",
           "数字工厂", "标识解析"]),
    ("配套服务", ["检测", "检验", "测评", "评估", "认证", "咨询", "培训", "运维",
             "应急响应", "监理"]),
]

# 上下文规则：名称含"安全"但语境为生产/工程安全的，不进中游（如 安全技术工程=生产安全服务→配套）
CONTEXT_RULES = [
    ("配套服务", "安全", ["生产", "工程", "消防", "评价", "应急"]),
]

CURRENT_YEAR = 2026  # 数据快照 2026-08-10（必做①）
CAP_TIERS = [("微型≤100万", -1, 100), ("小型100-1000万", 100, 1000),
             ("中型1000万-1亿", 1000, 10000), ("大型>1亿", 10000, None)]
AGE_BINS = [("<5年", 0, 5), ("5-10年", 5, 10), ("10-20年", 10, 20), ("≥20年", 20, None)]

# 北京/天津的"所属城市"为区县级 → 直辖市；河北保持地级市
def norm_city(prov: str, city: str) -> str:
    if prov in ("北京市", "天津市"):
        return prov
    return city


def primary_seg(s: str):
    seg = str(s).split("/")[0].strip()
    return SEG_ALIAS.get(seg, seg) if seg else None


def path_primary(p: str):
    """首条路径 → (环节, 中类, 节点)；节点缺失给中类名。"""
    parts = [x.strip() for x in str(p).split(" | ")[0].split(" > ")]
    if len(parts) < 3:
        return None, None, None
    seg = SEG_ALIAS.get(parts[1], parts[1])
    mid = parts[2]
    leaf = parts[3] if len(parts) > 3 else mid
    return seg, mid, leaf


def classify(name: str):
    if not isinstance(name, str):
        return None
    for seg, ctx, kws in CONTEXT_RULES:
        if ctx in name and any(kw in name for kw in kws):
            return seg
    for seg, kws in RULES:
        for kw in kws:
            if kw in name:
                return seg
    return None
