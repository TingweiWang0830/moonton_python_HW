# main.py
import logging
from collections import Counter
from typing import Any, Dict, List, Optional, Tuple

from apscheduler.schedulers.blocking import BlockingScheduler

from config import (
    BASE_URL, APP_ID, APP_SECRET,
    SOURCE_WIKI_NODE_TOKEN, SOURCE_TABLE_ID,
    RESULT_WIKI_NODE_TOKEN, RESULT_TABLE_ID,
    STUDENT_NAME, PAGE_SIZE, TIMEOUT_SEC
)
from feishu_api import (
    get_access_token,
    get_bitable_app_token_from_wiki,
    get_all_records,
    search_records_by_text,
    create_record,
    update_record,
)

# 日志配置：同时输出到屏幕和 task.log 文件
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("task.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)


def pick_field_name(sample_fields: Dict[str, Any], candidates: List[str]) -> Optional[str]:
    keys = [str(k) for k in sample_fields.keys()]
    for kw in candidates:
        for k in keys:
            if kw in k:
                return k
    return None


def safe_str(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, str):
        return v.strip()
    if isinstance(v, (int, float)):
        return str(v).strip()
    if isinstance(v, list):
        parts = []
        for x in v:
            s = safe_str(x)
            if s:
                parts.append(s)
        return ";".join(parts).strip()
    if isinstance(v, dict):
        for k in ("text", "value", "name", "id"):
            if k in v:
                return safe_str(v.get(k))
        return ""
    return str(v).strip()


def analyze_source_table(records: List[dict]) -> Tuple[int, Counter, Counter]:
    """
    基于你截图字段：
    - 英雄ID：数字
    - 英雄职业：中文（战士/坦克/刺客/法师/射手/辅助）
    - 技能类型：中文（普通攻击/主动技能/被动技能/其他）
    返回：
      (总英雄数, 职业Counter, 技能类型Counter)
    """
    if not records:
        return 0, Counter(), Counter()

    sample_fields = records[0].get("fields", {})
    hero_id_field = pick_field_name(sample_fields, ["英雄ID", "ID", "HeroID"])
    job_field = pick_field_name(sample_fields, ["英雄职业", "职业"])
    skill_type_field = pick_field_name(sample_fields, ["技能类型", "SkillType"])

    hero_seen = set()
    job_counter = Counter()
    skill_counter = Counter()

    for item in records:
        fields = item.get("fields", {})

        hid = safe_str(fields.get(hero_id_field)) if hero_id_field else ""
        job = safe_str(fields.get(job_field)) if job_field else ""
        st = safe_str(fields.get(skill_type_field)) if skill_type_field else ""

        # 英雄去重统计职业
        if hid:
            if hid not in hero_seen:
                hero_seen.add(hid)
                job_counter[job if job else "未知"] += 1

        # 技能类型按记录统计
        if st:
            skill_counter[st] += 1

    return len(hero_seen), job_counter, skill_counter


def format_counter_line(counter: Counter) -> str:
    """
    按作业要求：用 | 分隔
    例：坦克:8|战士:12|刺客:6
    """
    if not counter:
        return ""
    return "|".join([f"{k}:{v}" for k, v in counter.most_common()])


def upsert_result_row(
    result_app_token: str,
    result_table_id: str,
    access_token: str,
    student_name: str,
    total_heroes: int,
    job_counter: Counter,
    skill_counter: Counter,
):
    """
    每人只写一行：
    - 先按“学生姓名”查
    - 有则更新，无则新增
    """
    # 目标表字段名（按你截图）
    FIELD_STUDENT = "学生姓名"
    FIELD_TOTAL = "总英雄数"
    FIELD_JOB = "职业分布"
    FIELD_SKILL = "技能分布"
    FIELD_TOP_JOB = "职业占比最高"

    job_text = format_counter_line(job_counter)
    skill_text = format_counter_line(skill_counter)

    top_job = ""
    if job_counter:
        top_job = job_counter.most_common(1)[0][0]

    fields_payload = {
        FIELD_STUDENT: student_name,
        FIELD_TOTAL: total_heroes,
        FIELD_JOB: job_text,
        FIELD_SKILL: skill_text,
        FIELD_TOP_JOB: top_job,
    }

    # 1) 查是否已有该学生记录
    existed = search_records_by_text(
        app_token=result_app_token,
        table_id=result_table_id,
        access_token=access_token,
        base_url=BASE_URL,
        field_name=FIELD_STUDENT,
        text_value=student_name,
        timeout_sec=TIMEOUT_SEC,
    )

    # 2) update or create
    if existed:
        record_id = existed[0]["record_id"]
        update_record(
            app_token=result_app_token,
            table_id=result_table_id,
            record_id=record_id,
            access_token=access_token,
            base_url=BASE_URL,
            fields=fields_payload,
            timeout_sec=TIMEOUT_SEC,
        )
        return "update"
    else:
        create_record(
            app_token=result_app_token,
            table_id=result_table_id,
            access_token=access_token,
            base_url=BASE_URL,
            fields=fields_payload,
            timeout_sec=TIMEOUT_SEC,
        )
        return "create"


def main():
    # 1) token
    token = get_access_token(APP_ID, APP_SECRET, base_url=BASE_URL, timeout_sec=TIMEOUT_SEC)
    logger.info("✅ 成功获取访问令牌")

    # 2) source：wiki -> app_token -> records
    source_app_token = get_bitable_app_token_from_wiki(SOURCE_WIKI_NODE_TOKEN, token, base_url=BASE_URL, timeout_sec=TIMEOUT_SEC)
    source_records = get_all_records(
        app_token=source_app_token,
        table_id=SOURCE_TABLE_ID,
        access_token=token,
        base_url=BASE_URL,
        page_size=PAGE_SIZE,
        timeout_sec=TIMEOUT_SEC,
    )
    logger.info(f"✅ 成功读取来源表 {len(source_records)} 条记录")

    total_heroes, job_counter, skill_counter = analyze_source_table(source_records)

    # 3) result：wiki -> app_token
    result_app_token = get_bitable_app_token_from_wiki(RESULT_WIKI_NODE_TOKEN, token, base_url=BASE_URL, timeout_sec=TIMEOUT_SEC)

    # 4) upsert 写回
    action = upsert_result_row(
        result_app_token=result_app_token,
        result_table_id=RESULT_TABLE_ID,
        access_token=token,
        student_name=STUDENT_NAME,
        total_heroes=total_heroes,
        job_counter=job_counter,
        skill_counter=skill_counter,
    )

    logger.info("✅ 写回结果表完成：%s", "更新" if action == "update" else "新增")
    logger.info("—— 写入内容预览 ——")
    logger.info("学生姓名：%s", STUDENT_NAME)
    logger.info("总英雄数：%s", total_heroes)
    logger.info("职业分布：%s", format_counter_line(job_counter))
    logger.info("技能分布：%s", format_counter_line(skill_counter))
    logger.info("职业占比最高：%s", job_counter.most_common(1)[0][0] if job_counter else "")


if __name__ == "__main__":
    from datetime import datetime
    scheduler = BlockingScheduler()
    scheduler.add_job(main, "interval", minutes=2, id="hero_sync", next_run_time=datetime.now())
    logger.info("定时任务已启动，每 2 分钟执行一次（Ctrl+C 退出）")
    scheduler.start()