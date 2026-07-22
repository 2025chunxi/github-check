#!/usr/bin/env python3
"""Build a unified evidence packet for GitHub credibility and adoption review."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from collect_external_signals import crate_signals, github_star_sample, npm_signals, pypi_signals  # noqa: E402
from collect_github_repo import collect_repository  # noqa: E402


def parse_time(value: str | None):
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def days_since(value: str | None) -> int | None:
    parsed = parse_time(value)
    if not parsed:
        return None
    return max(0, (datetime.now(timezone.utc) - parsed).days)


def adoption_risk(evidence: dict) -> dict:
    repo = evidence.get("repository") or {}
    code = evidence.get("code") or {}
    activity = evidence.get("activity") or {}
    social = evidence.get("social") or {}
    repo_type = repo.get("type_hint") or "code"
    points = 0
    factors = []

    def add(value: int, factor: str):
        nonlocal points
        points += value
        factors.append({"points": value, "factor": factor})

    if repo.get("archived"):
        add(35, "Repository is archived")
    stale_days = days_since(repo.get("pushed_at"))
    if stale_days is not None and stale_days > 730:
        add(25, f"No push for {stale_days} days")
    elif stale_days is not None and stale_days > 365:
        add(15, f"No push for {stale_days} days")
    if not repo.get("license") or repo.get("license") == "NOASSERTION":
        add(20, "No machine-detectable license")
    if repo_type == "code" and not code.get("has_tests"):
        add(10, "No test files detected")
    if repo_type == "code" and not code.get("ci_workflows"):
        add(8, "No GitHub Actions workflow detected")
    if repo_type == "code" and not code.get("security_policy"):
        add(5, "No SECURITY.md policy detected")
    releases = (activity.get("releases") or {}).get("value")
    if releases == 0:
        add(7, "No GitHub releases")
    top_share = social.get("top_contributor_share_of_top_10")
    if isinstance(top_share, (int, float)) and top_share >= 0.8:
        add(10, "Top contributor owns at least 80% of top-10 contributions")
    if code.get("tree_truncated"):
        factors.append({"points": 0, "factor": "Tree was truncated; code checks have lower confidence"})

    score = min(100, points)
    level = "low" if score < 25 else "medium" if score < 50 else "high"
    return {
        "score": score,
        "level": level,
        "factors": sorted(factors, key=lambda item: item["points"], reverse=True),
        "scope": "Operational adoption risk, separate from credibility or star-integrity scoring.",
    }


def automated_precheck(evidence: dict, registries: dict) -> dict:
    repo = evidence.get("repository") or {}
    code = evidence.get("code") or {}
    social = evidence.get("social") or {}
    activity = evidence.get("activity") or {}
    repo_type = repo.get("type_hint") or "code"
    concerns = []
    positives = []

    ratio = social.get("star_fork_ratio")
    if isinstance(ratio, (int, float)) and ratio > 20:
        concerns.append("Star:fork ratio exceeds 20:1; investigate launch context and star trajectory")
    if repo.get("archived"):
        concerns.append("Repository is archived")
    if repo_type == "code" and not code.get("has_tests"):
        concerns.append("No tests detected in recursive tree")
    if (activity.get("commits_default_branch") or {}).get("value", 0) == 1:
        concerns.append("Default branch appears to contain only one commit")

    if code.get("has_tests"):
        positives.append("Tests detected")
    if code.get("ci_workflows"):
        positives.append("CI workflows detected")
    if repo.get("license") and repo.get("license") != "NOASSERTION":
        positives.append(f"License detected: {repo['license']}")
    if repo_type != "code":
        positives.append(f"Type-adjusted checks applied: {repo_type}")
    if any(item.get("status") == "ok" for values in registries.values() for item in values):
        positives.append("At least one package registry record verified")

    return {
        "concerns": concerns,
        "positive_signals": positives,
        "verdict": "manual scoring required",
        "reason": "Website claims, independent mentions, star-farming evidence, and launch context are not fully machine-verifiable.",
    }


def unique_packages(candidates: list[dict], explicit: dict[str, list[str]]) -> dict[str, list[str]]:
    result = {"npm": [], "pypi": [], "crates": []}
    for item in candidates:
        registry = item.get("registry")
        name = item.get("name")
        if registry in result and name and name not in result[registry]:
            result[registry].append(name)
    for registry, names in explicit.items():
        for name in names:
            if name not in result[registry]:
                result[registry].append(name)
    return result


def build_audit(repo: str, mode: str, npm: list[str], pypi: list[str], crates: list[str]) -> dict:
    core = collect_repository(repo)
    package_names = unique_packages(
        core.get("package_candidates") or [],
        {"npm": npm, "pypi": pypi, "crates": crates},
    )
    registries = {"npm": [], "pypi": [], "crates": []}
    star_sample = {"status": "not-collected", "reason": f"mode={mode}"}

    if mode in {"standard", "deep"}:
        registries["npm"] = [npm_signals(name) for name in package_names["npm"]]
        registries["pypi"] = [pypi_signals(name) for name in package_names["pypi"]]
        registries["crates"] = [crate_signals(name) for name in package_names["crates"]]
    if mode == "deep":
        star_sample = github_star_sample(repo)

    return {
        "schema_version": 1,
        "mode": mode,
        "evidence": core,
        "registry_signals": registries,
        "github_star_sample": star_sample,
        "automated_precheck": automated_precheck(core, registries),
        "adoption_risk": adoption_risk(core),
        "manual_collection_required": [
            "Official website and README quantitative claims",
            "Independent tutorials, discussions, and real user reports",
            "Star giveaways, paid-star campaigns, or viral launch context",
            "Live demo and documentation link health",
            "Security advisories and dependency vulnerabilities when access permits",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a GitHub credibility evidence packet.")
    parser.add_argument("repo", help="Repository slug, for example owner/repo")
    parser.add_argument("--mode", choices=("quick", "standard", "deep"), default="standard")
    parser.add_argument("--npm", action="append", default=[])
    parser.add_argument("--pypi", action="append", default=[])
    parser.add_argument("--crate", action="append", default=[])
    parser.add_argument("--output", help="Optional JSON output path")
    args = parser.parse_args()

    try:
        result = build_audit(args.repo, args.mode, args.npm, args.pypi, args.crate)
    except Exception as exc:  # noqa: BLE001
        print(f"Audit failed: {exc}", file=sys.stderr)
        return 1
    output = json.dumps(result, indent=2, ensure_ascii=False)
    if args.output:
        Path(args.output).write_text(output + "\n", encoding="utf-8")
        risk = result.get("adoption_risk") or {}
        print(
            f"{args.repo}: audit written to {Path(args.output).resolve()} "
            f"(adoption risk {risk.get('level')} {risk.get('score')}/100)"
        )
    else:
        print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
