# feishu_api.py
import time
from typing import List, Optional, Dict, Any

import requests


def get_access_token(app_id: str, app_secret: str, base_url: str, timeout_sec: int = 30) -> str:
    """获取 tenant_access_token"""
    url = f"{base_url}/open-apis/auth/v3/tenant_access_token/internal"
    resp = requests.post(url, json={"app_id": app_id, "app_secret": app_secret}, timeout=timeout_sec)
    resp.raise_for_status()
    data = resp.json()
    if data.get("code") != 0:
        raise RuntimeError(f"获取 token 失败：{data}")
    return data["tenant_access_token"]


def get_bitable_app_token_from_wiki(node_token: str, access_token: str, base_url: str, timeout_sec: int = 30) -> str:
    """
    wiki 场景：通过 node_token 获取多维表格 app_token（obj_token）
    """
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
    """读取多维表格 records（自动翻页）"""
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