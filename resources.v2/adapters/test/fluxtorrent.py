"""FluxTorrent NexusPHP 兼容层连通性热更适配器。"""

from typing import Tuple

from app.db.models.site import Site
from app.helper.site import SiteResourceRegistry, SitesHelper

try:
    from app.modules.indexer.spider.fluxtorrent import FluxTorrentSpider as _BuiltinFluxTorrentSpider
except ImportError:  # pragma: no cover - 兼容不含内置模块的旧版宿主
    _BuiltinFluxTorrentSpider = None


def test_site(site: Site) -> Tuple[bool, str]:
    """合并站点资源与当前配置，通过热更优先的 Spider 校验开放 API 令牌。"""
    indexer = SitesHelper().get_indexer(site.domain) or {}
    runtime_site = {**indexer, **site.to_dict()}
    spider_cls = SiteResourceRegistry.get_spider_class("FluxTorrent") or _BuiltinFluxTorrentSpider
    if spider_cls is None:
        return False, "未找到 FluxTorrent 站点适配器"
    return spider_cls(runtime_site).test_connection()
