from typing import Tuple

from app.core.config import settings
from app.db.models.site import Site
from app.utils.http import RequestUtils


def test_site(site: Site) -> Tuple[bool, str]:
    """
    通过 HDArea API v1 探活接口校验 API Key 与子令牌权限范围

    :param site: HDArea 站点配置对象
    :return: (是否可用, 状态描述)
    """
    if not site.apikey:
        return False, "请配置站点 API Key"
    base_url = str(site.url or "https://hdarea.club/").rstrip("/")
    res = RequestUtils(
        headers={
            "Accept": "application/json",
            "User-Agent": site.ua or settings.USER_AGENT,
            "X-API-Key": site.apikey.strip(),
        },
        proxies=settings.PROXY if site.proxy else None,
        timeout=site.timeout or 15,
    ).get_res(url=f"{base_url}/api/v1/status")
    if res is None:
        return False, "无法连接 HDArea API 服务"
    try:
        payload = res.json() or {}
    except (TypeError, ValueError):
        payload = {}
    if res.status_code != 200:
        err_msg = payload.get("message") if isinstance(payload, dict) else None
        return False, err_msg or f"错误：{res.status_code} {res.reason}"
    if not isinstance(payload, dict) or str(payload.get("code")) != "0":
        err_msg = payload.get("message") if isinstance(payload, dict) else None
        return False, err_msg or "API Key 已过期或无效"
    auth_user = (payload.get("data") or {}).get("authenticated_user") or {}
    scopes = set(auth_user.get("token_scopes") or [])
    if scopes:
        for required_scope in ("read", "download"):
            if required_scope not in scopes:
                return False, f"当前 API 令牌缺少 {required_scope} 权限"
    return True, "连接成功"
