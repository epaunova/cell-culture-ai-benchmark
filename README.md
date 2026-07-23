# Cell-Culture AI Benchmark
Markdown
[![DOI](https://zenodo.org/badge/1309680608.svg)](https://doi.org/10.5281/zenodo.21506133)


[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![Code license: MIT](https://img.shields.io/badge/code%20license-MIT-green.svg)](LICENSE)
[![CI](https://github.com/arcentlabs/cell-culture-ai-benchmark/actions/workflows/ci.yml/badge.svg)](https://github.com/arcentlabs/cell-culture-ai-benchmark/actions/workflows/ci.yml)

Reproducible public-data analysis, held-out validation, Pareto ranking, and non-compensatory biological scoring for:

> **Round-Aware Validation and Constraint-Aware Ranking for AI-Guided Cell-Culture Media Development: A Public-Data Benchmark**

**Author:** Eva Paunova  
**Affiliation:** ArcentLabs, Europe  
**Contact:** eva@arcentlabs.com

## Why this repository exists

AI-guided media development is sequential: later experimental rounds are chosen using information from earlier rounds. Random cross-validation can therefore give overly optimistic estimates by mixing future and past rounds. Candidate selection can also hide unacceptable biological or process trade-offs when all objectives are collapsed into one weighted score.

This repository provides an auditable benchmark with:

- 24 PBMC media-blend experiments collected over four rounds;
- 86 four-factor *Komagataella phaffii* experiments over seven rounds;
- 16 independently held-out four-factor validation conditions;
- 77 nine-factor *K. phaffii* experiments over seven rounds;
- random, round-blocked, and forward-round validation;
- mean, ridge, random-forest, and extra-trees baselines;
- separate point-error and rank-correlation reporting;
- a non-compensatory PBMC homeostasis score;
- a productivity-process-load Pareto analysis.

All analyses use public source data. No proprietary media formulations or company datasets are included.

## Key precomputed results

| Result | Value |
|---|---:|
| PBMC Extra Trees RMSE, random CV | 14.79 percentage points |
| PBMC Extra Trees RMSE, round-blocked | 18.17 percentage points |
| PBMC Extra Trees RMSE, forward-round | 18.60 percentage points |
| Four-factor held-out Ridge Spearman | 0.747 |
| Four-factor held-out Ridge R² | -0.188 |
| Top PBMC homeostasis formulation | 11 |
| Pareto-efficient four-factor candidates | 6 |

The held-out *K. phaffii* result is intentionally reported with both ranking and absolute-transfer metrics: useful ordering can coexist with negative R².

## Quick start

### 1. Create an environment

```bash
python -m venv .venv
```

Activate it:

```bash
# macOS / Linux
source .venv/bin/activate

# Windows PowerShell
.venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

For tests:

```bash
python -m pip install -r requirements-dev.txt
pytest -q
```

### 2. Verify the included results

```bash
python verify_precomputed.py
```

This checks file integrity, row counts, key reported metrics, the PBMC homeostasis winner, and the Pareto-front size.

### 3. Reproduce the full analysis

```bash
python analysis.py
```

The script regenerates all tables, the JSON summary, and the PDF/PNG figures. On a typical laptop the run should complete in well under a few minutes, although runtime depends on CPU and library versions.

### 4. Compile the manuscript

```bash
cd manuscript
pdflatex main.tex
pdflatex main.tex
```

## Repository structure

```text
.
├── analysis.py                       # Complete deterministic analysis and figure generation
├── verify_precomputed.py             # Fast integrity and result verification
├── data/                             # Public-data derivative CSV files
├── outputs/                          # Reported metrics, rankings, and JSON summary
├── figures/                          # Publication figures in PDF and PNG
├── manuscript/                       # Preprint PDF, LaTeX, bibliography, and metadata
├── tests/                            # Lightweight reproducibility tests
├── .github/workflows/                # Automatic CI and manual full reproduction
├── CITATION.cff                      # GitHub/Zenodo citation metadata
├── .zenodo.json                      # Zenodo release metadata
├── requirements.txt                  # Runtime dependencies
├── requirements-dev.txt              # Test dependencies
└── UPLOAD_AND_RELEASE_GUIDE_BG.md     # Bulgarian upload and DOI instructions
```

## Data provenance

The derivative CSV files were reconstructed from the public source-data workbook accompanying:

Narayanan H, Hinckley JA, Barry R, et al. **Accelerating cell culture media development using Bayesian optimization-based iterative experimental design.** *Nature Communications* 16, 6055 (2025). DOI: `10.1038/s41467-025-61113-5`.

The source article and data are distributed under CC BY 4.0. The original workbook is not redistributed here. See [`data/README.md`](data/README.md) for the exact derivative tables and interpretation limits.

## Reproducibility policy

- Experimental rounds define the prospective validation structure.
- Random cross-validation is reported only as a comparison, not as the preferred deployment estimate.
- Ranking metrics and absolute prediction errors are kept separate.
- Biological homeostasis uses a worst-dimension utility, so one strong outcome cannot hide a failed cell-population requirement.
- Pareto ranking preserves multiple efficient media candidates rather than forcing one undocumented weighted optimum.
- CI checks schemas and key reported values; the complete analysis is also available as a manually triggered workflow.

## Scientific scope and limitations

This repository does **not** establish:

- host-agnostic transfer to CHO or HEK293;
- prospective wet-lab validation by ArcentLabs;
- commercial media superiority;
- manufacturing cost or product-quality validation;
- readiness for autonomous process control.

The process-load variable is an illustrative normalized proxy, not a monetary or manufacturing-cost model.

## Citation

Use the citation suggested by GitHub from [`CITATION.cff`](CITATION.cff). After creating the first Zenodo archive, cite the **version-specific DOI** for exact reproducibility.

## License

Original analysis code is released under the MIT License. The manuscript, figures, and derivative public-data tables are not automatically covered by the code license. See [`LICENSE_SCOPE.md`](LICENSE_SCOPE.md).
