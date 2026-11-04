# Benchmark Tables and Figures

Generated locally from all 84 checksum-verified grouped summaries. No models or metrics were rerun.

Tables and CSVs retain all 14 metric slots: nine general and five terminology metrics. Twelve have numeric results. Both terminology-success-rate metrics are marked `not_applicable` in every current-run direction group because their native source/reference applicability rules select no eligible rows. Their scores and correlations are NA, not zero. Figures omit success-rate metrics when all their displayed scores or correlations are unavailable.

## Tables

- [Output tokens, ranks, latencies and default-thinking evidence](tables/output_tokens_rank_latency.csv)
- [Chosen 03 cost/rank/latency bubble data](tables/chosen_03_cost_rank_latency.csv)
- [API cost estimates and pricing assumptions](api_cost_estimates.md)
- [Readable performance tables](tables/performance.md)
- [LaTeX table fragments](tables/performance.tex) (requires `graphicx`)
- [Translation-quality data](tables/translation_quality.csv)
- [Terminology data](tables/terminology.csv)
- [All direction-level scores](tables/direction_scores.csv), including historical/native populations
- [Coverage](tables/coverage.csv)
- [Model provenance and source links](tables/model_provenance.csv)
- [Bubble-chart coordinates, sizes, and denominators](tables/bubble_chart_data.csv)
- [Distribution points and scored-row counts](tables/distribution_points.csv)
- [Density-fit sample sizes and status](tables/distribution_regions.csv)
- [All metric correlations and pair-specific supports](tables/metric_correlations.csv)
- [Four least-redundant metric columns](tables/selected_metric_columns.csv)
- [Chosen 01 mixed ranks and displayed scores](tables/chosen_01_mixed_ranks.csv)
- [Chosen 01 per-metric rank contributions and support](tables/chosen_01_rank_components.csv)
- [Chosen 02 latency, mixed ranks and timing support](tables/chosen_02_latency_data.csv)

## Figures

### Chosen Figures

- luna: Chosen 01 Balanced Mixed Rank Google Patents Few Shot: [PNG](figures/chosen/01_balanced_mixed_rank/luna/chosen_01_balanced_mixed_rank_google_patents_few_shot.png) | [PDF](figures/chosen/01_balanced_mixed_rank/luna/chosen_01_balanced_mixed_rank_google_patents_few_shot.pdf)
- luna: Chosen 01 Balanced Mixed Rank Google Patents Zero Shot: [PNG](figures/chosen/01_balanced_mixed_rank/luna/chosen_01_balanced_mixed_rank_google_patents_zero_shot.png) | [PDF](figures/chosen/01_balanced_mixed_rank/luna/chosen_01_balanced_mixed_rank_google_patents_zero_shot.pdf)
- luna: Chosen 01 Balanced Mixed Rank Jrc Articles Few Shot: [PNG](figures/chosen/01_balanced_mixed_rank/luna/chosen_01_balanced_mixed_rank_jrc_articles_few_shot.png) | [PDF](figures/chosen/01_balanced_mixed_rank/luna/chosen_01_balanced_mixed_rank_jrc_articles_few_shot.pdf)
- luna: Chosen 01 Balanced Mixed Rank Jrc Articles Zero Shot: [PNG](figures/chosen/01_balanced_mixed_rank/luna/chosen_01_balanced_mixed_rank_jrc_articles_zero_shot.png) | [PDF](figures/chosen/01_balanced_mixed_rank/luna/chosen_01_balanced_mixed_rank_jrc_articles_zero_shot.pdf)
- luna: Chosen 01 Balanced Mixed Rank Jrc Definitions Few Shot: [PNG](figures/chosen/01_balanced_mixed_rank/luna/chosen_01_balanced_mixed_rank_jrc_definitions_few_shot.png) | [PDF](figures/chosen/01_balanced_mixed_rank/luna/chosen_01_balanced_mixed_rank_jrc_definitions_few_shot.pdf)
- luna: Chosen 01 Balanced Mixed Rank Jrc Definitions Zero Shot: [PNG](figures/chosen/01_balanced_mixed_rank/luna/chosen_01_balanced_mixed_rank_jrc_definitions_zero_shot.png) | [PDF](figures/chosen/01_balanced_mixed_rank/luna/chosen_01_balanced_mixed_rank_jrc_definitions_zero_shot.pdf)
- luna: Chosen 01 Balanced Mixed Rank Overall: [PNG](figures/chosen/01_balanced_mixed_rank/luna/chosen_01_balanced_mixed_rank_overall.png) | [PDF](figures/chosen/01_balanced_mixed_rank/luna/chosen_01_balanced_mixed_rank_overall.pdf)
- original_glm: Chosen 01 Balanced Mixed Rank Google Patents Few Shot: [PNG](figures/chosen/01_balanced_mixed_rank/original_glm/chosen_01_balanced_mixed_rank_google_patents_few_shot.png) | [PDF](figures/chosen/01_balanced_mixed_rank/original_glm/chosen_01_balanced_mixed_rank_google_patents_few_shot.pdf)
- original_glm: Chosen 01 Balanced Mixed Rank Google Patents Zero Shot: [PNG](figures/chosen/01_balanced_mixed_rank/original_glm/chosen_01_balanced_mixed_rank_google_patents_zero_shot.png) | [PDF](figures/chosen/01_balanced_mixed_rank/original_glm/chosen_01_balanced_mixed_rank_google_patents_zero_shot.pdf)
- original_glm: Chosen 01 Balanced Mixed Rank Jrc Articles Few Shot: [PNG](figures/chosen/01_balanced_mixed_rank/original_glm/chosen_01_balanced_mixed_rank_jrc_articles_few_shot.png) | [PDF](figures/chosen/01_balanced_mixed_rank/original_glm/chosen_01_balanced_mixed_rank_jrc_articles_few_shot.pdf)
- original_glm: Chosen 01 Balanced Mixed Rank Jrc Articles Zero Shot: [PNG](figures/chosen/01_balanced_mixed_rank/original_glm/chosen_01_balanced_mixed_rank_jrc_articles_zero_shot.png) | [PDF](figures/chosen/01_balanced_mixed_rank/original_glm/chosen_01_balanced_mixed_rank_jrc_articles_zero_shot.pdf)
- original_glm: Chosen 01 Balanced Mixed Rank Jrc Definitions Few Shot: [PNG](figures/chosen/01_balanced_mixed_rank/original_glm/chosen_01_balanced_mixed_rank_jrc_definitions_few_shot.png) | [PDF](figures/chosen/01_balanced_mixed_rank/original_glm/chosen_01_balanced_mixed_rank_jrc_definitions_few_shot.pdf)
- original_glm: Chosen 01 Balanced Mixed Rank Jrc Definitions Zero Shot: [PNG](figures/chosen/01_balanced_mixed_rank/original_glm/chosen_01_balanced_mixed_rank_jrc_definitions_zero_shot.png) | [PDF](figures/chosen/01_balanced_mixed_rank/original_glm/chosen_01_balanced_mixed_rank_jrc_definitions_zero_shot.pdf)
- original_glm: Chosen 01 Balanced Mixed Rank Overall: [PNG](figures/chosen/01_balanced_mixed_rank/original_glm/chosen_01_balanced_mixed_rank_overall.png) | [PDF](figures/chosen/01_balanced_mixed_rank/original_glm/chosen_01_balanced_mixed_rank_overall.pdf)
- luna: Chosen 02 Latency Vs Mixed Rank Google Patents Few Shot: [PNG](figures/chosen/02_latency_vs_mixed_rank/luna/chosen_02_latency_vs_mixed_rank_google_patents_few_shot.png) | [PDF](figures/chosen/02_latency_vs_mixed_rank/luna/chosen_02_latency_vs_mixed_rank_google_patents_few_shot.pdf)
- luna: Chosen 02 Latency Vs Mixed Rank Google Patents Zero Shot: [PNG](figures/chosen/02_latency_vs_mixed_rank/luna/chosen_02_latency_vs_mixed_rank_google_patents_zero_shot.png) | [PDF](figures/chosen/02_latency_vs_mixed_rank/luna/chosen_02_latency_vs_mixed_rank_google_patents_zero_shot.pdf)
- luna: Chosen 02 Latency Vs Mixed Rank Jrc Articles Few Shot: [PNG](figures/chosen/02_latency_vs_mixed_rank/luna/chosen_02_latency_vs_mixed_rank_jrc_articles_few_shot.png) | [PDF](figures/chosen/02_latency_vs_mixed_rank/luna/chosen_02_latency_vs_mixed_rank_jrc_articles_few_shot.pdf)
- luna: Chosen 02 Latency Vs Mixed Rank Jrc Articles Zero Shot: [PNG](figures/chosen/02_latency_vs_mixed_rank/luna/chosen_02_latency_vs_mixed_rank_jrc_articles_zero_shot.png) | [PDF](figures/chosen/02_latency_vs_mixed_rank/luna/chosen_02_latency_vs_mixed_rank_jrc_articles_zero_shot.pdf)
- luna: Chosen 02 Latency Vs Mixed Rank Jrc Definitions Few Shot: [PNG](figures/chosen/02_latency_vs_mixed_rank/luna/chosen_02_latency_vs_mixed_rank_jrc_definitions_few_shot.png) | [PDF](figures/chosen/02_latency_vs_mixed_rank/luna/chosen_02_latency_vs_mixed_rank_jrc_definitions_few_shot.pdf)
- luna: Chosen 02 Latency Vs Mixed Rank Jrc Definitions Zero Shot: [PNG](figures/chosen/02_latency_vs_mixed_rank/luna/chosen_02_latency_vs_mixed_rank_jrc_definitions_zero_shot.png) | [PDF](figures/chosen/02_latency_vs_mixed_rank/luna/chosen_02_latency_vs_mixed_rank_jrc_definitions_zero_shot.pdf)
- luna: Chosen 02 Latency Vs Mixed Rank Overall: [PNG](figures/chosen/02_latency_vs_mixed_rank/luna/chosen_02_latency_vs_mixed_rank_overall.png) | [PDF](figures/chosen/02_latency_vs_mixed_rank/luna/chosen_02_latency_vs_mixed_rank_overall.pdf)
- original_glm: Chosen 02 Latency Vs Mixed Rank Google Patents Few Shot: [PNG](figures/chosen/02_latency_vs_mixed_rank/original_glm/chosen_02_latency_vs_mixed_rank_google_patents_few_shot.png) | [PDF](figures/chosen/02_latency_vs_mixed_rank/original_glm/chosen_02_latency_vs_mixed_rank_google_patents_few_shot.pdf)
- original_glm: Chosen 02 Latency Vs Mixed Rank Google Patents Zero Shot: [PNG](figures/chosen/02_latency_vs_mixed_rank/original_glm/chosen_02_latency_vs_mixed_rank_google_patents_zero_shot.png) | [PDF](figures/chosen/02_latency_vs_mixed_rank/original_glm/chosen_02_latency_vs_mixed_rank_google_patents_zero_shot.pdf)
- original_glm: Chosen 02 Latency Vs Mixed Rank Jrc Articles Few Shot: [PNG](figures/chosen/02_latency_vs_mixed_rank/original_glm/chosen_02_latency_vs_mixed_rank_jrc_articles_few_shot.png) | [PDF](figures/chosen/02_latency_vs_mixed_rank/original_glm/chosen_02_latency_vs_mixed_rank_jrc_articles_few_shot.pdf)
- original_glm: Chosen 02 Latency Vs Mixed Rank Jrc Articles Zero Shot: [PNG](figures/chosen/02_latency_vs_mixed_rank/original_glm/chosen_02_latency_vs_mixed_rank_jrc_articles_zero_shot.png) | [PDF](figures/chosen/02_latency_vs_mixed_rank/original_glm/chosen_02_latency_vs_mixed_rank_jrc_articles_zero_shot.pdf)
- original_glm: Chosen 02 Latency Vs Mixed Rank Jrc Definitions Few Shot: [PNG](figures/chosen/02_latency_vs_mixed_rank/original_glm/chosen_02_latency_vs_mixed_rank_jrc_definitions_few_shot.png) | [PDF](figures/chosen/02_latency_vs_mixed_rank/original_glm/chosen_02_latency_vs_mixed_rank_jrc_definitions_few_shot.pdf)
- original_glm: Chosen 02 Latency Vs Mixed Rank Jrc Definitions Zero Shot: [PNG](figures/chosen/02_latency_vs_mixed_rank/original_glm/chosen_02_latency_vs_mixed_rank_jrc_definitions_zero_shot.png) | [PDF](figures/chosen/02_latency_vs_mixed_rank/original_glm/chosen_02_latency_vs_mixed_rank_jrc_definitions_zero_shot.pdf)
- original_glm: Chosen 02 Latency Vs Mixed Rank Overall: [PNG](figures/chosen/02_latency_vs_mixed_rank/original_glm/chosen_02_latency_vs_mixed_rank_overall.png) | [PDF](figures/chosen/02_latency_vs_mixed_rank/original_glm/chosen_02_latency_vs_mixed_rank_overall.pdf)
- luna: Chosen 03 Api Cost Vs Rank Latency Google Patents Few Shot: [PNG](figures/chosen/03_api_cost_vs_rank_latency/luna/chosen_03_api_cost_vs_rank_latency_google_patents_few_shot.png) | [PDF](figures/chosen/03_api_cost_vs_rank_latency/luna/chosen_03_api_cost_vs_rank_latency_google_patents_few_shot.pdf)
- luna: Chosen 03 Api Cost Vs Rank Latency Google Patents Zero Shot: [PNG](figures/chosen/03_api_cost_vs_rank_latency/luna/chosen_03_api_cost_vs_rank_latency_google_patents_zero_shot.png) | [PDF](figures/chosen/03_api_cost_vs_rank_latency/luna/chosen_03_api_cost_vs_rank_latency_google_patents_zero_shot.pdf)
- luna: Chosen 03 Api Cost Vs Rank Latency Jrc Articles Few Shot: [PNG](figures/chosen/03_api_cost_vs_rank_latency/luna/chosen_03_api_cost_vs_rank_latency_jrc_articles_few_shot.png) | [PDF](figures/chosen/03_api_cost_vs_rank_latency/luna/chosen_03_api_cost_vs_rank_latency_jrc_articles_few_shot.pdf)
- luna: Chosen 03 Api Cost Vs Rank Latency Jrc Articles Zero Shot: [PNG](figures/chosen/03_api_cost_vs_rank_latency/luna/chosen_03_api_cost_vs_rank_latency_jrc_articles_zero_shot.png) | [PDF](figures/chosen/03_api_cost_vs_rank_latency/luna/chosen_03_api_cost_vs_rank_latency_jrc_articles_zero_shot.pdf)
- luna: Chosen 03 Api Cost Vs Rank Latency Jrc Definitions Few Shot: [PNG](figures/chosen/03_api_cost_vs_rank_latency/luna/chosen_03_api_cost_vs_rank_latency_jrc_definitions_few_shot.png) | [PDF](figures/chosen/03_api_cost_vs_rank_latency/luna/chosen_03_api_cost_vs_rank_latency_jrc_definitions_few_shot.pdf)
- luna: Chosen 03 Api Cost Vs Rank Latency Jrc Definitions Zero Shot: [PNG](figures/chosen/03_api_cost_vs_rank_latency/luna/chosen_03_api_cost_vs_rank_latency_jrc_definitions_zero_shot.png) | [PDF](figures/chosen/03_api_cost_vs_rank_latency/luna/chosen_03_api_cost_vs_rank_latency_jrc_definitions_zero_shot.pdf)
- luna: Chosen 03 Api Cost Vs Rank Latency Overall: [PNG](figures/chosen/03_api_cost_vs_rank_latency/luna/chosen_03_api_cost_vs_rank_latency_overall.png) | [PDF](figures/chosen/03_api_cost_vs_rank_latency/luna/chosen_03_api_cost_vs_rank_latency_overall.pdf)
- original_glm: Chosen 03 Api Cost Vs Rank Latency Google Patents Few Shot: [PNG](figures/chosen/03_api_cost_vs_rank_latency/original_glm/chosen_03_api_cost_vs_rank_latency_google_patents_few_shot.png) | [PDF](figures/chosen/03_api_cost_vs_rank_latency/original_glm/chosen_03_api_cost_vs_rank_latency_google_patents_few_shot.pdf)
- original_glm: Chosen 03 Api Cost Vs Rank Latency Google Patents Zero Shot: [PNG](figures/chosen/03_api_cost_vs_rank_latency/original_glm/chosen_03_api_cost_vs_rank_latency_google_patents_zero_shot.png) | [PDF](figures/chosen/03_api_cost_vs_rank_latency/original_glm/chosen_03_api_cost_vs_rank_latency_google_patents_zero_shot.pdf)
- original_glm: Chosen 03 Api Cost Vs Rank Latency Jrc Articles Few Shot: [PNG](figures/chosen/03_api_cost_vs_rank_latency/original_glm/chosen_03_api_cost_vs_rank_latency_jrc_articles_few_shot.png) | [PDF](figures/chosen/03_api_cost_vs_rank_latency/original_glm/chosen_03_api_cost_vs_rank_latency_jrc_articles_few_shot.pdf)
- original_glm: Chosen 03 Api Cost Vs Rank Latency Jrc Articles Zero Shot: [PNG](figures/chosen/03_api_cost_vs_rank_latency/original_glm/chosen_03_api_cost_vs_rank_latency_jrc_articles_zero_shot.png) | [PDF](figures/chosen/03_api_cost_vs_rank_latency/original_glm/chosen_03_api_cost_vs_rank_latency_jrc_articles_zero_shot.pdf)
- original_glm: Chosen 03 Api Cost Vs Rank Latency Jrc Definitions Few Shot: [PNG](figures/chosen/03_api_cost_vs_rank_latency/original_glm/chosen_03_api_cost_vs_rank_latency_jrc_definitions_few_shot.png) | [PDF](figures/chosen/03_api_cost_vs_rank_latency/original_glm/chosen_03_api_cost_vs_rank_latency_jrc_definitions_few_shot.pdf)
- original_glm: Chosen 03 Api Cost Vs Rank Latency Jrc Definitions Zero Shot: [PNG](figures/chosen/03_api_cost_vs_rank_latency/original_glm/chosen_03_api_cost_vs_rank_latency_jrc_definitions_zero_shot.png) | [PDF](figures/chosen/03_api_cost_vs_rank_latency/original_glm/chosen_03_api_cost_vs_rank_latency_jrc_definitions_zero_shot.pdf)
- original_glm: Chosen 03 Api Cost Vs Rank Latency Overall: [PNG](figures/chosen/03_api_cost_vs_rank_latency/original_glm/chosen_03_api_cost_vs_rank_latency_overall.png) | [PDF](figures/chosen/03_api_cost_vs_rank_latency/original_glm/chosen_03_api_cost_vs_rank_latency_overall.pdf)
- luna: Chosen 04 Prompting Bars Terminology Google Patents: [PNG](figures/chosen/04_zero_vs_few_shot/luna/chosen_04_prompting_bars_terminology_google_patents.png) | [PDF](figures/chosen/04_zero_vs_few_shot/luna/chosen_04_prompting_bars_terminology_google_patents.pdf)
- luna: Chosen 04 Prompting Bars Terminology Jrc Articles: [PNG](figures/chosen/04_zero_vs_few_shot/luna/chosen_04_prompting_bars_terminology_jrc_articles.png) | [PDF](figures/chosen/04_zero_vs_few_shot/luna/chosen_04_prompting_bars_terminology_jrc_articles.pdf)
- luna: Chosen 04 Prompting Bars Terminology Jrc Definitions: [PNG](figures/chosen/04_zero_vs_few_shot/luna/chosen_04_prompting_bars_terminology_jrc_definitions.png) | [PDF](figures/chosen/04_zero_vs_few_shot/luna/chosen_04_prompting_bars_terminology_jrc_definitions.pdf)
- original_glm: Chosen 04 Prompting Bars Terminology Google Patents: [PNG](figures/chosen/04_zero_vs_few_shot/original_glm/chosen_04_prompting_bars_terminology_google_patents.png) | [PDF](figures/chosen/04_zero_vs_few_shot/original_glm/chosen_04_prompting_bars_terminology_google_patents.pdf)
- original_glm: Chosen 04 Prompting Bars Terminology Jrc Articles: [PNG](figures/chosen/04_zero_vs_few_shot/original_glm/chosen_04_prompting_bars_terminology_jrc_articles.png) | [PDF](figures/chosen/04_zero_vs_few_shot/original_glm/chosen_04_prompting_bars_terminology_jrc_articles.pdf)
- original_glm: Chosen 04 Prompting Bars Terminology Jrc Definitions: [PNG](figures/chosen/04_zero_vs_few_shot/original_glm/chosen_04_prompting_bars_terminology_jrc_definitions.png) | [PDF](figures/chosen/04_zero_vs_few_shot/original_glm/chosen_04_prompting_bars_terminology_jrc_definitions.pdf)
- shared_general: Chosen 04 Prompting Bars General Google Patents: [PNG](figures/chosen/04_zero_vs_few_shot/shared_general/chosen_04_prompting_bars_general_google_patents.png) | [PDF](figures/chosen/04_zero_vs_few_shot/shared_general/chosen_04_prompting_bars_general_google_patents.pdf)
- shared_general: Chosen 04 Prompting Bars General Jrc Articles: [PNG](figures/chosen/04_zero_vs_few_shot/shared_general/chosen_04_prompting_bars_general_jrc_articles.png) | [PDF](figures/chosen/04_zero_vs_few_shot/shared_general/chosen_04_prompting_bars_general_jrc_articles.pdf)
- shared_general: Chosen 04 Prompting Bars General Jrc Definitions: [PNG](figures/chosen/04_zero_vs_few_shot/shared_general/chosen_04_prompting_bars_general_jrc_definitions.png) | [PDF](figures/chosen/04_zero_vs_few_shot/shared_general/chosen_04_prompting_bars_general_jrc_definitions.pdf)

### Output Tokens vs Rank and Latency

- Output Tokens Vs Rank Latency Google Patents Few Shot: [PNG](figures/output_tokens/luna/output_tokens_vs_rank_latency_google_patents_few_shot.png) | [PDF](figures/output_tokens/luna/output_tokens_vs_rank_latency_google_patents_few_shot.pdf)
- Output Tokens Vs Rank Latency Google Patents Zero Shot: [PNG](figures/output_tokens/luna/output_tokens_vs_rank_latency_google_patents_zero_shot.png) | [PDF](figures/output_tokens/luna/output_tokens_vs_rank_latency_google_patents_zero_shot.pdf)
- Output Tokens Vs Rank Latency Jrc Articles Few Shot: [PNG](figures/output_tokens/luna/output_tokens_vs_rank_latency_jrc_articles_few_shot.png) | [PDF](figures/output_tokens/luna/output_tokens_vs_rank_latency_jrc_articles_few_shot.pdf)
- Output Tokens Vs Rank Latency Jrc Articles Zero Shot: [PNG](figures/output_tokens/luna/output_tokens_vs_rank_latency_jrc_articles_zero_shot.png) | [PDF](figures/output_tokens/luna/output_tokens_vs_rank_latency_jrc_articles_zero_shot.pdf)
- Output Tokens Vs Rank Latency Jrc Definitions Few Shot: [PNG](figures/output_tokens/luna/output_tokens_vs_rank_latency_jrc_definitions_few_shot.png) | [PDF](figures/output_tokens/luna/output_tokens_vs_rank_latency_jrc_definitions_few_shot.pdf)
- Output Tokens Vs Rank Latency Jrc Definitions Zero Shot: [PNG](figures/output_tokens/luna/output_tokens_vs_rank_latency_jrc_definitions_zero_shot.png) | [PDF](figures/output_tokens/luna/output_tokens_vs_rank_latency_jrc_definitions_zero_shot.pdf)
- Output Tokens Vs Rank Latency Overall: [PNG](figures/output_tokens/luna/output_tokens_vs_rank_latency_overall.png) | [PDF](figures/output_tokens/luna/output_tokens_vs_rank_latency_overall.pdf)
- Output Tokens Vs Rank Latency Google Patents Few Shot: [PNG](figures/output_tokens/original_glm/output_tokens_vs_rank_latency_google_patents_few_shot.png) | [PDF](figures/output_tokens/original_glm/output_tokens_vs_rank_latency_google_patents_few_shot.pdf)
- Output Tokens Vs Rank Latency Google Patents Zero Shot: [PNG](figures/output_tokens/original_glm/output_tokens_vs_rank_latency_google_patents_zero_shot.png) | [PDF](figures/output_tokens/original_glm/output_tokens_vs_rank_latency_google_patents_zero_shot.pdf)
- Output Tokens Vs Rank Latency Jrc Articles Few Shot: [PNG](figures/output_tokens/original_glm/output_tokens_vs_rank_latency_jrc_articles_few_shot.png) | [PDF](figures/output_tokens/original_glm/output_tokens_vs_rank_latency_jrc_articles_few_shot.pdf)
- Output Tokens Vs Rank Latency Jrc Articles Zero Shot: [PNG](figures/output_tokens/original_glm/output_tokens_vs_rank_latency_jrc_articles_zero_shot.png) | [PDF](figures/output_tokens/original_glm/output_tokens_vs_rank_latency_jrc_articles_zero_shot.pdf)
- Output Tokens Vs Rank Latency Jrc Definitions Few Shot: [PNG](figures/output_tokens/original_glm/output_tokens_vs_rank_latency_jrc_definitions_few_shot.png) | [PDF](figures/output_tokens/original_glm/output_tokens_vs_rank_latency_jrc_definitions_few_shot.pdf)
- Output Tokens Vs Rank Latency Jrc Definitions Zero Shot: [PNG](figures/output_tokens/original_glm/output_tokens_vs_rank_latency_jrc_definitions_zero_shot.png) | [PDF](figures/output_tokens/original_glm/output_tokens_vs_rank_latency_jrc_definitions_zero_shot.pdf)
- Output Tokens Vs Rank Latency Overall: [PNG](figures/output_tokens/original_glm/output_tokens_vs_rank_latency_overall.png) | [PDF](figures/output_tokens/original_glm/output_tokens_vs_rank_latency_overall.pdf)

### All Model Scores on Every Metric

- all_terms / luna: All Terminology Metrics: [PNG](figures/all_metrics/all_terms/luna/all_terminology_metrics.png) | [PDF](figures/all_metrics/all_terms/luna/all_terminology_metrics.pdf)
- all_terms / original_glm: All Terminology Metrics: [PNG](figures/all_metrics/all_terms/original_glm/all_terminology_metrics.png) | [PDF](figures/all_metrics/all_terms/original_glm/all_terminology_metrics.pdf)
- externally_verified / luna: All Terminology Metrics: [PNG](figures/all_metrics/externally_verified/luna/all_terminology_metrics.png) | [PDF](figures/all_metrics/externally_verified/luna/all_terminology_metrics.pdf)
- externally_verified / original_glm: All Terminology Metrics: [PNG](figures/all_metrics/externally_verified/original_glm/all_terminology_metrics.png) | [PDF](figures/all_metrics/externally_verified/original_glm/all_terminology_metrics.pdf)
- general: All Metrics Google Patents: [PNG](figures/all_metrics/general/all_metrics_google_patents.png) | [PDF](figures/all_metrics/general/all_metrics_google_patents.pdf)
- general: All Metrics Jrc Articles: [PNG](figures/all_metrics/general/all_metrics_jrc_articles.png) | [PDF](figures/all_metrics/general/all_metrics_jrc_articles.pdf)
- general: All Metrics Jrc Definitions: [PNG](figures/all_metrics/general/all_metrics_jrc_definitions.png) | [PDF](figures/all_metrics/general/all_metrics_jrc_definitions.pdf)
- llm_enriched / luna: All Terminology Metrics: [PNG](figures/all_metrics/llm_enriched/luna/all_terminology_metrics.png) | [PDF](figures/all_metrics/llm_enriched/luna/all_terminology_metrics.pdf)
- llm_enriched / original_glm: All Terminology Metrics: [PNG](figures/all_metrics/llm_enriched/original_glm/all_terminology_metrics.png) | [PDF](figures/all_metrics/llm_enriched/original_glm/all_terminology_metrics.pdf)

### Metric Correlations Within and Across Term Groups

- luna: Metric Correlations All Datasets Few Shot: [PNG](figures/correlations/luna/metric_correlations_all_datasets_few_shot.png) | [PDF](figures/correlations/luna/metric_correlations_all_datasets_few_shot.pdf)
- luna: Metric Correlations All Datasets Zero Shot: [PNG](figures/correlations/luna/metric_correlations_all_datasets_zero_shot.png) | [PDF](figures/correlations/luna/metric_correlations_all_datasets_zero_shot.pdf)
- luna: Metric Correlations Google Patents Few Shot: [PNG](figures/correlations/luna/metric_correlations_google_patents_few_shot.png) | [PDF](figures/correlations/luna/metric_correlations_google_patents_few_shot.pdf)
- luna: Metric Correlations Google Patents Zero Shot: [PNG](figures/correlations/luna/metric_correlations_google_patents_zero_shot.png) | [PDF](figures/correlations/luna/metric_correlations_google_patents_zero_shot.pdf)
- luna: Metric Correlations Jrc Articles Few Shot: [PNG](figures/correlations/luna/metric_correlations_jrc_articles_few_shot.png) | [PDF](figures/correlations/luna/metric_correlations_jrc_articles_few_shot.pdf)
- luna: Metric Correlations Jrc Articles Zero Shot: [PNG](figures/correlations/luna/metric_correlations_jrc_articles_zero_shot.png) | [PDF](figures/correlations/luna/metric_correlations_jrc_articles_zero_shot.pdf)
- luna: Metric Correlations Jrc Definitions Few Shot: [PNG](figures/correlations/luna/metric_correlations_jrc_definitions_few_shot.png) | [PDF](figures/correlations/luna/metric_correlations_jrc_definitions_few_shot.pdf)
- luna: Metric Correlations Jrc Definitions Zero Shot: [PNG](figures/correlations/luna/metric_correlations_jrc_definitions_zero_shot.png) | [PDF](figures/correlations/luna/metric_correlations_jrc_definitions_zero_shot.pdf)
- original_glm: Metric Correlations All Datasets Few Shot: [PNG](figures/correlations/original_glm/metric_correlations_all_datasets_few_shot.png) | [PDF](figures/correlations/original_glm/metric_correlations_all_datasets_few_shot.pdf)
- original_glm: Metric Correlations All Datasets Zero Shot: [PNG](figures/correlations/original_glm/metric_correlations_all_datasets_zero_shot.png) | [PDF](figures/correlations/original_glm/metric_correlations_all_datasets_zero_shot.pdf)
- original_glm: Metric Correlations Google Patents Few Shot: [PNG](figures/correlations/original_glm/metric_correlations_google_patents_few_shot.png) | [PDF](figures/correlations/original_glm/metric_correlations_google_patents_few_shot.pdf)
- original_glm: Metric Correlations Google Patents Zero Shot: [PNG](figures/correlations/original_glm/metric_correlations_google_patents_zero_shot.png) | [PDF](figures/correlations/original_glm/metric_correlations_google_patents_zero_shot.pdf)
- original_glm: Metric Correlations Jrc Articles Few Shot: [PNG](figures/correlations/original_glm/metric_correlations_jrc_articles_few_shot.png) | [PDF](figures/correlations/original_glm/metric_correlations_jrc_articles_few_shot.pdf)
- original_glm: Metric Correlations Jrc Articles Zero Shot: [PNG](figures/correlations/original_glm/metric_correlations_jrc_articles_zero_shot.png) | [PDF](figures/correlations/original_glm/metric_correlations_jrc_articles_zero_shot.pdf)
- original_glm: Metric Correlations Jrc Definitions Few Shot: [PNG](figures/correlations/original_glm/metric_correlations_jrc_definitions_few_shot.png) | [PDF](figures/correlations/original_glm/metric_correlations_jrc_definitions_few_shot.pdf)
- original_glm: Metric Correlations Jrc Definitions Zero Shot: [PNG](figures/correlations/original_glm/metric_correlations_jrc_definitions_zero_shot.png) | [PDF](figures/correlations/original_glm/metric_correlations_jrc_definitions_zero_shot.pdf)
- luna: Metric Correlations Selected Four All Datasets Few Shot: [PNG](figures/correlations/selected_four/luna/metric_correlations_selected_four_all_datasets_few_shot.png) | [PDF](figures/correlations/selected_four/luna/metric_correlations_selected_four_all_datasets_few_shot.pdf)
- luna: Metric Correlations Selected Four All Datasets Zero Shot: [PNG](figures/correlations/selected_four/luna/metric_correlations_selected_four_all_datasets_zero_shot.png) | [PDF](figures/correlations/selected_four/luna/metric_correlations_selected_four_all_datasets_zero_shot.pdf)
- original_glm: Metric Correlations Selected Four All Datasets Few Shot: [PNG](figures/correlations/selected_four/original_glm/metric_correlations_selected_four_all_datasets_few_shot.png) | [PDF](figures/correlations/selected_four/original_glm/metric_correlations_selected_four_all_datasets_few_shot.pdf)
- original_glm: Metric Correlations Selected Four All Datasets Zero Shot: [PNG](figures/correlations/selected_four/original_glm/metric_correlations_selected_four_all_datasets_zero_shot.png) | [PDF](figures/correlations/selected_four/original_glm/metric_correlations_selected_four_all_datasets_zero_shot.pdf)

### Translation Quality

- Learned Metric Comparison: [PNG](figures/translation_quality/learned_metric_comparison.png) | [PDF](figures/translation_quality/learned_metric_comparison.pdf)
- Translation Quality Google Patents: [PNG](figures/translation_quality/translation_quality_google_patents.png) | [PDF](figures/translation_quality/translation_quality_google_patents.pdf)
- Translation Quality Jrc Articles: [PNG](figures/translation_quality/translation_quality_jrc_articles.png) | [PDF](figures/translation_quality/translation_quality_jrc_articles.pdf)
- Translation Quality Jrc Definitions: [PNG](figures/translation_quality/translation_quality_jrc_definitions.png) | [PDF](figures/translation_quality/translation_quality_jrc_definitions.pdf)

### Terminology Metrics

#### All Three Term Types Together

- Terminology Coverage Luna: [PNG](figures/terminology/overview/terminology_coverage_luna.png) | [PDF](figures/terminology/overview/terminology_coverage_luna.pdf)
- Terminology Coverage Original Glm: [PNG](figures/terminology/overview/terminology_coverage_original_glm.png) | [PDF](figures/terminology/overview/terminology_coverage_original_glm.pdf)

#### All Terms

- Terminology Metrics All Terms Luna: [PNG](figures/terminology/all_terms/luna/terminology_metrics_all_terms_luna.png) | [PDF](figures/terminology/all_terms/luna/terminology_metrics_all_terms_luna.pdf)
- Terminology Metrics All Terms Original Glm: [PNG](figures/terminology/all_terms/original_glm/terminology_metrics_all_terms_original_glm.png) | [PDF](figures/terminology/all_terms/original_glm/terminology_metrics_all_terms_original_glm.pdf)

#### Externally Verified Terms

- Terminology Metrics Externally Verified Luna: [PNG](figures/terminology/externally_verified/luna/terminology_metrics_externally_verified_luna.png) | [PDF](figures/terminology/externally_verified/luna/terminology_metrics_externally_verified_luna.pdf)
- Terminology Metrics Externally Verified Original Glm: [PNG](figures/terminology/externally_verified/original_glm/terminology_metrics_externally_verified_original_glm.png) | [PDF](figures/terminology/externally_verified/original_glm/terminology_metrics_externally_verified_original_glm.pdf)

#### LLM-Enriched Terms (Final Refined Group)

- Terminology Metrics Llm Enriched Luna: [PNG](figures/terminology/llm_enriched/luna/terminology_metrics_llm_enriched_luna.png) | [PDF](figures/terminology/llm_enriched/luna/terminology_metrics_llm_enriched_luna.pdf)
- Terminology Metrics Llm Enriched Original Glm: [PNG](figures/terminology/llm_enriched/original_glm/terminology_metrics_llm_enriched_original_glm.png) | [PDF](figures/terminology/llm_enriched/original_glm/terminology_metrics_llm_enriched_original_glm.pdf)

### Quality-versus-Terminology Bubble Charts

#### All Terms

- luna: Quality Terminology Bubbles Google Patents Few Shot: [PNG](figures/bubbles/all_terms/luna/quality_terminology_bubbles_google_patents_few_shot.png) | [PDF](figures/bubbles/all_terms/luna/quality_terminology_bubbles_google_patents_few_shot.pdf)
- luna: Quality Terminology Bubbles Google Patents Zero Shot: [PNG](figures/bubbles/all_terms/luna/quality_terminology_bubbles_google_patents_zero_shot.png) | [PDF](figures/bubbles/all_terms/luna/quality_terminology_bubbles_google_patents_zero_shot.pdf)
- original_glm: Quality Terminology Bubbles Google Patents Few Shot: [PNG](figures/bubbles/all_terms/original_glm/quality_terminology_bubbles_google_patents_few_shot.png) | [PDF](figures/bubbles/all_terms/original_glm/quality_terminology_bubbles_google_patents_few_shot.pdf)
- original_glm: Quality Terminology Bubbles Google Patents Zero Shot: [PNG](figures/bubbles/all_terms/original_glm/quality_terminology_bubbles_google_patents_zero_shot.png) | [PDF](figures/bubbles/all_terms/original_glm/quality_terminology_bubbles_google_patents_zero_shot.pdf)

#### Externally Verified Terms

- luna: Quality Terminology Bubbles Google Patents Few Shot: [PNG](figures/bubbles/externally_verified/luna/quality_terminology_bubbles_google_patents_few_shot.png) | [PDF](figures/bubbles/externally_verified/luna/quality_terminology_bubbles_google_patents_few_shot.pdf)
- luna: Quality Terminology Bubbles Google Patents Zero Shot: [PNG](figures/bubbles/externally_verified/luna/quality_terminology_bubbles_google_patents_zero_shot.png) | [PDF](figures/bubbles/externally_verified/luna/quality_terminology_bubbles_google_patents_zero_shot.pdf)
- original_glm: Quality Terminology Bubbles Google Patents Few Shot: [PNG](figures/bubbles/externally_verified/original_glm/quality_terminology_bubbles_google_patents_few_shot.png) | [PDF](figures/bubbles/externally_verified/original_glm/quality_terminology_bubbles_google_patents_few_shot.pdf)
- original_glm: Quality Terminology Bubbles Google Patents Zero Shot: [PNG](figures/bubbles/externally_verified/original_glm/quality_terminology_bubbles_google_patents_zero_shot.png) | [PDF](figures/bubbles/externally_verified/original_glm/quality_terminology_bubbles_google_patents_zero_shot.pdf)

#### LLM-Enriched Terms (Final Refined Group)

- luna: Quality Terminology Bubbles Google Patents Few Shot: [PNG](figures/bubbles/llm_enriched/luna/quality_terminology_bubbles_google_patents_few_shot.png) | [PDF](figures/bubbles/llm_enriched/luna/quality_terminology_bubbles_google_patents_few_shot.pdf)
- luna: Quality Terminology Bubbles Google Patents Zero Shot: [PNG](figures/bubbles/llm_enriched/luna/quality_terminology_bubbles_google_patents_zero_shot.png) | [PDF](figures/bubbles/llm_enriched/luna/quality_terminology_bubbles_google_patents_zero_shot.pdf)
- original_glm: Quality Terminology Bubbles Google Patents Few Shot: [PNG](figures/bubbles/llm_enriched/original_glm/quality_terminology_bubbles_google_patents_few_shot.png) | [PDF](figures/bubbles/llm_enriched/original_glm/quality_terminology_bubbles_google_patents_few_shot.pdf)
- original_glm: Quality Terminology Bubbles Google Patents Zero Shot: [PNG](figures/bubbles/llm_enriched/original_glm/quality_terminology_bubbles_google_patents_zero_shot.png) | [PDF](figures/bubbles/llm_enriched/original_glm/quality_terminology_bubbles_google_patents_zero_shot.pdf)

### Distributions Across Language Directions

- luna: Performance Distributions Few Shot: [PNG](figures/distributions/luna/performance_distributions_few_shot.png) | [PDF](figures/distributions/luna/performance_distributions_few_shot.pdf)
- luna: Performance Distributions Zero Shot: [PNG](figures/distributions/luna/performance_distributions_zero_shot.png) | [PDF](figures/distributions/luna/performance_distributions_zero_shot.pdf)
- original_glm: Performance Distributions Few Shot: [PNG](figures/distributions/original_glm/performance_distributions_few_shot.png) | [PDF](figures/distributions/original_glm/performance_distributions_few_shot.pdf)
- original_glm: Performance Distributions Zero Shot: [PNG](figures/distributions/original_glm/performance_distributions_zero_shot.png) | [PDF](figures/distributions/original_glm/performance_distributions_zero_shot.pdf)

### Prompting Comparisons

- luna: Prompting Bars Terminology Google Patents: [PNG](figures/prompting/bars/luna/prompting_bars_terminology_google_patents.png) | [PDF](figures/prompting/bars/luna/prompting_bars_terminology_google_patents.pdf)
- luna: Prompting Bars Terminology Jrc Articles: [PNG](figures/prompting/bars/luna/prompting_bars_terminology_jrc_articles.png) | [PDF](figures/prompting/bars/luna/prompting_bars_terminology_jrc_articles.pdf)
- luna: Prompting Bars Terminology Jrc Definitions: [PNG](figures/prompting/bars/luna/prompting_bars_terminology_jrc_definitions.png) | [PDF](figures/prompting/bars/luna/prompting_bars_terminology_jrc_definitions.pdf)
- original_glm: Prompting Bars Terminology Google Patents: [PNG](figures/prompting/bars/original_glm/prompting_bars_terminology_google_patents.png) | [PDF](figures/prompting/bars/original_glm/prompting_bars_terminology_google_patents.pdf)
- original_glm: Prompting Bars Terminology Jrc Articles: [PNG](figures/prompting/bars/original_glm/prompting_bars_terminology_jrc_articles.png) | [PDF](figures/prompting/bars/original_glm/prompting_bars_terminology_jrc_articles.pdf)
- original_glm: Prompting Bars Terminology Jrc Definitions: [PNG](figures/prompting/bars/original_glm/prompting_bars_terminology_jrc_definitions.png) | [PDF](figures/prompting/bars/original_glm/prompting_bars_terminology_jrc_definitions.pdf)
- shared_general: Prompting Bars General Google Patents: [PNG](figures/prompting/bars/shared_general/prompting_bars_general_google_patents.png) | [PDF](figures/prompting/bars/shared_general/prompting_bars_general_google_patents.pdf)
- shared_general: Prompting Bars General Jrc Articles: [PNG](figures/prompting/bars/shared_general/prompting_bars_general_jrc_articles.png) | [PDF](figures/prompting/bars/shared_general/prompting_bars_general_jrc_articles.pdf)
- shared_general: Prompting Bars General Jrc Definitions: [PNG](figures/prompting/bars/shared_general/prompting_bars_general_jrc_definitions.png) | [PDF](figures/prompting/bars/shared_general/prompting_bars_general_jrc_definitions.pdf)
- Prompting Comet Difference: [PNG](figures/prompting/prompting_comet_difference.png) | [PDF](figures/prompting/prompting_comet_difference.pdf)

### Coverage

- Translation Coverage: [PNG](figures/coverage/translation_coverage.png) | [PDF](figures/coverage/translation_coverage.pdf)

## Four Least-Redundant Metric Columns

Selected from equal-dataset, model-level correlations across all three datasets, both prompts and both annotation views. Minimize the mean absolute Pearson and Spearman coefficients of all six pairs; require four different metrics and complete support in every context. Ties minimize the maximum absolute coefficient, then use column names. No metric-family coverage constraint.

- BLEU (not_applicable)
- COMETKiwi-QE (not_applicable)
- Sequence Similarity (not_applicable)
- XCOMET-XL (not_applicable)

Mean absolute correlation: 0.8542; maximum: 0.9983. Searched 2097 supported sets across 8 view/prompt/method contexts. These metrics remain correlated; this descriptive shortlist does not establish independence, metric validity, or coverage of every quality aspect. Existing rankings are unchanged.


## Interpretation

- Output-token bubble plots (outside the chosen collection) use recorded output tokens on x (millions), original ten-model mixed rank on y, and latency-proportional bubble area. Only models documented as thinking by default are plotted: GPT-6 Luna, Granite 4.2, Muse Glimmer, Nemotron 3.5 Lightning and Qwen3.8. This does not verify the benchmark run's thinking mode: in particular, a local GPT configuration disables thinking and is not confirmed as the downloaded run's config. Gemma defaults to thinking off; Tiny Aya lacks verified default-thinking evidence. Output totals are NOT verified thinking-inclusive counts; reported reasoning tokens are retained, never added again. Overall tokens sum six dataset/prompt strata, while latency averages their means equally. Ranks are not recomputed for the subset. Different tokenizers, workloads and deployments prevent a row-matched, equal-budget or hardware-controlled interpretation. All token plots share axis and area scales.
- All-dataset correlations first compute pair-specific shared-direction means inside each dataset, then average the three dataset means equally per model before correlating the ten model scores. They are NOT averages of correlation coefficients or pooled 30-observation correlations. Both prompts/views remain separate. Every dataset must have common scored support; otherwise the pair is NA. CSV fields retain per-dataset direction lists and total dataset-direction support counts. Single-dataset coefficients use the original method. Four-metric plots show the same global shortlist for every all-dataset context.
- Prompting bar figures show one panel per available metric with models on x and native scores on y: zero-shot on the left, few-shot on the right. All panels use zero-inclusive axes, without normalization or pooling across datasets. General metrics have one nine-panel figure per dataset; terminology figures separate both annotation views and show all/external/LLM-enriched groups in distinct panels. Scores reuse the tables' metric-specific common direction support across all models and both prompts. NA bars are labeled, not assigned zero; universally unavailable success-rate metrics are omitted. No row-paired or significance claims are implied.
- Chosen 03 uses reference estimated API cost on x, the existing ten-model mixed rank on y (rank 1 at the top), and bubble area proportional to observed latency (8 square points per second; larger means slower). Only verified priced models with measured latency are plotted; others remain in the bubble CSV as unpriced or missing, not zero cost. Rankings are not recomputed for the priced subset. Cost sums recorded token charges across strata; overall latency weights the six dataset/prompt means equally. Cost is hypothetical hosted-API token repricing without cache discount, while latency comes from the original local/API deployments, NOT the priced hosted endpoints. They are not a jointly measured price/speed trade-off, hardware-controlled benchmark or row-matched comparison. The CSV retains input/output cost, latency, bubble area and source references. All Chosen 03 figures share cost-axis and area scales.
- Chosen 02 plots measured mean translation-request latency against Chosen 01 mixed rank (rank 1 at the top). Original translation summary downloads are opt-in through `uv run --no-sync python scripts/download_evaluation_summaries.py --translation-timing`. Their source URLs and checksums are recorded separately. Overall latency weights the same six dataset/prompt strata equally; counts are not used as stratum weights. Missing, nonpositive or nonfinite latency is omitted, never replaced by zero. The axes describe observed deployments: hardware, hosted/API setup, concurrency, prompt/output lengths and timing coverage differ. Timing covers all recorded timed requests and is not proven row-matched to quality-scored support. This is not a hardware-normalized speed or cost comparison. No monetary cost was inferred from tokens, evaluator runtime or model size. Annotation views reuse the same timings.
- Chosen 01 ranks models by an equal-weight mean of three family mean ranks: semantic (BERTScore, BLEURT, COMET, COMETKiwi, XCOMET), lexical (BLEU, chrF, chrF++, sequence similarity), and terminology. Metric scores are ranked descending within each dataset/prompt with average ranks for ties. Terminology averages metric ranks within each term group, then equally averages all/external/LLM-enriched groups. All-NA metrics are omitted for every model, never assigned a zero rank; partial model support is rejected. Final rank ties share the minimum rank (1, 1, 3). Overall scorecards average six dataset/prompt family ranks equally; original metric cells show equal-stratum native-score means, not the basis for recomputing ranks. Rank columns and darker colors indicate better/lower ranks. The first column also shows the mixed mean rank in parentheses. Rankings depend on the selected model roster and chosen weights; they are descriptive, not evidence of significance. Exact metric values, metric ranks, direction supports and denominators are exported. Overall metric availability must be consistent across strata.
- Main tables/figures include ten current run identifiers. Three historical snapshots and the 60-row native sample remain in direction/coverage/provenance exports, not the main comparisons.
- For each metric/dataset/annotation-view/subset, intersect scored directions across all ten runs AND both prompting settings. Average those directions with equal weight. Actual direction lists and scored/applicable row counts are retained in the CSV files.
- BLEU/chrF/chrF++ cells average direction-level corpus scores; they are NOT pooled corpus scores. Learned/terminology cells average direction-level segment means. Do not mix these with sentence-weighted means.
- Shared directions do not prove identical evaluation examples. Counts vary; true row-matched comparisons, confidence intervals, bootstrap significance, and causal prompting claims cannot be obtained from these summaries alone.
- Terminology supports can differ by annotation source, subset, metric, and model. All/external/refined contrasts are descriptive, not a matched-row annotation ablation. NA means no common scored support, not zero accuracy. CSV files also retain available scored/applicable counts outside the shared-direction intersection.
- General metric values were checked for equality across all six annotation tracks before exporting them once. Annotation views are not translation-model conditions.
- All-metrics heatmaps annotate native-scale scores; color encodes within-metric model rank, not a common score scale. All nine general metrics are shown; terminology success-rate metrics are omitted when all displayed values are unavailable. Terminology includes all three term groups and both annotation views.
- Correlation matrices start from nine general and 15 terminology variables (five metrics times three groups), omitting all-NA success-rate variables. Pearson measures linear association; Spearman measures model-rank association with average ranks for ties. Each observation is one current model's direction-macro score, not a translation or language direction. Datasets, prompts and annotation views are kept separate. For each metric pair, directions are intersected across all ten models, both prompts, both metrics, and all three terminology groups for any terminology metric involved. Thus cross-group coefficients use shared direction support. Different metric pairs can use different supports; these pairwise matrices need not be positive semidefinite. Exact supports are exported. Cells show unchanged coefficients to three decimals; colors use the same signed fourth-root distance-to-endpoint scale on [-1, 1] across all figures to expand differences near +/-1. Colorbar ticks remain actual coefficients; color distances are nonlinear and do not imply effect sizes or significance. Supports and coefficients are unchanged. Constant/unavailable scores give NA. No p-values or significance claims; the models are not independent random samples and identical rows are not established.
- Score scales are unchanged. Coverage percentages use 0-100; learned scores use their native scales. XCOMET span counts are available in direction exports; no paid FSP-MQM judging was run. Learned-metric plot axes may be zoomed.
- Display names are shortened artifact/model labels. Exact stored model identifiers, source URLs and evaluation signatures are in model_provenance.csv; release/checkpoint identity has not been independently certified.
- Coverage counts describe stored translations. Reported expected/missing totals are preserved, including unknown native-sample totals, but are not an independent completeness audit.
- Terminology figures are split into all terms, externally verified terms, and LLM-enriched terms (the final `refined` group, not raw LLM candidates). Each type has separate GLM/Luna figures showing coverage, variant-aware coverage, and term BERTScore recall across the three datasets. Overview figures compare all term types. Source-conditioned terminology success rates remain available in the tables.
- Bubble charts use COMET on x, the selected term subset's target coverage on y, and area proportional to BLEU (36 square points per BLEU point; no min/max size remapping). All three metrics use the same direction intersection across ten models and both prompt settings within each view/subset. Supports may differ between view/subsets; metric-specific row denominators can still differ. All bubble charts share axis limits and size scaling; neither cost nor model size is implied.
- Distribution plots compare all three term subsets on directions jointly supported by every current model, both prompt settings, and both plotted metrics within each dataset/annotation view. A point is one direction's equal-model average, not one translation. Each category therefore has the same direction count. COMET can be identical across categories for the same direction because translations are unchanged.
- Shading is a descriptive 50% highest-density region of a 2D Gaussian KDE using Scott bandwidth, computed on the displayed grid. At least six nondegenerate direction points are required; otherwise only points are shown. Region-fit status and sample sizes are exported. These are not confidence regions or per-translation distributions; directions and model averages are not independent replicates. No uncertainty or significance claims follow from these plots.

## Reproduce

```powershell
uv run --no-sync python scripts/render_evaluation_results.py
```
