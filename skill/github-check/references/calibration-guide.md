# Calibration Guide

Use this guide to test whether the credibility rubric generalizes before
changing weights or thresholds.

## Calibration Set

Maintain seed cases in `references/calibration-repos.json`. Include at least:

- Mature infrastructure/framework projects.
- Healthy early-stage projects under six months old.
- Documentation, awesome-list, dataset, and model repositories.
- Commercial open-source projects with disclosed paid offerings.
- Projects with documented star giveaways or platform star removals.
- Repositories with strong marketing but weak code/community evidence.
- Negative controls where rewards exist but are tied to feedback, contributions,
  or bug reports rather than stars.

Do not label a project as manipulated based only on an unusual ratio or growth
curve. A positive manipulation label requires a direct source such as a reward
campaign, acknowledged purchased stars, platform enforcement, or a documented
coordinated scheme.

When a document contains both a star request and a giveaway, verify the exact
reward condition. Rewarding accepted feedback or merged contributions is not a
reward-for-star campaign.

## Evaluation Fields

For every case record:

```text
repo
repo_type
collection_date
expected_band
direct_evidence
credible_alternative_explanations
signal_scores
weighted_score
adoption_risk
reviewer_notes
```

## Calibration Procedure

1. Run `audit_repo.py --mode standard` for every case.
2. Complete manual website, community, and campaign checks.
3. Score without looking at the expected band.
4. Compare false positives and false negatives by repo type.
5. Change one threshold or weight at a time.
6. Rerun the full set and document the effect.

Prioritize reducing false accusations over maximizing manipulation detection.
Keep adoption risk separate from credibility during calibration.

For rate-limited environments, use `scripts/run_calibration.py` with `--limit`
and a persistent output directory. Re-running the command resumes from cached
repository results. Automated summaries are evidence collection only; a reviewer
must still complete direct-evidence and alternative-explanation fields.

Before publishing calibration changes, run:

```bash
python scripts/validate_calibration.py
```

Suspicious labels must use commit-pinned evidence URLs so later README edits do
not silently change the basis of the label.
