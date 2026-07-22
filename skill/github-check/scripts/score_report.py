#!/usr/bin/env python3
"""Validate a manual scorecard, calculate WCS, and render a credibility report."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


WEIGHTS = {"A": 20, "B": 25, "C": 20, "D": 15, "E": 10, "F": 10}
SIGNAL_NAMES = {
    "A": "Star integrity",
    "B": "Claim verifiability",
    "C": "Code substance",
    "D": "Community substance",
    "E": "Marketing vs substance",
    "F": "Commercial conflicts",
}
REPO_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
PINNED_GITHUB_BLOB_RE = re.compile(
    r"^https://github\.com/[^/]+/[^/]+/blob/[0-9a-fA-F]{40}/.+"
)


def load_json(path: str | Path) -> dict:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Expected a JSON object: {path}")
    return data


def validate_scorecard(scorecard: dict) -> list[str]:
    errors = []
    if scorecard.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    if scorecard.get("template") is not False:
        errors.append("template must be false after replacing all example content")
    repo = scorecard.get("repo")
    if not isinstance(repo, str) or not REPO_RE.fullmatch(repo):
        errors.append("repo must be an owner/repo slug")
    if scorecard.get("confidence") not in {"high", "medium", "low"}:
        errors.append("confidence must be high, medium, or low")
    confidence_reason = scorecard.get("confidence_reason")
    if not isinstance(confidence_reason, str) or not confidence_reason.strip():
        errors.append("confidence_reason is required")
    signals = scorecard.get("signals")
    if not isinstance(signals, dict):
        return errors + ["signals must be an object containing A-F"]
    unexpected = sorted(set(signals) - set(WEIGHTS))
    if unexpected:
        errors.append("unexpected signal keys: " + ", ".join(unexpected))

    for key in WEIGHTS:
        signal = signals.get(key)
        if not isinstance(signal, dict):
            errors.append(f"signal {key} is missing")
            continue
        score = signal.get("score")
        if not isinstance(score, int) or isinstance(score, bool) or not 1 <= score <= 5:
            errors.append(f"signal {key}.score must be an integer from 1 to 5")
        summary = signal.get("summary")
        if not isinstance(summary, str) or not summary.strip():
            errors.append(f"signal {key}.summary is required")
        evidence = signal.get("evidence")
        if not isinstance(evidence, list) or not evidence:
            errors.append(f"signal {key} requires at least one evidence item")
            continue
        for index, item in enumerate(evidence, 1):
            if not isinstance(item, dict):
                errors.append(f"signal {key} evidence {index} must be an object")
                continue
            if not str(item.get("fact") or "").strip():
                errors.append(f"signal {key} evidence {index} requires fact")
            if not str(item.get("source") or "").strip():
                errors.append(f"signal {key} evidence {index} requires source")
            if "direct" in item and not isinstance(item.get("direct"), bool):
                errors.append(f"signal {key} evidence {index}.direct must be boolean")
            if "quote" in item and not isinstance(item.get("quote"), str):
                errors.append(f"signal {key} evidence {index}.quote must be a string")

        if score == 1 and key in {"A", "B"}:
            direct = [
                item for item in evidence
                if isinstance(item, dict)
                and item.get("direct") is True
                and str(item.get("source") or "").startswith(("https://", "http://"))
                and len(str(item.get("quote") or "").strip()) >= 12
                and (
                    not str(item.get("source") or "").startswith("https://github.com/")
                    or PINNED_GITHUB_BLOB_RE.match(str(item.get("source") or ""))
                )
            ]
            if not direct:
                errors.append(
                    f"signal {key}=1 requires direct=true evidence with a source URL and exact quote; "
                    "GitHub blob URLs must contain a 40-character commit SHA"
                )
    return errors


def validate_audit(audit: dict, repo: str) -> list[str]:
    errors = []
    if audit.get("schema_version") != 1:
        errors.append("audit schema_version must be 1")
    audit_repo = ((audit.get("evidence") or {}).get("repo"))
    if audit_repo != repo:
        errors.append(f"audit repo must match scorecard repo '{repo}'")
    risk = audit.get("adoption_risk")
    if not isinstance(risk, dict):
        return errors + ["audit adoption_risk must be an object"]
    score = risk.get("score")
    level = risk.get("level")
    if not isinstance(score, int) or isinstance(score, bool) or not 0 <= score <= 100:
        errors.append("audit adoption_risk.score must be an integer from 0 to 100")
    elif level != ("low" if score < 25 else "medium" if score < 50 else "high"):
        errors.append("audit adoption_risk.level does not match its score")
    if level not in {"low", "medium", "high"}:
        errors.append("audit adoption_risk.level must be low, medium, or high")
    factors = risk.get("factors")
    if not isinstance(factors, list):
        errors.append("audit adoption_risk.factors must be an array")
    else:
        for index, factor in enumerate(factors, 1):
            if not isinstance(factor, dict):
                errors.append(f"audit adoption_risk factor {index} must be an object")
                continue
            points = factor.get("points")
            if not isinstance(points, int) or isinstance(points, bool) or points < 0:
                errors.append(f"audit adoption_risk factor {index}.points must be a non-negative integer")
            if not str(factor.get("factor") or "").strip():
                errors.append(f"audit adoption_risk factor {index}.factor is required")
    return errors


def verdict_for_score(score: int) -> str:
    if score >= 75:
        return "credible"
    if score >= 55:
        return "mixed"
    if score >= 35:
        return "suspicious"
    return "unreliable"


def calculate(scorecard: dict, audit: dict | None = None) -> dict:
    errors = validate_scorecard(scorecard)
    if audit is not None and not errors:
        errors.extend(validate_audit(audit, scorecard["repo"]))
    if errors:
        raise ValueError("Invalid scorecard:\n- " + "\n- ".join(errors))
    signals = scorecard["signals"]
    contributions = {
        key: int(WEIGHTS[key] * signals[key]["score"] / 5)
        for key in WEIGHTS
    }
    raw_score = sum(contributions.values())
    final_score = raw_score
    raw_verdict = verdict_for_score(raw_score)
    override = None
    forced_verdict = None

    if signals["A"]["score"] == 1 and signals["C"]["score"] <= 2:
        override = "A=1 and C<=2"
        forced_verdict = "unreliable"
        final_score = min(final_score, 34)
    elif signals["A"]["score"] == 1 or signals["B"]["score"] == 1:
        override = "A=1 or B=1"
        forced_verdict = "suspicious"
        final_score = min(final_score, 54)
    elif signals["A"]["score"] <= 2 and signals["B"]["score"] <= 2 and signals["F"]["score"] <= 2:
        override = "A<=2, B<=2, and F<=2"
        forced_verdict = "suspicious"
        final_score = min(final_score, 54)

    return {
        "schema_version": 1,
        "repo": scorecard["repo"],
        "calculated_at": datetime.now(timezone.utc).isoformat(),
        "confidence": scorecard["confidence"],
        "confidence_reason": scorecard["confidence_reason"],
        "raw_score": raw_score,
        "final_score": final_score,
        "verdict_before_override": raw_verdict,
        "verdict": forced_verdict or verdict_for_score(final_score),
        "override": override,
        "contributions": contributions,
        "signals": signals,
        "adoption_risk": (
            {
                **audit["adoption_risk"],
                "status": "assessed",
                "source_collected_at": (audit.get("evidence") or {}).get("collected_at"),
            }
            if audit is not None
            else {"status": "not-assessed", "score": None, "level": None, "factors": []}
        ),
        "reviewer_notes": scorecard.get("reviewer_notes"),
    }


def source_markdown(source: str) -> str:
    if source.startswith(("https://", "http://")):
        safe_source = source.replace("(", "%28").replace(")", "%29")
        return f"[source]({safe_source})"
    safe_source = source.replace("`", "'")
    return f"`{safe_source}`"


def render_markdown(result: dict) -> str:
    adoption = result.get("adoption_risk") or {}
    lines = [
        f"# GitHub Credibility Report: {result['repo']}",
        "",
        f"- Credibility verdict: **{result['verdict'].upper()}**",
        f"- Weighted score: **{result['final_score']}/100** (raw: {result['raw_score']})",
        f"- Confidence: **{result['confidence']}**",
        f"- Confidence basis: {str(result['confidence_reason']).replace(chr(10), ' ')}",
        f"- Adoption risk: **{adoption.get('level') or 'not assessed'}**"
        + (f" ({adoption.get('score')}/100)" if adoption.get("score") is not None else ""),
        f"- Evidence scored at: {result['calculated_at']}",
        "",
        "## Signal Scorecard",
        "",
        "| Signal | Score | Contribution | Summary |",
        "|---|---:|---:|---|",
    ]
    for key in WEIGHTS:
        signal = result["signals"][key]
        summary = str(signal["summary"]).replace("|", "\\|").replace("\n", " ")
        lines.append(f"| {key}. {SIGNAL_NAMES[key]} | {signal['score']}/5 | {result['contributions'][key]} | {summary} |")

    lines.extend(["", "## Evidence", ""])
    for key in WEIGHTS:
        lines.append(f"### {key}. {SIGNAL_NAMES[key]}")
        lines.append("")
        for item in result["signals"][key]["evidence"]:
            direct = " Direct evidence." if item.get("direct") else ""
            quote_text = str(item.get("quote") or "").replace("\n", " ").replace('"', "'")
            quote = f" Quote: \"{quote_text}\"" if quote_text else ""
            fact = str(item["fact"]).replace("\n", " ")
            lines.append(f"- {fact} ({source_markdown(str(item['source']))}).{direct}{quote}")
        lines.append("")

    lines.extend(["## Calculation", ""])
    expression = " + ".join(f"{key}:{result['contributions'][key]}" for key in WEIGHTS)
    lines.append(f"`{expression} = {result['raw_score']}`")
    if result.get("override"):
        lines.extend(["", f"Override applied: `{result['override']}`; final score capped at {result['final_score']}. "])

    lines.extend(["", "## Adoption Risks", ""])
    factors = adoption.get("factors") or []
    if factors:
        for factor in factors:
            lines.append(f"- +{factor.get('points', 0)}: {factor.get('factor')}")
    else:
        lines.append("- Not assessed or no automated risk factors recorded.")

    recommendations = {
        "credible": "Reasonable to evaluate for adoption; still test compatibility, security, and license fit.",
        "mixed": "Pilot in a controlled environment and verify the unresolved claims before adoption.",
        "suspicious": "Do not rely on popularity or marketing claims; require direct technical validation before use.",
        "unreliable": "Avoid adoption until the confirmed credibility and code-substance issues are resolved.",
    }
    lines.extend([
        "",
        "## Recommended Action",
        "",
        recommendations[result["verdict"]],
        "",
        "## Evidence Boundary",
        "",
        "This verdict describes the supplied evidence and rubric. Anomalous stars or ratios alone do not prove purchased or automated stars.",
        "",
    ])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Score and render a GitHub credibility report.")
    parser.add_argument("scorecard")
    parser.add_argument("--audit", help="Optional audit_repo.py JSON output")
    parser.add_argument("--json-output")
    parser.add_argument("--markdown-output")
    args = parser.parse_args()

    try:
        scorecard = load_json(args.scorecard)
        audit = load_json(args.audit) if args.audit else None
        result = calculate(scorecard, audit)
    except Exception as exc:  # noqa: BLE001
        print(str(exc), file=sys.stderr)
        return 1

    output = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    if args.json_output:
        Path(args.json_output).write_text(output, encoding="utf-8")
    if args.markdown_output:
        Path(args.markdown_output).write_text(render_markdown(result), encoding="utf-8")
    if not args.json_output and not args.markdown_output:
        print(output, end="")
    else:
        print(f"{result['repo']}: {result['verdict']} {result['final_score']}/100")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
