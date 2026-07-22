#!/usr/bin/env python3
"""Collect reproducible GitHub repository metrics for credibility checks."""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from datetime import datetime, timezone

try:
    import tomllib
except ImportError:  # pragma: no cover
    tomllib = None


API_ROOT = "https://api.github.com"
LINK_PAGE_RE = re.compile(r"[?&]page=(\d+)")


class GitHubClient:
    def __init__(self):
        self.token = os.environ.get("GITHUB_TOKEN")
        self.requests = 0

    def get(self, path: str, accept: str = "application/vnd.github+json"):
        request = urllib.request.Request(API_ROOT + path)
        request.add_header("Accept", accept)
        request.add_header("User-Agent", "github-check-skill")
        request.add_header("X-GitHub-Api-Version", "2022-11-28")
        if self.token:
            request.add_header("Authorization", f"Bearer {self.token}")

        last_error: Exception | None = None
        for attempt in range(3):
            try:
                self.requests += 1
                with urllib.request.urlopen(request, timeout=25) as response:
                    return json.loads(response.read().decode("utf-8")), dict(response.headers)
            except urllib.error.HTTPError as exc:
                detail = exc.read().decode("utf-8", errors="replace")
                if exc.code in {403, 429} and "rate limit" in detail.lower():
                    raise RuntimeError("GitHub API rate limit exceeded; set GITHUB_TOKEN and retry") from exc
                raise RuntimeError(f"GitHub API {exc.code} for {path}: {detail}") from exc
            except (urllib.error.URLError, TimeoutError) as exc:
                last_error = exc
                if attempt < 2:
                    time.sleep(1 + attempt)
                    continue
        raise RuntimeError(f"GitHub API request failed for {path}: {last_error}")


def parse_link_pages(link_header: str | None) -> dict[str, int]:
    result = {}
    if not link_header:
        return result
    for part in link_header.split(","):
        rel_match = re.search(r'rel="([^"]+)"', part)
        page_match = LINK_PAGE_RE.search(part)
        if rel_match and page_match:
            result[rel_match.group(1)] = int(page_match.group(1))
    return result


def paginated_count(client: GitHubClient, path: str) -> dict:
    separator = "&" if "?" in path else "?"
    first, headers = client.get(f"{path}{separator}per_page=100&page=1")
    if not isinstance(first, list):
        return {"value": "not found", "exact": False}
    pages = parse_link_pages(headers.get("Link"))
    last_page = pages.get("last")
    if not last_page:
        return {"value": len(first), "exact": True}
    last, _ = client.get(f"{path}{separator}per_page=100&page={last_page}")
    value = (last_page - 1) * 100 + (len(last) if isinstance(last, list) else 0)
    return {"value": value, "exact": isinstance(last, list)}


def search_count(client: GitHubClient, query: str) -> int | str:
    encoded = urllib.parse.quote(query, safe=":/")
    try:
        data, _ = client.get(f"/search/issues?q={encoded}&per_page=1")
        return data.get("total_count", "not found") if isinstance(data, dict) else "not found"
    except RuntimeError as exc:
        return f"blocked: {exc}"


def decode_content(client: GitHubClient, slug: str, path: str, ref: str) -> str | None:
    encoded_path = "/".join(urllib.parse.quote(part, safe="") for part in path.split("/"))
    try:
        data, _ = client.get(f"/repos/{slug}/contents/{encoded_path}?ref={urllib.parse.quote(ref, safe='')}")
    except RuntimeError:
        return None
    if not isinstance(data, dict) or data.get("encoding") != "base64":
        return None
    try:
        return base64.b64decode(data.get("content", "")).decode("utf-8", errors="ignore")
    except (ValueError, TypeError):
        return None


def detect_packages(client: GitHubClient, slug: str, branch: str, tree_paths: set[str]) -> list[dict]:
    packages = []
    if "package.json" in tree_paths:
        raw = decode_content(client, slug, "package.json", branch)
        try:
            data = json.loads(raw or "{}")
            if data.get("name"):
                packages.append({"registry": "npm", "name": data["name"], "source": "package.json"})
        except json.JSONDecodeError:
            pass
    if "pyproject.toml" in tree_paths and tomllib is not None:
        raw = decode_content(client, slug, "pyproject.toml", branch)
        try:
            data = tomllib.loads(raw or "")
            project = data.get("project") or {}
            poetry = ((data.get("tool") or {}).get("poetry") or {})
            name = project.get("name") or poetry.get("name")
            if name:
                packages.append({"registry": "pypi", "name": name, "source": "pyproject.toml"})
        except (ValueError, tomllib.TOMLDecodeError):
            pass
    if "Cargo.toml" in tree_paths and tomllib is not None:
        raw = decode_content(client, slug, "Cargo.toml", branch)
        try:
            data = tomllib.loads(raw or "")
            name = (data.get("package") or {}).get("name")
            if name:
                packages.append({"registry": "crates", "name": name, "source": "Cargo.toml"})
        except (ValueError, tomllib.TOMLDecodeError):
            pass
    return packages


def repository_type_hint(name: str, description: str | None, extension_counts: Counter, language_bytes: dict) -> str:
    text = f"{name} {description or ''}".lower()
    total_files = sum(extension_counts.values()) or 1
    markdown_ratio = extension_counts.get(".md", 0) / total_files
    if any(term in text for term in ("awesome list", "curated list", "collective list", "list of free", "collection of")):
        return "curated-list"
    if markdown_ratio >= 0.6 and sum(language_bytes.values()) < 100_000:
        return "documentation"
    if any(term in text for term in ("dataset", "data set", "model weights")):
        return "data-or-model"
    return "code"


def collect_repository(repo: str) -> dict:
    if repo.count("/") != 1:
        raise ValueError("repo must be an owner/repo slug")
    owner, name = repo.split("/", 1)
    slug = f"{urllib.parse.quote(owner, safe='')}/{urllib.parse.quote(name, safe='')}"
    client = GitHubClient()

    repo_data, repo_headers = client.get(f"/repos/{slug}")
    branch = repo_data.get("default_branch") or "main"

    commits_10, _ = client.get(f"/repos/{slug}/commits?sha={urllib.parse.quote(branch, safe='')}&per_page=10")
    commit_count = paginated_count(client, f"/repos/{slug}/commits?sha={urllib.parse.quote(branch, safe='')}")
    contributor_count = paginated_count(client, f"/repos/{slug}/contributors?anon=1")
    release_count = paginated_count(client, f"/repos/{slug}/releases")
    tag_count = paginated_count(client, f"/repos/{slug}/tags")

    contributors, _ = client.get(f"/repos/{slug}/contributors?anon=1&per_page=10")
    releases, _ = client.get(f"/repos/{slug}/releases?per_page=5")
    languages, _ = client.get(f"/repos/{slug}/languages")

    tree_paths: set[str] = set()
    tree_entries = []
    tree_truncated = False
    try:
        tree, _ = client.get(f"/repos/{slug}/git/trees/{urllib.parse.quote(branch, safe='')}?recursive=1")
        tree_truncated = bool(tree.get("truncated"))
        tree_entries = tree.get("tree") or []
        tree_paths = {entry.get("path", "") for entry in tree_entries if entry.get("path")}
    except RuntimeError:
        pass

    lower_paths = {path.lower() for path in tree_paths}
    test_markers = ("/test/", "/tests/", "/__tests__/", ".spec.", ".test.", "test_")
    has_tests = any(marker in f"/{path}" for path in lower_paths for marker in test_markers)
    ci_paths = sorted(path for path in tree_paths if path.startswith(".github/workflows/") and path.endswith((".yml", ".yaml")))
    security_policy = next((path for path in tree_paths if path.lower() in {"security.md", ".github/security.md", "docs/security.md"}), None)
    code_of_conduct = next((path for path in tree_paths if "code_of_conduct" in path.lower()), None)
    packages = detect_packages(client, slug, branch, tree_paths)

    blob_entries = [entry for entry in tree_entries if entry.get("type") == "blob"]
    extension_counts = Counter(
        ("." + entry.get("path", "").rsplit(".", 1)[-1].lower())
        if "." in entry.get("path", "").rsplit("/", 1)[-1] else "[no-extension]"
        for entry in blob_entries
    )
    type_hint = repository_type_hint(name, repo_data.get("description"), extension_counts, languages if isinstance(languages, dict) else {})
    largest_files = sorted(
        ({"path": entry.get("path"), "size": entry.get("size", 0)} for entry in blob_entries),
        key=lambda item: item["size"],
        reverse=True,
    )[:10]

    stars = repo_data.get("stargazers_count") or 0
    forks = repo_data.get("forks_count") or 0
    top_contributors = []
    if isinstance(contributors, list):
        top_contributors = [
            {"login": item.get("login") or item.get("name") or "anonymous", "contributions": item.get("contributions", 0)}
            for item in contributors
        ]
    contribution_total = sum(item["contributions"] for item in top_contributors)
    top_share = (
        round(top_contributors[0]["contributions"] / contribution_total, 3)
        if top_contributors and contribution_total else "not found"
    )
    issues_enabled = bool(repo_data.get("has_issues"))
    open_issues = search_count(client, f"repo:{repo} type:issue state:open") if issues_enabled else "disabled"
    closed_issues = search_count(client, f"repo:{repo} type:issue state:closed") if issues_enabled else "disabled"

    rate_remaining = repo_headers.get("X-RateLimit-Remaining")
    return {
        "collected_at": datetime.now(timezone.utc).isoformat(),
        "repo": repo,
        "source": repo_data.get("html_url"),
        "api_requests": client.requests,
        "rate_limit_remaining_after_repo_request": int(rate_remaining) if str(rate_remaining).isdigit() else rate_remaining,
        "repository": {
            "description": repo_data.get("description"),
            "homepage": repo_data.get("homepage"),
            "created_at": repo_data.get("created_at"),
            "updated_at": repo_data.get("updated_at"),
            "pushed_at": repo_data.get("pushed_at"),
            "default_branch": branch,
            "archived": repo_data.get("archived"),
            "fork": repo_data.get("fork"),
            "size_kb": repo_data.get("size"),
            "visibility": repo_data.get("visibility"),
            "license": (repo_data.get("license") or {}).get("spdx_id"),
            "has_issues": issues_enabled,
            "has_discussions": repo_data.get("has_discussions"),
            "type_hint": type_hint,
        },
        "social": {
            "stars": stars,
            "forks": forks,
            "watchers": repo_data.get("subscribers_count"),
            "star_fork_ratio": round(stars / forks, 2) if forks else "undefined",
            "contributors": contributor_count,
            "top_contributors_sample": top_contributors,
            "top_contributor_share_of_top_10": top_share,
        },
        "activity": {
            "commits_default_branch": commit_count,
            "releases": release_count,
            "tags": tag_count,
            "latest_releases": [
                {"tag": item.get("tag_name"), "published_at": item.get("published_at"), "prerelease": item.get("prerelease")}
                for item in releases if isinstance(item, dict)
            ] if isinstance(releases, list) else [],
            "last_10_commits": [
                {
                    "sha": item.get("sha", "")[:7],
                    "date": ((item.get("commit") or {}).get("committer") or {}).get("date"),
                    "message": ((item.get("commit") or {}).get("message") or "").splitlines()[0],
                }
                for item in commits_10 if isinstance(item, dict)
            ] if isinstance(commits_10, list) else [],
        },
        "issues_and_prs": {
            "open_issues": open_issues,
            "closed_issues": closed_issues,
            "open_pull_requests": search_count(client, f"repo:{repo} type:pr state:open"),
            "closed_pull_requests": search_count(client, f"repo:{repo} type:pr state:closed"),
            "github_open_issues_count_raw_includes_prs": repo_data.get("open_issues_count"),
            "count_note": (
                "GitHub Issues are disabled; issue search counts are not applicable. "
                "The raw open_issues_count field can include pull requests and may not reconcile with search totals."
                if not issues_enabled
                else "The raw open_issues_count field includes pull requests and can lag behind search totals."
            ),
        },
        "code": {
            "languages_bytes": languages if isinstance(languages, dict) else {},
            "tree_truncated": tree_truncated,
            "file_count": len(blob_entries),
            "extension_counts": dict(extension_counts.most_common(20)),
            "has_tests": has_tests,
            "ci_workflows": ci_paths,
            "security_policy": security_policy,
            "code_of_conduct": code_of_conduct,
            "largest_files": largest_files,
        },
        "package_candidates": packages,
        "limitations": [
            "Contributor concentration uses only the top 10 contributors, not the full history.",
            "Recursive Git trees can be truncated for very large repositories.",
            "Search counts and private repository data depend on GitHub API permissions.",
            "GitHub search totals and repository open_issues_count can update on different schedules.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Collect GitHub repository evidence.")
    parser.add_argument("repo", help="Repository slug, for example owner/repo")
    parser.add_argument("--output", help="Optional JSON output path")
    args = parser.parse_args()
    try:
        result = collect_repository(args.repo)
    except Exception as exc:  # noqa: BLE001
        print(str(exc), file=sys.stderr)
        return 1
    output = json.dumps(result, indent=2, ensure_ascii=False)
    if args.output:
        from pathlib import Path
        Path(args.output).write_text(output + "\n", encoding="utf-8")
        print(f"{result['repo']}: evidence written to {Path(args.output).resolve()}")
    else:
        print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
