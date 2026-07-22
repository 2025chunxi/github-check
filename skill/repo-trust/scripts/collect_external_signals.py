#!/usr/bin/env python3
"""Collect external adoption signals for a GitHub credibility check.

Examples:
    python scripts/collect_external_signals.py owner/repo --npm package-name
    python scripts/collect_external_signals.py owner/repo --pypi package-name
    python scripts/collect_external_signals.py owner/repo --crate crate-name

Set GITHUB_TOKEN to raise GitHub API limits for stargazer sampling.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request


def request_json(url: str, headers: dict[str, str] | None = None):
    request = urllib.request.Request(url)
    request.add_header("User-Agent", "repo-trust-skill")
    for key, value in (headers or {}).items():
        request.add_header(key, value)

    last_error: Exception | None = None
    for attempt in range(3):
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                return json.loads(response.read().decode("utf-8")), dict(response.headers)
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            if exc.code in {403, 429} and "rate limit" in detail.lower():
                raise RuntimeError(f"rate limited: {detail}") from exc
            raise RuntimeError(f"HTTP {exc.code}: {detail}") from exc
        except (urllib.error.URLError, TimeoutError) as exc:
            last_error = exc
            if attempt < 2:
                time.sleep(1 + attempt)
                continue
    raise RuntimeError(str(last_error))


def parse_last_page(link_header: str | None) -> int | None:
    if not link_header:
        return None
    for part in link_header.split(","):
        if 'rel="last"' not in part:
            continue
        match = re.search(r"[?&]page=(\d+)", part)
        if match:
            return int(match.group(1))
    return None


def github_star_sample(repo: str):
    token = os.environ.get("GITHUB_TOKEN")
    headers = {"Accept": "application/vnd.github.star+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    base = f"https://api.github.com/repos/{repo}/stargazers?per_page=100"
    try:
        first_page, first_headers = request_json(base + "&page=1", headers)
        last_page_num = parse_last_page(first_headers.get("Link"))
        sample_pages = [1]
        if last_page_num and last_page_num > 1:
            middle = max(1, round(last_page_num / 2))
            sample_pages.extend(page for page in [middle, last_page_num] if page not in sample_pages)

        samples = []
        for page in sample_pages:
            data, _ = request_json(base + f"&page={page}", headers)
            starred_at_values = [
                item.get("starred_at")
                for item in data
                if isinstance(item, dict) and item.get("starred_at")
            ]
            if starred_at_values:
                samples.append(
                    {
                        "page": page,
                        "first_starred_at": starred_at_values[0],
                        "last_starred_at": starred_at_values[-1],
                        "count": len(starred_at_values),
                    }
                )

        return {
            "status": "ok",
            "sampled_pages": sample_pages,
            "estimated_total_pages": last_page_num,
            "samples": samples,
            "note": "GitHub returns stargazers chronologically for the star+json media type; use this as a trajectory sample, not a full star-history replacement.",
        }
    except Exception as exc:  # noqa: BLE001
        return {"status": "blocked", "reason": str(exc), "hint": "Set GITHUB_TOKEN or use browser/star-history fallback."}


def npm_signals(package: str):
    encoded = urllib.parse.quote(package, safe="@")
    try:
        metadata, _ = request_json(f"https://registry.npmjs.org/{encoded}")
        downloads, _ = request_json(f"https://api.npmjs.org/downloads/point/last-month/{encoded}")
        versions = metadata.get("versions") or {}
        latest = (metadata.get("dist-tags") or {}).get("latest")
        return {
            "status": "ok",
            "package": metadata.get("name") or package,
            "latest_version": latest,
            "versions_count": len(versions),
            "created": (metadata.get("time") or {}).get("created"),
            "modified": (metadata.get("time") or {}).get("modified"),
            "downloads_last_month": downloads.get("downloads"),
            "registry_url": f"https://www.npmjs.com/package/{encoded}",
        }
    except Exception as exc:  # noqa: BLE001
        return {"status": "blocked", "package": package, "reason": str(exc)}


def pypi_signals(package: str):
    encoded = urllib.parse.quote(package, safe="")
    try:
        metadata, _ = request_json(f"https://pypi.org/pypi/{encoded}/json")
        info = metadata.get("info") or {}
        releases = metadata.get("releases") or {}
        release_times = []
        for files in releases.values():
            for file_info in files:
                uploaded = file_info.get("upload_time_iso_8601") or file_info.get("upload_time")
                if uploaded:
                    release_times.append(uploaded)
        return {
            "status": "ok",
            "package": info.get("name") or package,
            "latest_version": info.get("version"),
            "versions_count": len(releases),
            "first_upload": min(release_times) if release_times else "not found",
            "latest_upload": max(release_times) if release_times else "not found",
            "project_url": info.get("project_url"),
            "downloads": "not available from PyPI JSON",
        }
    except Exception as exc:  # noqa: BLE001
        return {"status": "blocked", "package": package, "reason": str(exc)}


def crate_signals(crate: str):
    encoded = urllib.parse.quote(crate, safe="")
    try:
        metadata, _ = request_json(f"https://crates.io/api/v1/crates/{encoded}")
        crate_data = metadata.get("crate") or {}
        versions = metadata.get("versions") or []
        return {
            "status": "ok",
            "crate": crate_data.get("name") or crate,
            "latest_version": crate_data.get("max_version"),
            "versions_count": len(versions),
            "downloads_total": crate_data.get("downloads"),
            "downloads_recent": crate_data.get("recent_downloads"),
            "created_at": crate_data.get("created_at"),
            "updated_at": crate_data.get("updated_at"),
            "homepage": crate_data.get("homepage"),
            "repository": crate_data.get("repository"),
        }
    except Exception as exc:  # noqa: BLE001
        return {"status": "blocked", "crate": crate, "reason": str(exc)}


def main() -> int:
    parser = argparse.ArgumentParser(description="Collect external credibility signals.")
    parser.add_argument("repo", help="GitHub owner/repo slug")
    parser.add_argument("--npm", action="append", default=[], help="npm package name")
    parser.add_argument("--pypi", action="append", default=[], help="PyPI package name")
    parser.add_argument("--crate", action="append", default=[], help="crates.io crate name")
    args = parser.parse_args()

    if "/" not in args.repo:
        print("repo must be an owner/repo slug", file=sys.stderr)
        return 2

    result = {
        "repo": args.repo,
        "github_star_sample": github_star_sample(args.repo),
        "npm": [npm_signals(package) for package in args.npm],
        "pypi": [pypi_signals(package) for package in args.pypi],
        "crates": [crate_signals(crate) for crate in args.crate],
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
