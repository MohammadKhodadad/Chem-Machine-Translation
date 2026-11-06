# Language Performance Analysis

## Method

Native heatmaps show metric-specific direction scores averaged equally across all models; rows are source languages and columns are target languages. Each panel's native color range is shared between zero-shot and few-shot.

Heatmaps omit languages with no supported cell in either role for that panel. Missing pairs between retained languages remain NA; ranking tables retain all observed languages and explicitly show missing overall coverage.

Balanced scores rank directions AND both prompts jointly within each model, dataset, view and metric. Higher native scores rank better; ties receive average ranks. Score = 100 * (pool size - rank) / (pool size - 1). These are relative rank percentiles, not accuracy percentages or native-score normalization.

Language-pair correlations compare native scores for different directions across models, with prompts separate. English-versus-French panels hold the source fixed.

Metrics are averaged equally within semantic and lexical families. Terminology metrics are averaged within each of the three annotation groups, then groups are averaged equally. The three families receive equal one-third weights, mirroring the balanced mixed-rank model scorecard. Universally unavailable metrics are omitted. Balanced panels use the intersection across every active component, model and both prompts; missing support is never replaced by zero.

Source/target rankings first average partner directions within each model, then models equally, prompts equally, and datasets equally. Overall language ranks require every dataset/prompt stratum; overall pair panels require the same directed pair in all three datasets. Tables include all observed languages and leave incomplete aggregates unranked. Direction and language ranks use competition ranks.

Partner-language sets differ, especially in the sparse patent grid. Rankings are descriptive of supported benchmark subsets, NOT partner-matched comparisons or intrinsic language difficulty. GLM/Luna supports differ and their ranks must not be compared as if populations were identical. Models, directions and datasets are not weighted by translation counts. Small direction samples, shared documents, reference overlap and few-shot exposure can affect results; no significance or leakage conclusion follows from these figures.

## Data and Tables

- [Translation from rankings](../../language_rankings_from.md) | [CSV](../../tables/language_rankings_from.csv)
- [Translation to rankings](../../language_rankings_to.md) | [CSV](../../tables/language_rankings_to.csv)
- [language_direction_model_scores](../../tables/language_direction_model_scores.csv)
- [language_rank_components](../../tables/language_rank_components.csv)
- [language_direction_support](../../tables/language_direction_support.csv)
- [language_pair_scores](../../tables/language_pair_scores.csv)

## Best Achieved Performance

[Best-model, best/median and hardest-pair plots](best_performance.md)

## Language Violins

[Pair, source-language and target-language violins](violins.md)

## Figures

- native_heatmaps/shared_general/native_google_patents_zero_shot: [PNG](native_heatmaps/shared_general/native_google_patents_zero_shot.png) | [PDF](native_heatmaps/shared_general/native_google_patents_zero_shot.pdf)
- native_heatmaps/shared_general/native_google_patents_few_shot: [PNG](native_heatmaps/shared_general/native_google_patents_few_shot.png) | [PDF](native_heatmaps/shared_general/native_google_patents_few_shot.pdf)
- native_heatmaps/shared_general/native_jrc_articles_zero_shot: [PNG](native_heatmaps/shared_general/native_jrc_articles_zero_shot.png) | [PDF](native_heatmaps/shared_general/native_jrc_articles_zero_shot.pdf)
- native_heatmaps/shared_general/native_jrc_articles_few_shot: [PNG](native_heatmaps/shared_general/native_jrc_articles_few_shot.png) | [PDF](native_heatmaps/shared_general/native_jrc_articles_few_shot.pdf)
- native_heatmaps/shared_general/native_jrc_definitions_zero_shot: [PNG](native_heatmaps/shared_general/native_jrc_definitions_zero_shot.png) | [PDF](native_heatmaps/shared_general/native_jrc_definitions_zero_shot.pdf)
- native_heatmaps/shared_general/native_jrc_definitions_few_shot: [PNG](native_heatmaps/shared_general/native_jrc_definitions_few_shot.png) | [PDF](native_heatmaps/shared_general/native_jrc_definitions_few_shot.pdf)
- native_heatmaps/original_glm/native_google_patents_zero_shot: [PNG](native_heatmaps/original_glm/native_google_patents_zero_shot.png) | [PDF](native_heatmaps/original_glm/native_google_patents_zero_shot.pdf)
- native_heatmaps/original_glm/native_google_patents_few_shot: [PNG](native_heatmaps/original_glm/native_google_patents_few_shot.png) | [PDF](native_heatmaps/original_glm/native_google_patents_few_shot.pdf)
- native_heatmaps/original_glm/native_jrc_articles_zero_shot: [PNG](native_heatmaps/original_glm/native_jrc_articles_zero_shot.png) | [PDF](native_heatmaps/original_glm/native_jrc_articles_zero_shot.pdf)
- native_heatmaps/original_glm/native_jrc_articles_few_shot: [PNG](native_heatmaps/original_glm/native_jrc_articles_few_shot.png) | [PDF](native_heatmaps/original_glm/native_jrc_articles_few_shot.pdf)
- native_heatmaps/original_glm/native_jrc_definitions_zero_shot: [PNG](native_heatmaps/original_glm/native_jrc_definitions_zero_shot.png) | [PDF](native_heatmaps/original_glm/native_jrc_definitions_zero_shot.pdf)
- native_heatmaps/original_glm/native_jrc_definitions_few_shot: [PNG](native_heatmaps/original_glm/native_jrc_definitions_few_shot.png) | [PDF](native_heatmaps/original_glm/native_jrc_definitions_few_shot.pdf)
- native_heatmaps/luna/native_google_patents_zero_shot: [PNG](native_heatmaps/luna/native_google_patents_zero_shot.png) | [PDF](native_heatmaps/luna/native_google_patents_zero_shot.pdf)
- native_heatmaps/luna/native_google_patents_few_shot: [PNG](native_heatmaps/luna/native_google_patents_few_shot.png) | [PDF](native_heatmaps/luna/native_google_patents_few_shot.pdf)
- native_heatmaps/luna/native_jrc_articles_zero_shot: [PNG](native_heatmaps/luna/native_jrc_articles_zero_shot.png) | [PDF](native_heatmaps/luna/native_jrc_articles_zero_shot.pdf)
- native_heatmaps/luna/native_jrc_articles_few_shot: [PNG](native_heatmaps/luna/native_jrc_articles_few_shot.png) | [PDF](native_heatmaps/luna/native_jrc_articles_few_shot.pdf)
- native_heatmaps/luna/native_jrc_definitions_zero_shot: [PNG](native_heatmaps/luna/native_jrc_definitions_zero_shot.png) | [PDF](native_heatmaps/luna/native_jrc_definitions_zero_shot.pdf)
- native_heatmaps/luna/native_jrc_definitions_few_shot: [PNG](native_heatmaps/luna/native_jrc_definitions_few_shot.png) | [PDF](native_heatmaps/luna/native_jrc_definitions_few_shot.pdf)
- balanced_heatmaps/original_glm/balanced_google_patents_zero_shot: [PNG](balanced_heatmaps/original_glm/balanced_google_patents_zero_shot.png) | [PDF](balanced_heatmaps/original_glm/balanced_google_patents_zero_shot.pdf)
- balanced_heatmaps/original_glm/balanced_google_patents_few_shot: [PNG](balanced_heatmaps/original_glm/balanced_google_patents_few_shot.png) | [PDF](balanced_heatmaps/original_glm/balanced_google_patents_few_shot.pdf)
- balanced_heatmaps/original_glm/balanced_jrc_articles_zero_shot: [PNG](balanced_heatmaps/original_glm/balanced_jrc_articles_zero_shot.png) | [PDF](balanced_heatmaps/original_glm/balanced_jrc_articles_zero_shot.pdf)
- balanced_heatmaps/original_glm/balanced_jrc_articles_few_shot: [PNG](balanced_heatmaps/original_glm/balanced_jrc_articles_few_shot.png) | [PDF](balanced_heatmaps/original_glm/balanced_jrc_articles_few_shot.pdf)
- balanced_heatmaps/original_glm/balanced_jrc_definitions_zero_shot: [PNG](balanced_heatmaps/original_glm/balanced_jrc_definitions_zero_shot.png) | [PDF](balanced_heatmaps/original_glm/balanced_jrc_definitions_zero_shot.pdf)
- balanced_heatmaps/original_glm/balanced_jrc_definitions_few_shot: [PNG](balanced_heatmaps/original_glm/balanced_jrc_definitions_few_shot.png) | [PDF](balanced_heatmaps/original_glm/balanced_jrc_definitions_few_shot.pdf)
- balanced_heatmaps/luna/balanced_google_patents_zero_shot: [PNG](balanced_heatmaps/luna/balanced_google_patents_zero_shot.png) | [PDF](balanced_heatmaps/luna/balanced_google_patents_zero_shot.pdf)
- balanced_heatmaps/luna/balanced_google_patents_few_shot: [PNG](balanced_heatmaps/luna/balanced_google_patents_few_shot.png) | [PDF](balanced_heatmaps/luna/balanced_google_patents_few_shot.pdf)
- balanced_heatmaps/luna/balanced_jrc_articles_zero_shot: [PNG](balanced_heatmaps/luna/balanced_jrc_articles_zero_shot.png) | [PDF](balanced_heatmaps/luna/balanced_jrc_articles_zero_shot.pdf)
- balanced_heatmaps/luna/balanced_jrc_articles_few_shot: [PNG](balanced_heatmaps/luna/balanced_jrc_articles_few_shot.png) | [PDF](balanced_heatmaps/luna/balanced_jrc_articles_few_shot.pdf)
- balanced_heatmaps/luna/balanced_jrc_definitions_zero_shot: [PNG](balanced_heatmaps/luna/balanced_jrc_definitions_zero_shot.png) | [PDF](balanced_heatmaps/luna/balanced_jrc_definitions_zero_shot.pdf)
- balanced_heatmaps/luna/balanced_jrc_definitions_few_shot: [PNG](balanced_heatmaps/luna/balanced_jrc_definitions_few_shot.png) | [PDF](balanced_heatmaps/luna/balanced_jrc_definitions_few_shot.pdf)
- balanced_heatmaps/original_glm/balanced_google_patents_both_prompts: [PNG](balanced_heatmaps/original_glm/balanced_google_patents_both_prompts.png) | [PDF](balanced_heatmaps/original_glm/balanced_google_patents_both_prompts.pdf)
- balanced_heatmaps/original_glm/balanced_jrc_articles_both_prompts: [PNG](balanced_heatmaps/original_glm/balanced_jrc_articles_both_prompts.png) | [PDF](balanced_heatmaps/original_glm/balanced_jrc_articles_both_prompts.pdf)
- balanced_heatmaps/original_glm/balanced_jrc_definitions_both_prompts: [PNG](balanced_heatmaps/original_glm/balanced_jrc_definitions_both_prompts.png) | [PDF](balanced_heatmaps/original_glm/balanced_jrc_definitions_both_prompts.pdf)
- balanced_heatmaps/luna/balanced_google_patents_both_prompts: [PNG](balanced_heatmaps/luna/balanced_google_patents_both_prompts.png) | [PDF](balanced_heatmaps/luna/balanced_google_patents_both_prompts.pdf)
- balanced_heatmaps/luna/balanced_jrc_articles_both_prompts: [PNG](balanced_heatmaps/luna/balanced_jrc_articles_both_prompts.png) | [PDF](balanced_heatmaps/luna/balanced_jrc_articles_both_prompts.pdf)
- balanced_heatmaps/luna/balanced_jrc_definitions_both_prompts: [PNG](balanced_heatmaps/luna/balanced_jrc_definitions_both_prompts.png) | [PDF](balanced_heatmaps/luna/balanced_jrc_definitions_both_prompts.pdf)
- balanced_heatmaps/original_glm/balanced_all_datasets_zero_shot: [PNG](balanced_heatmaps/original_glm/balanced_all_datasets_zero_shot.png) | [PDF](balanced_heatmaps/original_glm/balanced_all_datasets_zero_shot.pdf)
- balanced_heatmaps/original_glm/balanced_all_datasets_few_shot: [PNG](balanced_heatmaps/original_glm/balanced_all_datasets_few_shot.png) | [PDF](balanced_heatmaps/original_glm/balanced_all_datasets_few_shot.pdf)
- balanced_heatmaps/luna/balanced_all_datasets_zero_shot: [PNG](balanced_heatmaps/luna/balanced_all_datasets_zero_shot.png) | [PDF](balanced_heatmaps/luna/balanced_all_datasets_zero_shot.pdf)
- balanced_heatmaps/luna/balanced_all_datasets_few_shot: [PNG](balanced_heatmaps/luna/balanced_all_datasets_few_shot.png) | [PDF](balanced_heatmaps/luna/balanced_all_datasets_few_shot.pdf)
- balanced_heatmaps/original_glm/balanced_all_datasets_both_prompts: [PNG](balanced_heatmaps/original_glm/balanced_all_datasets_both_prompts.png) | [PDF](balanced_heatmaps/original_glm/balanced_all_datasets_both_prompts.pdf)
- balanced_heatmaps/luna/balanced_all_datasets_both_prompts: [PNG](balanced_heatmaps/luna/balanced_all_datasets_both_prompts.png) | [PDF](balanced_heatmaps/luna/balanced_all_datasets_both_prompts.pdf)

## Pair Correlations

[Language-pair correlations and English-versus-French scatter plots](pair_correlations.md)

## Language Correlations

[Language correlations: to-to, from-from and from-to](correlations.md)

## Language Correlations

[Combined language correlations and model scatter plots](correlations_combined.md)

## Balanced Language Rankings

[Balanced language median/best-model scorecards](../../tables/language_rankings/README.md)
