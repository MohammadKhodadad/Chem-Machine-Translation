# Language-Pair Correlations

Each observation is one retained model. Native scores for two directed language pairs are correlated across the same models using Pearson and Spearman. Zero-shot and few-shot are separate, as are datasets, metrics and terminology groups. General metrics share the annotation-independent translation scores.

Heatmaps cover every supported pair of directions for COMET, chrF++ and variant-aware coverage. English-versus-French COMET scatter panels hold the source language fixed: for example German -> English versus German -> French.

Scores are native model-direction aggregates, not within-model language percentiles. All models and both prompts must have complete direction scores. Every model has equal weight; translation counts do not weight correlations. Constant vectors or fewer than three models produce NA, not zero. Exact model vectors are exported in [language_pair_correlations.csv](../../tables/language_pair_correlations.csv).

A positive correlation can reflect overall model strength rather than a specific language relationship. Models are not independent random samples, direction rows are not matched translations, and no p-values, significance or causal claims are made.

## Figures

- model_pairs/luna/pair_correlations_google_patents_few_shot: [PNG](model_pairs/luna/pair_correlations_google_patents_few_shot.png) | [PDF](model_pairs/luna/pair_correlations_google_patents_few_shot.pdf)
- model_pairs/luna/pair_correlations_google_patents_zero_shot: [PNG](model_pairs/luna/pair_correlations_google_patents_zero_shot.png) | [PDF](model_pairs/luna/pair_correlations_google_patents_zero_shot.pdf)
- model_pairs/luna/pair_correlations_jrc_articles_few_shot: [PNG](model_pairs/luna/pair_correlations_jrc_articles_few_shot.png) | [PDF](model_pairs/luna/pair_correlations_jrc_articles_few_shot.pdf)
- model_pairs/luna/pair_correlations_jrc_articles_zero_shot: [PNG](model_pairs/luna/pair_correlations_jrc_articles_zero_shot.png) | [PDF](model_pairs/luna/pair_correlations_jrc_articles_zero_shot.pdf)
- model_pairs/luna/pair_correlations_jrc_definitions_few_shot: [PNG](model_pairs/luna/pair_correlations_jrc_definitions_few_shot.png) | [PDF](model_pairs/luna/pair_correlations_jrc_definitions_few_shot.pdf)
- model_pairs/luna/pair_correlations_jrc_definitions_zero_shot: [PNG](model_pairs/luna/pair_correlations_jrc_definitions_zero_shot.png) | [PDF](model_pairs/luna/pair_correlations_jrc_definitions_zero_shot.pdf)
- model_pairs/original_glm/pair_correlations_google_patents_few_shot: [PNG](model_pairs/original_glm/pair_correlations_google_patents_few_shot.png) | [PDF](model_pairs/original_glm/pair_correlations_google_patents_few_shot.pdf)
- model_pairs/original_glm/pair_correlations_google_patents_zero_shot: [PNG](model_pairs/original_glm/pair_correlations_google_patents_zero_shot.png) | [PDF](model_pairs/original_glm/pair_correlations_google_patents_zero_shot.pdf)
- model_pairs/original_glm/pair_correlations_jrc_articles_few_shot: [PNG](model_pairs/original_glm/pair_correlations_jrc_articles_few_shot.png) | [PDF](model_pairs/original_glm/pair_correlations_jrc_articles_few_shot.pdf)
- model_pairs/original_glm/pair_correlations_jrc_articles_zero_shot: [PNG](model_pairs/original_glm/pair_correlations_jrc_articles_zero_shot.png) | [PDF](model_pairs/original_glm/pair_correlations_jrc_articles_zero_shot.pdf)
- model_pairs/original_glm/pair_correlations_jrc_definitions_few_shot: [PNG](model_pairs/original_glm/pair_correlations_jrc_definitions_few_shot.png) | [PDF](model_pairs/original_glm/pair_correlations_jrc_definitions_few_shot.pdf)
- model_pairs/original_glm/pair_correlations_jrc_definitions_zero_shot: [PNG](model_pairs/original_glm/pair_correlations_jrc_definitions_zero_shot.png) | [PDF](model_pairs/original_glm/pair_correlations_jrc_definitions_zero_shot.pdf)
- model_pairs/shared_general/pair_correlations_google_patents_few_shot: [PNG](model_pairs/shared_general/pair_correlations_google_patents_few_shot.png) | [PDF](model_pairs/shared_general/pair_correlations_google_patents_few_shot.pdf)
- model_pairs/shared_general/english_vs_french_google_patents_few_shot: [PNG](model_pairs/shared_general/english_vs_french_google_patents_few_shot.png) | [PDF](model_pairs/shared_general/english_vs_french_google_patents_few_shot.pdf)
- model_pairs/shared_general/pair_correlations_google_patents_zero_shot: [PNG](model_pairs/shared_general/pair_correlations_google_patents_zero_shot.png) | [PDF](model_pairs/shared_general/pair_correlations_google_patents_zero_shot.pdf)
- model_pairs/shared_general/english_vs_french_google_patents_zero_shot: [PNG](model_pairs/shared_general/english_vs_french_google_patents_zero_shot.png) | [PDF](model_pairs/shared_general/english_vs_french_google_patents_zero_shot.pdf)
- model_pairs/shared_general/pair_correlations_jrc_articles_few_shot: [PNG](model_pairs/shared_general/pair_correlations_jrc_articles_few_shot.png) | [PDF](model_pairs/shared_general/pair_correlations_jrc_articles_few_shot.pdf)
- model_pairs/shared_general/english_vs_french_jrc_articles_few_shot: [PNG](model_pairs/shared_general/english_vs_french_jrc_articles_few_shot.png) | [PDF](model_pairs/shared_general/english_vs_french_jrc_articles_few_shot.pdf)
- model_pairs/shared_general/pair_correlations_jrc_articles_zero_shot: [PNG](model_pairs/shared_general/pair_correlations_jrc_articles_zero_shot.png) | [PDF](model_pairs/shared_general/pair_correlations_jrc_articles_zero_shot.pdf)
- model_pairs/shared_general/english_vs_french_jrc_articles_zero_shot: [PNG](model_pairs/shared_general/english_vs_french_jrc_articles_zero_shot.png) | [PDF](model_pairs/shared_general/english_vs_french_jrc_articles_zero_shot.pdf)
- model_pairs/shared_general/pair_correlations_jrc_definitions_few_shot: [PNG](model_pairs/shared_general/pair_correlations_jrc_definitions_few_shot.png) | [PDF](model_pairs/shared_general/pair_correlations_jrc_definitions_few_shot.pdf)
- model_pairs/shared_general/english_vs_french_jrc_definitions_few_shot: [PNG](model_pairs/shared_general/english_vs_french_jrc_definitions_few_shot.png) | [PDF](model_pairs/shared_general/english_vs_french_jrc_definitions_few_shot.pdf)
- model_pairs/shared_general/pair_correlations_jrc_definitions_zero_shot: [PNG](model_pairs/shared_general/pair_correlations_jrc_definitions_zero_shot.png) | [PDF](model_pairs/shared_general/pair_correlations_jrc_definitions_zero_shot.pdf)
- model_pairs/shared_general/english_vs_french_jrc_definitions_zero_shot: [PNG](model_pairs/shared_general/english_vs_french_jrc_definitions_zero_shot.png) | [PDF](model_pairs/shared_general/english_vs_french_jrc_definitions_zero_shot.pdf)
