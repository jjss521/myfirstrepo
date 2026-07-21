#!/usr/bin/env python3
from __future__ import annotations
"""
Migrate rule JSON files: add template_content and sub_modules to every item.

Handles 4 different JSON structures:
  a. Standard (water_supply, drainage):
     data["design_stages"][stage][category]["items"]
  b. With sub-containers (road):
     data["design_stages"][stage][category][sub_category]["items"]
  c. With sections wrapper (sanitation):
     data["design_stages"][stage]["sections"][category]["items"]

Uses recursive traversal — any dict with an "items" key holding a list
will be processed, regardless of nesting depth.

Idempotent: items that already have template_content are skipped.
"""

import json
import os
import re
from typing import Any

# ── Paths ──────────────────────────────────────────────────────

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RULES_DIR = os.path.join(BASE_DIR, "backend", "data", "rules")

FILES = [
    "water_supply.json",
    "drainage.json",
    "road.json",
    "sanitation.json",
]

# ── Keyword → Sub-modules mapping ─────────────────────────────
# Each entry: (tuple_of_keywords, list_of_sub_module_names)
# Keywords are matched against the item's title (substring match).
# First match wins; order matters — more specific patterns first.

KEYWORD_SUB_MODULES: list[tuple[tuple[str, ...], list[str]]] = [
    # ── 设计范围 / 依据 ──
    (("设计范围", "编制依据", "设计依据", "设计原则"), ["设计范围描述", "编制依据说明", "设计原则概述"]),

    # ── 电源 ──
    (("供电电源", "电源"), ["电源来源及电压等级", "供电方案说明", "备用电源设置"]),

    # ── 负荷 ──
    (("用电负荷", "负荷计算", "负荷估算", "负荷等级"), ["负荷等级划分", "计算参数说明", "计算结果分析"]),

    # ── 供配电系统 ──
    (("供配电系统",), ["系统接线方案", "运行方式说明", "配电方式选择"]),

    # ── 变配电 / 变电所 ──
    (("变配电", "变电所"), ["变电所位置设置", "变压器容量选择", "设备布置方案"]),

    # ── 保护和控制 ──
    (("保护和控制", "继电保护"), ["继电保护配置", "操作电源选择", "控制方式说明"]),

    # ── 计量 ──
    (("计量",), ["计量方式确定", "计量装置配置"]),

    # ── 电缆 / 管缆敷设 ──
    (("管线敷设", "电缆敷设", "管缆敷设", "电缆及管缆", "电缆及敷设", "电缆选型"),
     ["电缆选型原则", "敷设方式确定", "防火封堵措施"]),

    # ── 照明 ──
    (("照明",), ["照明标准确定", "光源选型方案", "应急照明设置"]),

    # ── 防雷 / 接地 ──
    (("防雷", "接地"), ["防雷等级确定", "接地系统设计", "等电位联结"]),

    # ── 设备选型 ──
    (("设备选型", "设备选择", "设备配置"), ["设备选型原则", "主要设备参数", "技术性能要求"]),

    # ── 监控系统 ──
    (("监控系统",), ["系统架构设计", "监控点位设置", "信号传输方案"]),

    # ── 仪表系统 ──
    (("仪表系统", "仪表"), ["仪表选型原则", "检测参数确定", "仪表布置方案"]),

    # ── 通信系统 ──
    (("通信系统", "通信"), ["通信方式选择", "综合布线方案", "设备配置"]),

    # ── 火灾自动报警 ──
    (("火灾自动报警",), ["系统形式确定", "探测选型方案", "联动控制设计"]),

    # ── 安防系统 ──
    (("安防系统",), ["系统组成确定", "防范区域划分", "管理平台设计"]),

    # ── 工业电视 / 视频 ──
    (("工业电视", "视频", "闭路电视"), ["摄像机点位布置", "传输存储方案", "显示控制方案"]),

    # ── 防爆 / 防腐 / 防护 ──
    (("防爆", "防腐", "防护等级"), ["区域划分", "设备选型要求", "防护等级确定"]),

    # ── 节能 ──
    (("节能",), ["节能措施说明", "能效指标确定"]),

    # ── 自控系统 ──
    (("自控系统",), ["系统架构设计", "硬件配置方案", "软件功能实现"]),

    # ── 弱电系统 ──
    (("弱电系统",), ["系统类型确定", "功能配置方案", "建设规模说明"]),

    # ── 智慧管控平台 ──
    (("智慧",), ["平台架构设计", "功能模块说明", "数据集成方案"]),

    # ── 有线电视 ──
    (("有线电视",), ["系统配置方案", "信号传输方式", "功能实现说明"]),

    # ── 抗震 ──
    (("抗震",), ["抗震设防标准", "支架固定方案", "设备加固措施"]),

    # ── 路灯控制 ──
    (("路灯控制", "控制方式"), ["控制策略确定", "控制设备配置", "节能运行方案"]),

    # ── 需求分析 ──
    (("需求分析",), ["业务需求梳理", "功能需求确定", "性能指标要求"]),
]

DEFAULT_SUB_MODULES = ["设计内容说明", "技术方案确定", "参数指标说明"]


def match_sub_modules(title: str) -> list[str]:
    """Return sub-module name list for a given item title.

    Matches title against keyword groups; returns names of the first
    matching group, or DEFAULT_SUB_MODULES if no keyword matches.
    """
    for keywords, names in KEYWORD_SUB_MODULES:
        for kw in keywords:
            if kw in title:
                return list(names)
    return list(DEFAULT_SUB_MODULES)


# ── Template content generation ───────────────────────────────

def generate_template_content(item: dict) -> str:
    """Generate a Chinese design-document template paragraph for an item.

    If the item has an ``example_text`` field, use it verbatim.
    Otherwise, generate a paragraph starting with "本工程" that
    incorporates key terms extracted from the item's ``requirement``.
    """
    if item.get("example_text"):
        return item["example_text"]
    requirement = item.get("requirement", "")
    title = item.get("title", "")
    return _build_template_paragraph(requirement, title)


# Mapping of requirement keywords → generated sentence templates.
# Each sentence is a stand-alone phrase (no leading "本工程") that
# will be joined with "，" into the final paragraph.
_REQUIREMENT_SENTENCE_MAP: list[tuple[str, str]] = [
    # ── Design scope & basis ──
    (r"设计范围", "设计范围包括XXXX"),
    (r"设计内容", "设计内容包括XXXX"),
    (r"设计依据|编制依据", "设计依据主要为《XXXX》GB XXXX等现行国家标准及规范"),
    (r"设计原则", "设计遵循安全可靠、技术先进、经济合理的原则"),
    (r"设计标准", "设计标准按现行国家及行业规范执行"),

    # ── Power supply ──
    (r"供电电源", "供电电源引自XX变电站XXkV专线"),
    (r"电压等级", "电压等级采用XXkV/XXkV"),
    (r"备用电源", "备用电源采用XX方式，确保重要负荷供电可靠性"),
    (r"(?<!保安)电源(?!来源)", "电源引自XX变电站"),
    (r"保安电源", "保安电源采用XX发电机组"),

    # ── Load ──
    (r"用电负荷", "用电负荷主要包括XXXX、XXXX等工艺设备"),
    (r"负荷等级|负荷性质", "负荷等级根据工艺要求和规范划分为XX级和XX级"),
    (r"用电容量|总装机", "总装机容量约XXXkW，计算负荷约XXXkVA"),
    (r"负荷班制", "负荷班制为XX班制运行"),

    # ── Distribution & substation ──
    (r"供配电系统", "供配电系统采用XX接线方式"),
    (r"配电方式|配电系统", "配电方式采用放射式与树干式相结合"),
    (r"变配电|变电所", "变配电所设置于厂区适当位置，变压器选用XX型节能干式变压器"),
    (r"变压器", "变压器选用XX型节能干式变压器，容量按计算负荷确定"),
    (r"一次系统|接线形式", "一次系统接线形式根据负荷性质及可靠性要求确定"),
    (r"运行方式", "各系统运行方式根据负荷可靠性要求确定"),

    # ── Protection & control ──
    (r"继电保护", "继电保护采用微机型综合保护装置"),
    (r"操作电源", "操作电源采用直流XXV系统"),
    (r"电机启动|电机设备", "电机设备采用XX启动方式"),
    (r"控制方式|控制联锁", "控制方式采用就地/远程控制，关键设备设置联锁保护"),
    (r"低压配电.*保护", "低压配电线路按规范要求设置过载和短路保护"),

    # ── Metering & compensation ──
    (r"计量", "计量方式按电力部门要求设置商业计量"),
    (r"功率因数补偿", "功率因数补偿采用低压集中自动补偿，补偿后功率因数不低于0.95"),

    # ── Cables ──
    (r"电缆.*敷设|管线敷设|管缆", "电缆敷设采用电缆沟、桥架与穿管相结合的方式"),
    (r"电缆选型", "电缆选型根据载流量和敷设环境条件确定"),
    (r"防火封堵", "电缆穿越防火分区处设置防火封堵"),

    # ── Lighting ──
    (r"照明.*光源|光源选择", "光源选用高效LED灯具"),
    (r"照度标准", "各场所照度标准按现行国家规范执行"),
    (r"应急照明", "应急照明按规范要求设置，持续供电时间不少于XXmin"),
    (r"照明", "照明设计满足各场所照度标准及功能要求"),

    # ── Equipment selection ──
    (r"设备选型|电气设备", "电气设备选型遵循安全可靠、技术先进、经济合理的原则"),
    (r"新技术应用", "积极采用节能型变压器、智能配电终端等新技术"),

    # ── Lightning & grounding ──
    (r"防雷", "防雷设计按第X类防雷建筑物执行"),
    (r"接地", "接地系统采用TN-S系统，接地电阻不大于XΩ"),
    (r"等电位", "等电位联结按规范要求设置"),

    # ── Explosion / corrosion protection ──
    (r"防爆", "爆炸危险区域电气设备按防爆等级要求选型"),
    (r"防腐", "腐蚀性环境区域电气设备按防腐等级要求选型"),
    (r"防护等级", "设备防护等级根据安装环境确定"),

    # ── Seismic ──
    (r"抗震|机电抗震", "机电抗震按现行抗震设计规范要求执行"),

    # ── Monitoring & control systems ──
    (r"监控系统", "监控系统采用XX架构，实现全场工艺参数在线监测"),
    (r"仪表系统|仪表设置", "仪表选型遵循可靠、适用、经济的原则"),
    (r"工业电视", "工业电视系统采用高清网络摄像机，覆盖场区重点区域"),
    (r"安防系统", "安防系统覆盖场区出入口及重点区域"),
    (r"通信|综合布线", "通信及综合布线系统按功能需求配置"),
    (r"火灾自动报警", "火灾自动报警系统按集中报警系统设计"),

    # ── Smart systems ──
    (r"智慧.*平台", "智慧管理平台实现全场数据集成与智能运维"),
    (r"需求分析", "根据工程特点和运营需求进行系统功能需求分析"),
    (r"内容及目标|建设目标", "建设目标为实现全场自动化、信息化管理"),

    # ── Energy saving ──
    (r"节能", "节能措施包括选用高效设备及优化运行控制策略"),
]

# Max sentences in generated template to keep it concise.
MAX_TEMPLATE_SENTENCES = 5


def _build_template_paragraph(requirement: str, title: str) -> str:
    """Build a "本工程…" paragraph from requirement keywords."""
    # Normalize: replace Chinese punctuation separators with commas
    req = requirement.replace("；", "，").replace("、", "，").replace("。", "，").rstrip("， ")

    sentences: list[str] = []
    for pattern, template in _REQUIREMENT_SENTENCE_MAP:
        if re.search(pattern, req):
            if template not in sentences:  # deduplicate
                sentences.append(template)

    # Limit number of sentences
    if len(sentences) > MAX_TEMPLATE_SENTENCES:
        sentences = sentences[:MAX_TEMPLATE_SENTENCES]

    if not sentences:
        # Fallback when no keywords matched
        sentences = [f"根据{title}要求，结合本工程实际情况进行设计"]

    return "本工程" + "，".join(sentences) + "。"


# ── Recursive item processor ──────────────────────────────────

def process_items_recursive(obj: Any) -> int:
    """Recursively find all ``items`` arrays in the JSON tree and enrich them.

    For every dict that has an ``"items"`` key whose value is a list,
    each element in that list gets ``template_content`` and ``sub_modules``
    added (only if not already present — idempotent).

    Returns the number of items actually updated (had template_content added).
    """
    count = 0

    if isinstance(obj, dict):
        # Check for items list at this level
        items = obj.get("items")
        if isinstance(items, list):
            for item in items:
                if isinstance(item, dict):
                    if "template_content" not in item:
                        item["template_content"] = generate_template_content(item)
                        count += 1
                    if "sub_modules" not in item:
                        title = str(item.get("title", ""))
                        names = match_sub_modules(title)
                        item["sub_modules"] = [
                            {"name": name, "template_content": ""}
                            for name in names
                        ]

        # Recurse into all values
        for value in obj.values():
            count += process_items_recursive(value)

    elif isinstance(obj, list):
        for elem in obj:
            count += process_items_recursive(elem)

    return count


# ── Main ──────────────────────────────────────────────────────

def main() -> None:
    total_updated = 0

    for file_name in FILES:
        file_path = os.path.join(RULES_DIR, file_name)

        if not os.path.exists(file_path):
            print(f"  [SKIP] {file_name} — file not found at {file_path}")
            continue

        # Read
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Process
        updated = process_items_recursive(data)
        total_updated += updated

        # Write back
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"  [DONE] {file_name} — {updated} items enriched")

    print(f"\nMigration complete. {total_updated} total items enriched across {len(FILES)} files.")


if __name__ == "__main__":
    main()
