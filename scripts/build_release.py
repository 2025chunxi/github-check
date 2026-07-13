#!/usr/bin/env python3
"""Run offline checks and build github-credibility-check.skill."""

from __future__ import annotations

import subprocess
import sys
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skill" / "github-credibility-check"
DIST = ROOT / "dist"


def run(*args: str | Path) -> None:
    command = [str(arg) for arg in args]
    print("+", " ".join(command), flush=True)
    subprocess.run(command, cwd=ROOT, check=True)


def verify_archive(path: Path) -> None:
    with zipfile.ZipFile(path) as archive:
        bad_member = archive.testzip()
        if bad_member:
            raise RuntimeError(f"Corrupt archive member: {bad_member}")
        names = {name.rstrip("/") for name in archive.namelist() if name.rstrip("/")}
    roots = {name.split("/", 1)[0] for name in names}
    if roots != {"github-credibility-check"}:
        raise RuntimeError(f"Unexpected archive roots: {sorted(roots)}")
    forbidden = [
        name for name in names
        if "/evals/" in f"/{name}/"
        or "/__pycache__/" in f"/{name}/"
        or name.endswith((".pyc", ".pyo"))
    ]
    if forbidden:
        raise RuntimeError(f"Forbidden release files: {forbidden}")
    required = {
        "github-credibility-check/SKILL.md",
        "github-credibility-check/agents/openai.yaml",
        "github-credibility-check/scripts/audit_repo.py",
        "github-credibility-check/scripts/score_report.py",
        "github-credibility-check/references/scorecard-template.json",
    }
    if missing := sorted(required - names):
        raise RuntimeError(f"Missing release files: {missing}")


def main() -> int:
    python = sys.executable
    validator = ROOT / "scripts" / "quick_validate.py"
    packager = ROOT / "scripts" / "package_skill.py"
    run(python, SKILL / "evals" / "test_score_report.py")
    run(python, validator, SKILL, "--strict")
    run(python, SKILL / "scripts" / "validate_calibration.py", SKILL / "references" / "calibration-repos.json")
    DIST.mkdir(parents=True, exist_ok=True)
    run(python, packager, SKILL, DIST)
    verify_archive(DIST / "github-credibility-check.skill")
    run(python, ROOT / "scripts" / "security_scan.py")
    print(DIST / "github-credibility-check.skill")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
