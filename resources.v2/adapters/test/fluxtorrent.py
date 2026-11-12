"""FluxTorrent NexusPHP 兼容层连通性热更适配器。"""

from typing import Tuple

from app.db.models.site import Site
from app.helper.site import SitesHelper
from app.modules.indexer.spider.fluxtorrent import FluxTorrentSpider


def test_site(site: Site) -> Tuple[bool, str]:
    """合并站点资源与当前配置，通过 user.json 校验开放 API 令牌。"""
    indexer = SitesHelper().get_indexer(site.domain) or {}
    runtime_site = {**indexer, **site.to_dict()}
    return FluxTorrentSpider(runtime_site).test_connection()
