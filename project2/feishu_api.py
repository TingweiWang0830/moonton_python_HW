# feishu_api.py
import time
from typing import List, Optional, Dict, Any

import requests


def get_access_token(app_id: str, app_secret: str, base_url: str, timeout_sec: int = 30) -> str:
    url = f"{base_url}/open-apis/auth/v3/tenant_access_token/internal"
    resp = requests.post(url, json={"app_id": app_id, "app_secret": app_secret}, timeout=timeout_sec)
    resp.raise_for_status()
    data = resp.json()
    if data.get("code") != 0:
        raise RuntimeError(f"获取 token 失败：{data}")
    return data["tenant_access_token"]


def get_bitable_app_token_from_wiki(node_token: str, access_token: str, base_url: str, timeout_sec: int = 30) -> str:
    url = f"{base_url}/open-apis/wiki/v2/spaces/get_node"
    headers = {"Authorization": f"Bearer {access_token}"}
    resp = requests.get(url, headers=headers, params={"token": node_token}, timeout=timeout_sec)
    resp.raise_for_status()
    data = resp.json()
    if data.get("code") != 0:
        raise RuntimeError(f"get_node 失败：{data}")

    node = data["data"]["node"]
    if node.get("obj_type") != "bitable":
        raise RuntimeError(f"该节点不是 bitable：obj_type={node.get('obj_type')}")
    return node["obj_token"]


def get_all_records(
    app_token: str,
    table_id: str,
    access_token: str,
    base_url: str,
    page_size: int = 500,
    timeout_sec: int = 30,
    sleep_sec: float = 0.1,
) -> List[dict]:
    url = f"{base_url}/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records"
    headers = {"Authorization": f"Bearer {access_token}"}

    all_items: List[dict] = []
    page_token: Optional[str] = None

    while True:
        params = {"page_size": page_size}
        if page_token:
            params["page_token"] = page_token

        resp = requests.get(url, headers=headers, params=params, timeout=timeout_sec)
        resp.raise_for_status()
        data = resp.json()
        if data.get("code") != 0:
            raise RuntimeError(f"读取 records 失败：{data}")

        all_items.extend(data["data"].get("items", []))

        if not data["data"].get("has_more", False):
            break
        page_token = data["data"].get("page_token")
        if sleep_sec:
            time.sleep(sleep_sec)

    return all_items


def search_records_by_text(
    app_token: str,
    table_id: str,
    access_token: str,
    base_url: str,
    field_name: str,
    text_value: str,
    page_size: int = 50,
    timeout_sec: int = 30,
) -> List[dict]:
    """
    用 bitable search API 按文本字段精确查找记录（用于“学生姓名”去重）
    """
    url = f"{base_url}/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records/search"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json; charset=utf-8",
    }
    payload = {
        "page_size": page_size,
        "filter": {
            "conjunction": "and",
            "conditions": [
                {
                    "field_name": field_name,
                    "operator": "is",
                    "value": [text_value],
                }
            ]
        }
    }

    resp = requests.post(url, headers=headers, json=payload, timeout=timeout_sec)
    resp.raise_for_status()
    data = resp.json()
    if data.get("code") != 0:
        raise RuntimeError(f"search 失败：{data}")

    return data["data"].get("items", [])


def create_record(
    app_token: str,
    table_id: str,
    access_token: str,
    base_url: str,
    fields: Dict[str, Any],
    timeout_sec: int = 30,
) -> str:
    """
    新增一条记录，返回 record_id
    """
    url = f"{base_url}/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json; charset=utf-8",
    }
    payload = {"fields": fields}

    resp = requests.post(url, headers=headers, json=payload, timeout=timeout_sec)
    resp.raise_for_status()
    data = resp.json()
    if data.get("code") != 0:
        raise RuntimeError(f"create 失败：{data}")

    return data["data"]["record"]["record_id"]


def update_record(
    app_token: str,
    table_id: str,
    record_id: str,
    access_token: str,
    base_url: str,
    fields: Dict[str, Any],
    timeout_sec: int = 30,
) -> None:
    """
    更新一条记录
    """
    url = f"{base_url}/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records/{record_id}"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json; charset=utf-8",
    }
    payload = {"fields": fields}

    resp = requests.put(url, headers=headers, json=payload, timeout=timeout_sec)
    resp.raise_for_status()
    data = resp.json()
    if data.get("code") != 0:
        raise RuntimeError(f"update 失败：{data}")