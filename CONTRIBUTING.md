# Contributing

## Setup

```bash
python -m pip install -r requirements.txt
python scripts/build_release.py
```

## Evidence Requirements

- Separate observed facts from inference and record confidence limits.
- Severe A=1 or B=1 scores require direct evidence and an exact quote.
- GitHub blob evidence used for an override must contain a full commit SHA.
- Record plausible alternative explanations for suspicious signals.
- Never infer paid or automated stars from ratios or growth anomalies alone.
- Add or update a regression or calibration case for scoring behavior changes.
- Never include tokens, private repository data, raw local audits, or personal paths.

The release build and security scan must pass before review.
