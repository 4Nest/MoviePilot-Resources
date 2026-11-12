"""猪猪实验室 API 连通性热更适配器。"""

from typing import Tuple

from app.db.models.site import Site
from app.helper.site import SitesHelper
from app.modules.indexer.spider.piggo import PiggoSpider


def test_site(site: Site) -> Tuple[bool, str]:
    """合并站点资源与当前配置，通过 /me 校验猪猪长期令牌及账号权限。"""
    indexer = SitesHelper().get_indexer(site.domain) or {}
    runtime_site = {**indexer, **site.to_dict()}
    return PiggoSpider(runtime_site).test_connection()
