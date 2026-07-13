#!/usr/bin/env python3
"""Run a resumable automated precheck over the credibility calibration set."""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from audit_repo import build_audit  # noqa: E402


def safe_name(repo: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_.-]+", "__", repo)


def load_json(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return data


def summarize(case: dict, result: dict | None, error: str | None) -> dict:
    case_context = {
        "repo": case.get("repo"),
        "repo_type": case.get("repo_type"),
        "expected_band": case.get("expected_band"),
        "direct_evidence": case.get("direct_evidence"),
        "expected_signal_constraints": case.get("expected_signal_constraints"),
        "alternative_explanation": case.get("alternative_explanation"),
    }
    if error:
        return case_context | {
            "status": "failed",
            "error": error,
        }
    precheck = result.get("automated_precheck") or {}
    adoption = result.get("adoption_risk") or {}
    return case_context | {
        "status": "collected",
        "automated_concerns": precheck.get("concerns") or [],
        "automated_positive_signals": precheck.get("positive_signals") or [],
        "adoption_risk": adoption.get("level"),
        "adoption_risk_score": adoption.get("score"),
        "manual_scoring_required": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the GitHub credibility calibration seed set.")
    parser.add_argument(
        "--cases",
        default=str(SKILL_DIR / "references" / "calibration-repos.json"),
        help="Calibration case JSON",
    )
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--mode", choices=("quick", "standard", "deep"), default="quick")
    parser.add_argument("--limit", type=int, default=0, help="Maximum cases; 0 means all")
    parser.add_argument("--delay", type=float, default=0.0, help="Seconds between cases")
    parser.add_argument("--no-resume", action="store_true", help="Ignore cached successful results")
    args = parser.parse_args()

    try:
        payload = load_json(Path(args.cases).resolve())
    except Exception as exc:  # noqa: BLE001
        print(f"Calibration setup failed: {exc}", file=sys.stderr)
        return 2
    cases = payload.get("cases") or []
    if not isinstance(cases, list) or not cases:
        print("Calibration setup failed: no cases", file=sys.stderr)
        return 2
    if args.limit > 0:
        cases = cases[: args.limit]

    output_dir = Path(args.output_dir).resolve()
    results_dir = output_dir / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    summary = []
    stopped_for_rate_limit = False

    for index, case in enumerate(cases):
        repo = case.get("repo")
        if not repo:
            summary.append(summarize(case, None, "missing repo"))
            continue
        result_path = results_dir / f"{safe_name(repo)}.json"
        result = None
        error = None
        if result_path.exists() and not args.no_resume:
            try:
                result = load_json(result_path)
            except Exception:
                result = None
        if result is None:
            try:
                result = build_audit(repo, args.mode, [], [], [])
                result_path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            except Exception as exc:  # noqa: BLE001
                error = str(exc)
                if "rate limit" in error.lower():
                    stopped_for_rate_limit = True
        summary.append(summarize(case, result, error))
        if stopped_for_rate_limit:
            break
        if args.delay and index < len(cases) - 1:
            time.sleep(args.delay)

    report = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "mode": args.mode,
        "requested_cases": len(cases),
        "completed_cases": sum(item.get("status") == "collected" for item in summary),
        "failed_cases": sum(item.get("status") == "failed" for item in summary),
        "stopped_for_rate_limit": stopped_for_rate_limit,
        "manual_labels_complete": False,
        "results": summary,
    }
    summary_path = output_dir / "calibration-summary.json"
    summary_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(summary_path)
    return 1 if stopped_for_rate_limit else 0


if __name__ == "__main__":
    raise SystemExit(main())
