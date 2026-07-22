#!/usr/bin/env python3
"""Validate calibration labels and direct-evidence requirements."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


PINNED_GITHUB_BLOB_RE = re.compile(r"^https://github\.com/[^/]+/[^/]+/blob/[0-9a-f]{40}/")


def main() -> int:
    skill_dir = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(description="Validate credibility calibration cases.")
    parser.add_argument(
        "cases",
        nargs="?",
        default=str(skill_dir / "references" / "calibration-repos.json"),
    )
    args = parser.parse_args()

    try:
        payload = json.loads(Path(args.cases).read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        print(f"Calibration validation failed: {exc}", file=sys.stderr)
        return 1
    cases = payload.get("cases") or []
    errors = []
    repos = set()

    for index, case in enumerate(cases, 1):
        repo = case.get("repo")
        prefix = f"case {index} ({repo or 'missing repo'})"
        if not repo or "/" not in repo:
            errors.append(f"{prefix}: invalid repo")
            continue
        if repo.lower() in repos:
            errors.append(f"{prefix}: duplicate repo")
        repos.add(repo.lower())

        expected = str(case.get("expected_band") or "")
        evidence = case.get("direct_evidence") or {}
        constraints = case.get("expected_signal_constraints") or {}
        if expected in {"suspicious", "unreliable", "manipulated"}:
            if not evidence.get("type") or not evidence.get("quote") or not evidence.get("source"):
                errors.append(f"{prefix}: suspicious label requires type, quote, and source")
            elif not PINNED_GITHUB_BLOB_RE.match(str(evidence.get("source"))):
                errors.append(f"{prefix}: evidence source must be a commit-pinned GitHub blob URL")
            if constraints.get("A") != 1:
                errors.append(f"{prefix}: direct reward/manipulation case must explicitly constrain Signal A")
            if not case.get("alternative_explanation"):
                errors.append(f"{prefix}: record the strongest alternative explanation")

        if "negative-control" in str(case.get("repo_type") or ""):
            if constraints.get("A_not") != 1:
                errors.append(f"{prefix}: incentive negative control must specify A_not=1")
            if not evidence.get("verification"):
                errors.append(f"{prefix}: negative control must explain the actual reward condition")

    if errors:
        print("Calibration validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print(f"Calibration set is valid: {len(cases)} cases")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
