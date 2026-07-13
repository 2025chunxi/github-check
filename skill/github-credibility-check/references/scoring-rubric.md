# Scoring Rubric — Reference & Worked Examples

This file supplements SKILL.md. All scoring rules authoritative to SKILL.md.
Use this file for calibration examples and edge case scoring guidance.

---

## WCS Lookup Table (complete)

The table below contains every possible WCS value. Find each signal's score,
look up its contribution, and sum all six columns.

| Score | A (×4) | B (×5) | C (×4) | D (×3) | E (×2) | F (×2) |
|---|---|---|---|---|---|---|
| 5 | 20 | 25 | 20 | 15 | 10 | 10 |
| 4 | 16 | 20 | 16 | 12 | 8 | 8 |
| 3 | 12 | 15 | 12 | 9 | 6 | 6 |
| 2 | 8 | 10 | 8 | 6 | 4 | 4 |
| 1 | 4 | 5 | 4 | 3 | 2 | 2 |

Max = 100 (all 5s). Min = 20 (all 1s).

---

## Verdict Threshold Quick Reference

| WCS | Verdict | Recommended Posture |
|---|---|---|
| 75–100 | CREDIBLE | Safe to adopt. Note any unverified claims as items to watch. |
| 55–74 | MIXED | Adopt with caution. Verify headline metrics independently. |
| 35–54 | SUSPICIOUS | Not safe to build on. Independent validation required. |
| 20–34 | UNRELIABLE | Do not adopt. Multiple confirmed deception patterns. |

---

## Override Rule Summary

Override rules take precedence over WCS thresholds. Apply in order:

1. Signal A = 1 AND Signal C ≤ 2 → **UNRELIABLE**, cap WCS at 34
2. Signal A = 1 OR Signal B = 1 → **SUSPICIOUS**, cap WCS at 54
3. A ≤ 2 AND B ≤ 2 AND F ≤ 2 → **SUSPICIOUS**, cap WCS at 54
4. No override → use WCS verdict table

---

## Worked Example 1 — OpenSquilla (UNRELIABLE)

**Data collected:**
- Stars: 4 (current GitHub) vs 3,200+ (Trendshift peak) = 98% drop → A1 triggered
- Confirmed giveaway: "Star our repo → 10M token giveaway" → A2 triggered
- "60-80% cost savings" footnoted as "internal testing, typical scenarios" → B1
- Self-written ✅/❌ comparison table → B4
- 5 commits on main branch, project claims production-ready → C1 (< 3/month for 2 weeks)
- 4 real stars, 0 forks currently; no external PRs → D low
- "Memory Dream Consolidation", "Four-Tier Cognitive Architecture" → E1 × 2
- "Claim Free Tokens" Tally form; SaaS tier; giveaway = commercial acquisition → F2

**Scoring:**

```
A score = 1  → A contribution = 4
B score = 2  → B contribution = 10
C score = 2  → C contribution = 8
D score = 2  → D contribution = 6
E score = 2  → E contribution = 4
F score = 2  → F contribution = 4

WCS = 4 + 10 + 8 + 6 + 4 + 4 = 36
```

**Override check:** A = 1 AND C ≤ 2 → Force UNRELIABLE, cap at 34.

**Final: UNRELIABLE (WCS 34)**

---

## Worked Example 2 — Healthy Project (CREDIBLE)

*Hypothetical: a mature, honest open-source library*

**Data collected:**
- Stars: 12,400 / Forks: 2,100 → ratio = 5.9:1 (clean)
- No giveaway posts found
- Star trajectory: gradual S-curve over 18 months
- Independent blog posts: 23 found
- PyPI downloads: 180,000/month (14.5 per star per month, very healthy)
- 847 commits over 24 months = 35 commits/month
- Detailed commit messages, extensive test suite
- Claims linked to arXiv paper and public benchmark leaderboard
- Comparison table exists but acknowledges project weaknesses
- Apache 2.0, no SaaS tier

**Scoring:**

```
A score = 5  → A contribution = 20
B score = 4  → B contribution = 20  (one claim is Tier 2, not Tier 1)
C score = 5  → C contribution = 20
D score = 5  → D contribution = 15
E score = 4  → E contribution = 8   (comparison table exists but honest)
F score = 5  → F contribution = 10

WCS = 20 + 20 + 20 + 15 + 8 + 10 = 93
```

**Override check:** No override conditions triggered.

**Final: CREDIBLE (WCS 93)**

---

## Worked Example 3 — Mixed/Early Stage (MIXED)

*Hypothetical: a promising but early-stage tool with honest but thin evidence*

**Data collected:**
- Stars: 890 / Forks: 145 → ratio = 6.1:1 (clean)
- No giveaway found
- Project is 3 months old
- npm downloads: 2,400/month (2.7 per star per month, acceptable for AI tool)
- 45 commits total over 3 months = 15 commits/month
- Good commit messages
- Claims include "50% faster" footnoted as "benchmarked on our test suite" (Tier 2)
- No comparison table
- Seed-stage company, disclosed in README

**Scoring:**

```
A score = 5  → A contribution = 20
B score = 3  → B contribution = 15  (Tier 2 benchmarks, some hedging)
C score = 4  → C contribution = 16  (15/month is good for 3-month project)
D score = 3  → D contribution = 9   (early; no external PRs yet, acceptable)
E score = 4  → E contribution = 8   (minor marketing language only)
F score = 4  → F contribution = 8   (commercial but disclosed and not inflating)

WCS = 20 + 15 + 16 + 9 + 8 + 8 = 76
```

**Override check:** No override conditions triggered.

**Final: CREDIBLE (WCS 76)**

*Note: This project would receive the note: "Claims rest on self-benchmarks only.
Independently test the '50% faster' claim against your own use case before
committing to this dependency."*

---

## Calibration Notes

### Signal B is the hardest 5 to earn
Almost no early-stage project has fully independent benchmark validation.
A 4 on Signal B means: claims present, appropriately hedged, at least one Tier 2
source with disclosed methodology.

### Signal F = 3 is the neutral baseline for commercial OSS
Score F = 3 for any project with a clean hosted tier that doesn't drive metric inflation.
Do not penalize below 3 unless commercial interest demonstrably distorts claims.

### When all data is unavailable (GitHub blocked, no tracker data, etc.)
Score all unavailable signals as 3 (neutral conservative default).
Set Data Confidence to Low.
State in the report: "Limited data available — this analysis has low confidence.
Recommend repeating with direct repository access."

### Age adjustment for Signal C and D
For repos < 6 weeks old: score C and D at 3 regardless of raw metrics (insufficient data).
State explicitly: "Project is [N] days old — signals C and D have insufficient history."
