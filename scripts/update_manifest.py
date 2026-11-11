#!/usr/bin/env python3
"""校验并更新 MoviePilot-Resources NEO 增量资源包清单与 SHA-256 摘要。"""

import argparse
import ast
import hashlib
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
PACKAGE_V2_PATH = REPO_ROOT / "package.v2.json"
NEO_SITES_PATH = REPO_ROOT / "resources.v2" / "neo.sites.json"
ADAPTERS_DIR = REPO_ROOT / "resources.v2" / "adapters"


def compute_sha256(path: Path) -> str:
    """计算文件的 SHA-256 十六进制摘要。"""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def bump_semver(version: str, part: str) -> str:
    """按 major/minor/patch 递增语义化版本号。"""
    segs = [int(x) for x in version.strip().split(".")]
    while len(segs) < 3:
        segs.append(0)
    if part == "major":
        return f"{segs[0] + 1}.0.0"
    if part == "minor":
        return f"{segs[0]}.{segs[1] + 1}.0"
    return f"{segs[0]}.{segs[1]}.{segs[2] + 1}"


def collect_and_validate_files() -> tuple[dict, dict[str, dict[str, str]]]:
    """校验 neo.sites.json 与所有适配器 Python 语法并收集文件清单。"""
    if not NEO_SITES_PATH.is_file():
        raise FileNotFoundError(f"Missing {NEO_SITES_PATH}")
    neo_cfg = json.loads(NEO_SITES_PATH.read_text(encoding="utf-8"))
    if not isinstance(neo_cfg, dict) or not neo_cfg.get("version"):
        raise ValueError("neo.sites.json 必须包含顶层 version 字段")

    for section in ("supplements", "overrides", "rss_link_conf", "apikey_rss_templates", "adapters"):
        val = neo_cfg.get(section)
        if val is not None and not isinstance(val, dict):
            raise ValueError(f"neo.sites.json 字段 {section} 必须为对象")

    files_manifest: dict[str, dict[str, str]] = {}
    tracked_paths = [NEO_SITES_PATH]
    if ADAPTERS_DIR.is_dir():
        tracked_paths.extend(sorted(p for p in ADAPTERS_DIR.rglob("*.py") if p.is_file()))

    # 校验 adapters 中引用的模块均存在
    for adapter_name, spec in (neo_cfg.get("adapters") or {}).items():
        if not isinstance(spec, dict):
            raise ValueError(f"adapter {adapter_name} 定义必须为对象")
        for key in ("spider_module", "parser_module", "test_module"):
            rel_mod = spec.get(key)
            if rel_mod:
                mod_path = REPO_ROOT / "resources.v2" / rel_mod
                if not mod_path.is_file():
                    raise FileNotFoundError(f"adapter {adapter_name}.{key} 指向不存在的文件: {rel_mod}")

    for file_path in tracked_paths:
        if file_path.suffix == ".py":
            source = file_path.read_text(encoding="utf-8")
            ast.parse(source, filename=str(file_path))
        repo_rel = file_path.relative_to(REPO_ROOT).as_posix()
        target_rel = file_path.relative_to(REPO_ROOT / "resources.v2").as_posix()
        files_manifest[repo_rel] = {
            "target": target_rel,
            "sha256": compute_sha256(file_path),
        }

    return neo_cfg, files_manifest


def main() -> int:
    """命令行入口：支持更新清单或仅执行 CI 一致性校验。"""
    parser = argparse.ArgumentParser(description="更新或校验 NEO 站点资源包清单")
    parser.add_argument(
        "--bump",
        choices=("patch", "minor", "major"),
        help="自动递增 neo.sites.json 与 package.v2.json 中的 neo_sites 版本号",
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="只读校验 JSON/Python 语法与 package.v2.json 中的 SHA-256 摘要是否一致",
    )
    args = parser.parse_args()

    pkg = json.loads(PACKAGE_V2_PATH.read_text(encoding="utf-8"))

    if args.bump and not args.verify:
        neo_cfg = json.loads(NEO_SITES_PATH.read_text(encoding="utf-8"))
        neo_cfg["version"] = bump_semver(str(neo_cfg.get("version") or "1.0.0"), args.bump)
        NEO_SITES_PATH.write_text(
            json.dumps(neo_cfg, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    neo_cfg, files_manifest = collect_and_validate_files()
    expected_neo_block = {
        "version": str(neo_cfg["version"]),
        "files": files_manifest,
    }

    if args.verify:
        current_block = pkg.get("neo_sites")
        if current_block != expected_neo_block:
            print("ERROR: package.v2.json 中的 neo_sites 清单或 SHA-256 与实际文件不一致！", file=sys.stderr)
            print("请运行: python3 scripts/update_manifest.py", file=sys.stderr)
            return 1
        print(
            f"OK: neo_sites v{expected_neo_block['version']} 校验通过，"
            f"共 {len(files_manifest)} 个受保护文件。"
        )
        return 0

    pkg["neo_sites"] = expected_neo_block
    PACKAGE_V2_PATH.write_text(
        json.dumps(pkg, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        f"Updated package.v2.json -> neo_sites v{expected_neo_block['version']} "
        f"({len(files_manifest)} files)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
