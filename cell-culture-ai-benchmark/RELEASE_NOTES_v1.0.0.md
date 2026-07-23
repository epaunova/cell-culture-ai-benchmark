# v1.0.0 - First archived benchmark release

This release contains the exact code, derivative public-data tables, precomputed outputs, figures, tests, and manuscript source for the Cell-Culture AI Benchmark.

## Included analyses

- Random, round-blocked, and forward-round validation across three sequential media-development tasks.
- Independent evaluation on 16 held-out four-factor *K. phaffii* conditions.
- Separate reporting of point error, ranking, and calibration limitations.
- Non-compensatory PBMC homeostasis scoring.
- Pareto-efficient productivity/process-load ranking.

## Reproduce

```bash
python -m pip install -r requirements.txt
python analysis.py
python verify_precomputed.py
```

## Scientific boundary

This is a secondary analysis of public data. It is not a prospective wet-lab validation, a commercial media recommendation, or evidence of host-agnostic transfer to CHO or HEK293.
