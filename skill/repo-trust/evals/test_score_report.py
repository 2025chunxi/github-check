#!/usr/bin/env python3
"""Regression checks for deterministic credibility scoring."""

from __future__ import annotations

import sys
import unittest
from copy import deepcopy
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = SKILL_ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from score_report import calculate, load_json  # noqa: E402


class ScoreReportTests(unittest.TestCase):
    def setUp(self) -> None:
        self.scorecard = load_json(Path(__file__).with_name("scorecard-valid-override.json"))
        self.audit = load_json(Path(__file__).with_name("audit-fixture.json"))

    def test_applies_override_and_preserves_adoption_risk(self) -> None:
        result = calculate(self.scorecard, self.audit)
        self.assertEqual(result["raw_score"], 71)
        self.assertEqual(result["final_score"], 54)
        self.assertEqual(result["verdict"], "suspicious")
        self.assertEqual(result["adoption_risk"]["level"], "low")
        self.assertEqual(result["adoption_risk"]["status"], "assessed")

    def test_rejects_untouched_template(self) -> None:
        template = load_json(SKILL_ROOT / "references" / "scorecard-template.json")
        with self.assertRaisesRegex(ValueError, "template must be false"):
            calculate(template)

    def test_rejects_audit_for_another_repository(self) -> None:
        audit = deepcopy(self.audit)
        audit["evidence"]["repo"] = "another/repository"
        with self.assertRaisesRegex(ValueError, "audit repo must match"):
            calculate(self.scorecard, audit)

    def test_rejects_unpinned_github_override_evidence(self) -> None:
        scorecard = deepcopy(self.scorecard)
        scorecard["signals"]["A"]["evidence"][0]["source"] = (
            "https://github.com/CyberStrategyInstitute/ai-safe2-framework/blob/main/VANGUARD_PROGRAM.md"
        )
        with self.assertRaisesRegex(ValueError, "40-character commit SHA"):
            calculate(scorecard)


if __name__ == "__main__":
    unittest.main()
