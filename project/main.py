# main.py
# 作业A：飞书数据读取与分析（基础版）
# 输出格式对齐你截图：总英雄数量、职业分布（按英雄去重）、技能类型分布（按记录统计）
#
# 依赖：requests（pip install requests）

from collections import Counter
from typing import Any, Dict, List, Optional

from project2.config import (
    BASE_URL,
    APP_ID,
    APP_SECRET,
    WIKI_NODE_TOKEN,
    TABLE_ID,
    PAGE_SIZE,
    TIMEOUT_SEC,
)
from feishu_api import (
    get_access_token,
    get_bitable_app_token_from_wiki,
    get_all_records,
)


def pick_field_name(sample_fields: Dict[str, Any], candidates: List[str]) -> Optional[str]:
    """
    在 fields 的 key 里，用“包含匹配”找到字段名。
    例：候选 ["英雄ID","ID"]，只要 key 里包含 "英雄ID" 就命中。
    """
    keys = [str(k) for k in sample_fields.keys()]
    for kw in candidates:
        for k in keys:
            if kw in k:
                return k
    return None


def safe_str(v: Any) -> str:
    """把字段值转成可统计的字符串（兼容 None、数字、数组、字典）"""
    if v is None:
        return ""
    # 飞书单选/多选很多时候直接是字符串；也可能是 list/dict
    if isinstance(v, str):
        return v.strip()
    if isinstance(v, (int, float)):
        return str(v).strip()
    if isinstance(v, list):
        # 多选可能是 ["战士","坦克"] 或 [{"text":...}]
        parts = []
        for x in v:
            s = safe_str(x)
            if s:
                parts.append(s)
        return ";".join(parts).strip()
    if isinstance(v, dict):
        # 常见 {"text": "..."} 或 {"value": "..."}
        for k in ("text", "value", "name", "id"):
            if k in v:
                return safe_str(v.get(k))
        return ""
    return str(v).strip()


def analyze_heroes(records: List[dict]) -> str:
    """
    统计逻辑（对齐你飞书表结构）：
    - 总英雄数量：按“英雄ID”去重
    - 职业分布：按英雄维度统计（同一个英雄只统计一次职业）
    - 技能类型分布：按记录维度统计（每条记录算一次）
    """
    if not records:
        return (
            "========== 英雄数据分析报告 ==========\n"
            "（无记录）\n"
            "====================================\n"
        )

    sample_fields = records[0].get("fields", {})

    # 你的表字段名就是这些（截图里很清楚），这里仍做“容错匹配”
    hero_id_field = pick_field_name(sample_fields, ["英雄ID", "ID", "HeroID"])
    job_field = pick_field_name(sample_fields, ["英雄职业", "职业"])
    skill_type_field = pick_field_name(sample_fields, ["技能类型", "SkillType"])

    hero_seen = set()
    job_counter = Counter()
    skill_counter = Counter()

    for item in records:
        fields = item.get("fields", {})

        hero_id_val = fields.get(hero_id_field) if hero_id_field else None
        job_val = fields.get(job_field) if job_field else None
        skill_val = fields.get(skill_type_field) if skill_type_field else None

        # 1) 英雄去重（职业按英雄维度统计）
        hid = safe_str(hero_id_val)
        if hid:
            if hid not in hero_seen:
                hero_seen.add(hid)

                job = safe_str(job_val)
                if not job:
                    job = "未知"
                # 你的表“英雄职业”是单选中文（战士/坦克/...），直接统计
                job_counter[job] += 1

        # 2) 技能类型分布（按记录统计）
        st = safe_str(skill_val)
        if st:
            skill_counter[st] += 1

    total_heroes = len(hero_seen)

    # 组装输出（格式对齐你截图）
    lines = []
    lines.append("========== 英雄数据分析报告 ==========")
    lines.append("")
    lines.append("✅ 成功获取访问令牌")
    lines.append(f"✅ 成功读取 {len(records)} 条记录")
    lines.append("")
    lines.append("【基本统计】")
    lines.append(f"总英雄数量：{total_heroes}")
    lines.append("")
    lines.append("【职业分布】")
    if total_heroes == 0:
        lines.append("（无数据）")
    else:
        for job, cnt in job_counter.most_common():
            pct = (cnt / total_heroes * 100) if total_heroes else 0.0
            lines.append(f"{job}：{cnt}个（{pct:.1f}%）")

    lines.append("")
    lines.append("【技能类型分布】")
    if sum(skill_counter.values()) == 0:
        lines.append("（无数据）")
    else:
        for t, cnt in skill_counter.most_common():
            lines.append(f"{t}：{cnt}个")

    lines.append("")
    lines.append("====================================")
    return "\n".join(lines)


def main():
    # 1) 获取 tenant_access_token
    token = get_access_token(APP_ID, APP_SECRET, base_url=BASE_URL, timeout_sec=TIMEOUT_SEC)
    print("✅ 成功获取访问令牌")

    # 2) wiki node_token -> bitable app_token（obj_token）
    app_token = get_bitable_app_token_from_wiki(
        node_token=WIKI_NODE_TOKEN,
        access_token=token,
        base_url=BASE_URL,
        timeout_sec=TIMEOUT_SEC,
    )

    # 3) 读取多维表格 records
    records = get_all_records(
        app_token=app_token,
        table_id=TABLE_ID,
        access_token=token,
        base_url=BASE_URL,
        page_size=PAGE_SIZE,
        timeout_sec=TIMEOUT_SEC,
    )
    print(f"✅ 成功读取 {len(records)} 条记录")

    # 4) 分析并打印
    print(analyze_heroes(records))


if __name__ == "__main__":
    main()