# config.py
import os


BASE_URL = os.getenv("FEISHU_BASE_URL", "https://open.feishu.cn")
APP_ID = os.getenv("FEISHU_APP_ID", "cli_a92bfa7ab8b89cef")
APP_SECRET = os.getenv("FEISHU_APP_SECRET", "Yfi1VOYuravdLXAZ89Kh2c3b0wtXh1gS")

WIKI_NODE_TOKEN = os.getenv("FEISHU_WIKI_NODE_TOKEN", "ISvLwe1XJi97oPkXXKwcpoavnm7")  # bascnxxxx
TABLE_ID = os.getenv("FEISHU_TABLE_ID", "tbl2My5W6t0it6hY")      # tblxxxx

PAGE_SIZE = int(os.getenv("FEISHU_PAGE_SIZE", "500"))
TIMEOUT_SEC = int(os.getenv("FEISHU_TIMEOUT_SEC", "30"))