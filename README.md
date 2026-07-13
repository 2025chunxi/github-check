# github-credibility-check

A Codex Skill for evidence-based GitHub repository credibility and adoption-risk
assessment.

> Status: `v0.1.0-beta`. The collection and scoring workflow is tested and
> calibrated; heuristic conclusions remain decision support, not proof.

[简体中文](README.zh-CN.md)

## What It Does

- Collects repository, commit, contributor, release, tag, code-tree, test, CI,
  license, Issue/PR, and package-registry evidence.
- Supports `quick`, `standard`, and `deep` audit modes.
- Distinguishes repository credibility from operational adoption risk.
- Scores six signals: star integrity, claim verifiability, code substance,
  community substance, marketing versus implementation, and commercial conflict.
- Requires direct evidence and exact quotes before severe A=1 or B=1 overrides.
- Uses fixed-commit calibration examples and a negative control against false
  reward-for-star findings.
- Produces deterministic JSON and Markdown reports with explicit evidence limits.

## Why It Matters

Repository popularity is not the same as trustworthiness or production fitness.
This Skill makes source collection, confidence, alternative explanations,
override rules, and adoption risks reviewable instead of relying on a single
opaque model judgment.

## Install

Download `github-credibility-check.skill` from the latest GitHub Release and
extract its top-level `github-credibility-check` folder under
`$CODEX_HOME/skills` or `~/.codex/skills`. Start a new Codex task so Skill
metadata is reloaded.

The source Skill lives at `skill/github-credibility-check` for GitHub-based
installers.

## Build And Verify

Requires Python 3.11 or newer. PyYAML is used only by repository release tooling.

```bash
python -m pip install -r requirements.txt
python scripts/build_release.py
```

Output: `dist/github-credibility-check.skill`.

The build runs scorecard regression tests, strict Skill validation, the eight-case
calibration validator, archive checks, and a repository-wide secret, PII,
private-path, and archive-safety scan. Live GitHub calls are excluded from CI.

## Authentication And Privacy

`GITHUB_TOKEN` is optional but recommended for higher API limits. It is read from
the environment, used only in request headers, and never written into reports.
Do not put tokens in command arguments, scorecards, fixtures, or issue reports.

## Evidence Boundary

- Star anomalies and ratios alone do not prove paid or automated stars.
- A credible repository can still have high maintenance, security, or license risk.
- Missing external evidence lowers confidence; it must not be silently invented.
- Run current security and compatibility checks before production adoption.

## License

MIT. See [LICENSE](LICENSE).
