# MoviePilot-Resources (NEO)

MoviePilot NEO 的站点索引与动态适配器热更新仓库。保留上游 `resources.v2/*.so` 与 `user.sites.v2.bin` 存量二进制底座，并通过 `resources.v2/neo.sites.json` 与 `resources.v2/adapters/` 提供免发版站点热更新。

## 目录结构

- `package.v2.json`：V2 资源总清单（含存量二进制资源版本及 `neo_sites` 热更文件 SHA-256 清单）
- `resources.v2/neo.sites.json`：NEO 增量站点与覆盖规则
  - `supplements`：上游未收录的新增站点定义（支持 `alias_of` 复用既有模板）
  - `overrides`：已改版老站点的协议/分类覆盖定义
  - `rss_link_conf` / `apikey_rss_templates`：站点 RSS 自动生成规则
  - `special_site_tests`：复用既有特殊测活器的域名别名映射
  - `adapters`：自定义 API 站点的动态 `spider` / `parser` / `test` 模块映射
- `resources.v2/adapters/`：按 SHA-256 校验下发的 Python 站点适配器（`spider/*.py`、`parser/*.py`、`test/*.py`）
- `scripts/update_manifest.py`：语法校验、版本号递增与 SHA-256 清单生成工具

## 日常维护流程

1. 修改 `resources.v2/neo.sites.json`（或新增/更新 `resources.v2/adapters/` 下的模块，注意用户数据解析器类直接声明字符串 `schema = "SiteName"` 即可，无需依赖宿主枚举）。
2. 生成最新版本号与 SHA-256 清单：
   ```bash
   python3 scripts/update_manifest.py --bump patch
   ```
3. 本地校验并推送：
   ```bash
   python3 scripts/update_manifest.py --verify
   git add package.v2.json resources.v2/
   git commit -m "feat(site): 适配 xxx 站点"
   git push origin main
   ```

所有开启 `AUTO_UPDATE_RESOURCE` 的 MoviePilot NEO 实例会自动拉取、校验 SHA-256 并免重启热重载生效（也可在「系统 → 定时服务 → 站点资源包更新」手动立即触发）。
