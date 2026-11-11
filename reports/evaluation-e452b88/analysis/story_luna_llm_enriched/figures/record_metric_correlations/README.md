# Metric Correlations Across All Available Direction Records

Each observation is one matched (dataset, model, direction) score-table row for a fixed prompt. These are native direction aggregates, NOT individual translation records. No averaging across directions, models, prompts or datasets. Pairwise finite support uses every available matched row; no all-model/all-prompt filter. Prompting-change correlations require both metric endpoints for both prompts and subtract few-shot minus zero-shot before correlating. Constant vectors and fewer than three observations are NA, including diagonals. Per-dataset figures use shared general metrics and Luna llm_enriched terms; pooled figures retain all Luna groups as separate columns and pool all datasets directly, without equal-dataset weighting. Dataset composition can affect pooled coefficients. Row counts do not establish matched underlying translations; model/text reuse creates dependence. No significance inference or causal claims.

[Coefficients, exact paired keys/vectors and row-count flags](../../tables/record_metric_correlations/correlations.csv)

Rebuild: `uv run --no-sync python scripts/render_evaluation_results.py --record-metric-correlations-only`.

- dataset_correlations_zero_shot: [PNG](dataset_correlations_zero_shot.png) | [PDF](dataset_correlations_zero_shot.pdf)
- dataset_correlations_few_shot: [PNG](dataset_correlations_few_shot.png) | [PDF](dataset_correlations_few_shot.pdf)
- prompting_change_agreement: [PNG](prompting_change_agreement.png) | [PDF](prompting_change_agreement.pdf)
- metric_correlations_all_datasets_zero_shot: [PNG](metric_correlations_all_datasets_zero_shot.png) | [PDF](metric_correlations_all_datasets_zero_shot.pdf)
- metric_correlations_all_datasets_few_shot: [PNG](metric_correlations_all_datasets_few_shot.png) | [PDF](metric_correlations_all_datasets_few_shot.pdf)
