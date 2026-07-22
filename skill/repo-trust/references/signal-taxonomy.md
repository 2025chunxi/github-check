# Signal Taxonomy — Extended Pattern Reference

This file provides supplementary depth for each signal category.
The SKILL.md decision tables are self-contained and authoritative.
Use this file for additional detection nuance and edge case examples.

## Table of Contents

- Signal A: star integrity patterns.
- Signal B: claim verifiability patterns.
- Signal C: code substance patterns.
- Signal D: community substance patterns.
- Signal E: marketing versus substance patterns.
- Signal F: commercial intent patterns.
- Pattern combinations and supplementary patterns.

---

## Signal A — Extended Star Integrity Patterns

### A1 · Confirmed star purge
GitHub may remove stars associated with inauthentic activity such as bot accounts
or coordinated campaigns. A tracker peak ≥60% above the current GitHub count is
a strong anomaly to investigate, but it is not proof by itself.
Why 60% and not 40%: Trendshift/star-history.com data may lag real-time by 1–2 weeks
and can over-report due to caching. A 40% gap could be a data sync artifact; 60%+ is
much harder to explain without a purge event.
Corroborating evidence: if star-farming (A2) is ALSO confirmed, lower the confidence
threshold — any purge percentage above 30% with confirmed A2 should score A = 1.

### A2 · Active star-farming campaign — detection nuance
The giveaway language must offer something in exchange for the starring action.
- ✅ "Star our repo to enter the giveaway" — clear exchange
- ✅ "We'll give 10M tokens to 30 winners who star by Friday" — clear exchange
- ❌ "We just hit 1k stars! Celebrating!" — celebration post, not farming
- ❌ "Check out our repo and give us a star if you like it" — organic ask, not farming
Key: is there a material reward contingent on the starring action?

### A3 · Viral media exemption — how to verify
To claim the exemption, you must find a specific qualifying event:
- Hacker News: search `site:news.ycombinator.com "[repo-name]"` — must be front page
- Product Hunt: search `site:producthunt.com "[repo-name]"` — must be #1–3 of the day
- Major tech outlet: TechCrunch, The Verge, Ars Technica, InfoQ, etc.
- Academic paper citation: the repo is cited in a published paper that went viral
If you cannot find a specific qualifying event, the exemption does not apply.

### A4 · Spike-plateau vs S-curve distinction
- Organic viral growth: gradual increase → acceleration → plateau (S-curve shape)
- Fake star growth: baseline → vertical spike over 1–2 weeks → immediate flat plateau
- Bot purchase: baseline → instantaneous step function → flat (within hours)
The spike-plateau pattern is A4. The step function is a stronger variant (also score A = 2).

### A5 · Regional ecosystem note
Chinese GitHub ecosystem (projects with Chinese-language README, hosted on related
platforms) naturally has different star/fork behavior. Chinese developers "star" as
bookmarks more commonly than Western developers. Adjust A3 threshold to 15:1 for
repos where the primary audience is Chinese developers.

---

## Signal B — Extended Claim Verifiability Patterns

### B1 · Internal benchmark — why it matters
A company testing its own product on a task set it designed will almost always produce
favorable results. Even without malicious intent, the following selection biases apply:
- Task selection bias: naturally gravitate toward tasks where the product excels
- Baseline selection bias: compare against an older or worse configuration of competitors
- Metric selection bias: report the metric that shows best results
Without independent reproduction, no quantitative claim can be taken at face value.

### B2 · Weasel phrase taxonomy
Complete list of phrases that make a claim unfalsifiable:
"up to X%", "as much as Y×", "in typical scenarios", "for most use cases",
"can achieve", "potential savings of", "up to X faster", "reduced costs by up to",
"in our testing", "internal benchmarks show", "in our experience",
"users report", "commonly observed", "average savings vary".

### B3 · Self-benchmark disclosure minimum
A self-benchmark that discloses: (a) the exact task set used, (b) the model versions
compared, (c) the prompt templates used, and (d) the raw results data — is Tier 2
even without third-party reproduction. Most project benchmarks disclose none of these.

### B5 · Version-pinning as falsifiability proxy
Claims without version pins cannot be falsified when the comparison becomes stale.
"Outperforms GPT-4" could have been true in March 2024 and false by October 2024.
A claim with no version pin is epistemically equivalent to an undated claim.

---

## Signal C — Extended Code Substance Patterns

### C1 · Commit density calibration by project type
The 3 commits/month threshold is calibrated for a full application or framework.
Adjust for:
- Library/SDK: 2 commits/month is acceptable (fewer moving parts)
- CLI tool: 2 commits/month acceptable
- Agent framework with claimed 20+ features: 10 commits/month minimum expected
- Infrastructure/DevOps tool: 5 commits/month minimum expected

### C2 · Single-author exemption
Solo founder projects are common and legitimate. C2 only applies when the project
claims "community-built", "open source contributions welcome", or "X contributors"
in its marketing, but the commit history shows a single author.

### C4 · Feature-to-file verification method
For each headline feature (e.g., "Smart LLM Router"):
1. Search the README for the feature section
2. Find the claimed behavior (e.g., "routes by complexity")
3. Search the repo file tree for a plausible implementation file (router.py, routing.ts)
4. If browser, GitHub raw, or API access can read the file, check for at least one function/class related to
   the claimed behavior
5. If no file is found, mark as C4 (vaporware feature)

### C5 · AI-generated code — detection signals
These are indicators, not proof. Note them but don't score solely on this basis:
- Entire codebase created in < 72 hours (check first and last commit timestamps)
- All files have identical, overly formal docstring structure
- No typos, no debug comments, no "TODO" markers anywhere in the code
- Commit history is suspiciously clean (real iterative development leaves messier history)
- Function names are unusually verbose and self-describing (LLM style)

---

## Signal D — Extended Community Substance Patterns

### D1 · Fork quality check procedure
Navigate to `https://github.com/[owner/repo]/forks` and pick 5 forks at random
(not the most recent — use page 2 or 3 if many exist).
For each fork, check: does it have any commits beyond the original?
A fork with original commits = active use (someone is building something).
A fork with zero original commits = bookmark behavior, not development.

### D4 · Download-to-star ratio calibration
These are rough reference ratios for healthy developer tools:
- CLI tools and utilities: 5–20 downloads per star per month
- Libraries/frameworks: 10–50 downloads per star per month
- AI/ML tools: 2–10 downloads per star per month (higher barrier to install)
- Developer tools (editors, IDEs): 0.5–5 downloads per star per month
If monthly downloads are < 0.1 per star per month for any category, this is suspicious.

### D5 · Independent tutorial quality tiers
Not all "independent" content is equal:
- Tier 1: Technical deep-dive on an independent dev blog with original code examples
- Tier 2: Community forum post with hands-on usage report (Reddit, HN, dev.to)
- Tier 3: AI-generated summary article that mostly paraphrases the README
Only count Tier 1 and Tier 2 as genuine independent adoption signals.

---

## Signal E — Extended Marketing vs Substance Patterns

### E1 · Buzzword-wrapping — common examples
| Marketing name | What it actually is |
|---|---|
| "Memory Dream Consolidation" | Periodic memory summarization (standard RAG) |
| "Four-Tier Cognitive Architecture" | A categorization scheme for prompt types |
| "Denial Ledger" | A counter that pauses when threshold is hit |
| "Unified Consciousness Loop" | A single event dispatch loop |
| "Adaptive Reasoning Engine" | Routing between models |
| "Semantic Memory Fabric" | A vector database |
| "Neural Context Bridge" | Cross-session context injection |

Test: describe the feature in a 10-word plain sentence. If a senior developer would say
"oh, that's just a [standard pattern]", it's E1.

### E3 · Roadmap-as-feature detection
Signs that a "feature" is actually unshipped:
- Listed with 🚧, ⏳, 🔜, or "Coming Soon" anywhere in the section
- No corresponding import or module in the codebase
- GitHub issue exists titled "Implement [feature name]" and is still open
- README has a separate "Roadmap" section that overlaps with "Features" section

---

## Signal F — Extended Commercial Intent Patterns

### F1 · OSS-as-funnel — neutral unless amplified
The pattern itself is not deceptive. Flag it as context, not as a penalty, unless:
- The hosted tier provides functionality that the open-source version cannot
  (creating dependency and making the "free open-source" claim misleading)
- The commercial pressure is causing metric inflation (A signals)
- The README primarily markets the hosted service over the open-source project

### F2 · Giveaway-as-acquisition — why this is worse than star farming alone
A standard star-farming giveaway (cash prize, merch) is bad but at least separable
from the product. When the prize is the product's own tokens/credits/API access:
1. The project acquires commercial leads while artificially inflating GitHub metrics
2. Winners are now users of the commercial product (double benefit)
3. The giveaway cost is effectively subsidized by inflated fundraising valuation
This creates a compounding incentive that makes the fraud more rational and therefore
more likely to be intentional rather than naive.

---

## Pattern Combination Reference

When multiple patterns co-occur, the combination is more damning than the sum of parts.
Apply +1 to the combination's most relevant signal when 2+ patterns from a row are found:

| Combination | Signals affected | Interpretation |
|---|---|---|
| A1 + A2 + B1 | A and B | Purge + confirmed farming + self-data = nothing can be trusted |
| A1 + C1 | A and C | Fake popularity + thin code = manufactured reputation |
| B1 + B4 + E5 | B and E | All validation is self-referential |
| C1 + C3 + E4 | C and E | Marketing-first project, code is secondary |
| F2 + A2 + F1 | A and F | Commercial star-to-lead pipeline confirmed |
| D4 + A3 | A and D | Stars are pure vanity, no real adoption |

---

## Supplementary Patterns — Added in v2

### E6 · Dead links and inoperative demos
**Detection:** README or official website contains "Try it now", "Live Demo",
"Playground", or similar CTA links. Open or request each URL. Return of HTTP 404,
domain-not-found, or hosting provider's default error page = demo infrastructure
abandoned after initial hype push.
**Weight:** Minor for a single dead link. Moderate if ≥50% of demo links dead.
Major if ALL demo links dead while project claims "actively maintained".

### E7 · New org with single repo
**Detection:** GitHub org was created within 4 weeks of the repo AND has no other
public repositories. Indicates an org spun up to manufacture the appearance of an
established team behind a single hype project.
**Weight:** Minor alone. Moderate when combined with any Signal A red flag.

### Updated Pattern Combination — E6/E7 variants
| Combination | Signals affected | Interpretation |
|---|---|---|
| E6 + C1 | C and E | Dead demos + thin commits = project was never real |
| E7 + A2 + F2 | A, E, F | New org + giveaway + commercial acquisition = purpose-built hype entity |
