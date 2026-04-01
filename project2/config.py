# config.py
# 配置区：所有可调参数集中在此处，敏感信息从 .env 文件读取（不提交到 git）。
import os
from dotenv import load_dotenv

# 加载 .env 文件（文件不存在时静默跳过，依赖系统环境变量）
load_dotenv()

# ============================================================
# ========================= 配置区 ==========================
# ============================================================

# 飞书 API 基础地址
BASE_URL = os.getenv("FEISHU_BASE_URL", "https://open.feishu.cn")

# 飞书应用凭证（从 .env 或环境变量读取，不在代码里硬编码）
APP_ID = os.getenv("FEISHU_APP_ID", "")
APP_SECRET = os.getenv("FEISHU_APP_SECRET", "")

# 数据来源：英雄技能配置表（Wiki 节点 Token + Table ID）
SOURCE_WIKI_NODE_TOKEN = os.getenv("FEISHU_SOURCE_WIKI_NODE_TOKEN", "")
SOURCE_TABLE_ID = os.getenv("FEISHU_SOURCE_TABLE_ID", "")

# 写回目标：英雄信息汇总结果表（Wiki 节点 Token + Table ID）
RESULT_WIKI_NODE_TOKEN = os.getenv("FEISHU_RESULT_WIKI_NODE_TOKEN", "")
RESULT_TABLE_ID = os.getenv("FEISHU_RESULT_TABLE_ID", "")

# 学生姓名（用于结果表防重复提交的唯一标识）
STUDENT_NAME = os.getenv("STUDENT_NAME", "")

# 分页大小（每页最多拉取的记录条数）
PAGE_SIZE = 500

# HTTP 请求超时秒数
TIMEOUT_SEC = 30
