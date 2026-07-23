# Data provenance and schemas

The CSV files in this directory are derivative tables reconstructed from the public source-data workbook associated with:

Narayanan H, Hinckley JA, Barry R, et al. *Accelerating cell culture media development using Bayesian optimization-based iterative experimental design*. Nature Communications 16, 6055 (2025). DOI: `10.1038/s41467-025-61113-5`.

The source article and source data are distributed under CC BY 4.0. The original workbook should be obtained from the publisher. These compact derivative tables are included only to reproduce the reported secondary analysis.

## Files

| File | Rows | Purpose |
|---|---:|---|
| `pbmc_media_blend.csv` | 24 | Four-component PBMC media mixtures, round, and average viability |
| `pbmc_cytokine_homeostasis.csv` | 13 | Viability and B/NK/T-cell changes for cytokine formulations |
| `kphaffii_four_factor_train.csv` | 86 | Seven-round four-factor protein-production experiment |
| `kphaffii_four_factor_validation.csv` | 16 | Independently held-out validation conditions |
| `kphaffii_nine_factor.csv` | 77 | Seven-round nine-factor experiment |

## Important interpretation limits

- Experimental rows are not independent when they arise from the same sequential campaign; validation must respect round order.
- The four-factor validation set tests endpoint prediction and ranking, not continuous bioreactor control.
- The PBMC homeostasis table supports a methodological non-compensatory score; it does not establish clinical or manufacturing suitability.
- No CHO, HEK293, proprietary media, patient, or confidential company data are included.
