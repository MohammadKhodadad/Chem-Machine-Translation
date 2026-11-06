# Best Achieved Language-Pair Performance

Three views: best-model heatmaps with winner IDs; best versus median heatmaps; hardest-pair plots showing every model, sorted by the whole-direction maximum.

COMET and chrF++ use the shared general scores. Variant-aware terminology coverage has separate GLM/Luna views and all/external/LLM-enriched groups. All models and both prompts must have each direction. Datasets and prompt settings are never pooled. Model IDs follow the same sorted model order across all figures.

Every maximum comes from one complete model-direction evaluation, not an oracle choosing different models per translation. A model can win different pairs or metrics. Exact ties retain every winner in the CSV; heatmaps show the lowest winning ID with *. Best observed scores are optimistically selected on the test set, not an independently validated deployment policy. Low scores indicate difficulty on these benchmark rows, not intrinsic language difficulty. Consult scored-row support before interpreting near-perfect small-sample results.

Best and median use identical color limits, shared across prompts within each dataset/view/group/metric. Unsupported languages are omitted from the grid; missing pairs remain NA. Different metrics/groups can have different support.

- [Best/median scores, winning models, ties and support](../../tables/best_language_pairs.csv)
- [All model-direction points](../../tables/best_language_model_points.csv)

## Figures

- best_models/shared_general/best_google_patents_zero_shot: [PNG](best_models/shared_general/best_google_patents_zero_shot.png) | [PDF](best_models/shared_general/best_google_patents_zero_shot.pdf)
- best_vs_median/shared_general/comparison_google_patents_zero_shot: [PNG](best_vs_median/shared_general/comparison_google_patents_zero_shot.png) | [PDF](best_vs_median/shared_general/comparison_google_patents_zero_shot.pdf)
- hardest_pairs/shared_general/hardest_google_patents_zero_shot: [PNG](hardest_pairs/shared_general/hardest_google_patents_zero_shot.png) | [PDF](hardest_pairs/shared_general/hardest_google_patents_zero_shot.pdf)
- best_models/shared_general/best_google_patents_few_shot: [PNG](best_models/shared_general/best_google_patents_few_shot.png) | [PDF](best_models/shared_general/best_google_patents_few_shot.pdf)
- best_vs_median/shared_general/comparison_google_patents_few_shot: [PNG](best_vs_median/shared_general/comparison_google_patents_few_shot.png) | [PDF](best_vs_median/shared_general/comparison_google_patents_few_shot.pdf)
- hardest_pairs/shared_general/hardest_google_patents_few_shot: [PNG](hardest_pairs/shared_general/hardest_google_patents_few_shot.png) | [PDF](hardest_pairs/shared_general/hardest_google_patents_few_shot.pdf)
- best_models/shared_general/best_jrc_articles_zero_shot: [PNG](best_models/shared_general/best_jrc_articles_zero_shot.png) | [PDF](best_models/shared_general/best_jrc_articles_zero_shot.pdf)
- best_vs_median/shared_general/comparison_jrc_articles_zero_shot: [PNG](best_vs_median/shared_general/comparison_jrc_articles_zero_shot.png) | [PDF](best_vs_median/shared_general/comparison_jrc_articles_zero_shot.pdf)
- hardest_pairs/shared_general/hardest_jrc_articles_zero_shot: [PNG](hardest_pairs/shared_general/hardest_jrc_articles_zero_shot.png) | [PDF](hardest_pairs/shared_general/hardest_jrc_articles_zero_shot.pdf)
- best_models/shared_general/best_jrc_articles_few_shot: [PNG](best_models/shared_general/best_jrc_articles_few_shot.png) | [PDF](best_models/shared_general/best_jrc_articles_few_shot.pdf)
- best_vs_median/shared_general/comparison_jrc_articles_few_shot: [PNG](best_vs_median/shared_general/comparison_jrc_articles_few_shot.png) | [PDF](best_vs_median/shared_general/comparison_jrc_articles_few_shot.pdf)
- hardest_pairs/shared_general/hardest_jrc_articles_few_shot: [PNG](hardest_pairs/shared_general/hardest_jrc_articles_few_shot.png) | [PDF](hardest_pairs/shared_general/hardest_jrc_articles_few_shot.pdf)
- best_models/shared_general/best_jrc_definitions_zero_shot: [PNG](best_models/shared_general/best_jrc_definitions_zero_shot.png) | [PDF](best_models/shared_general/best_jrc_definitions_zero_shot.pdf)
- best_vs_median/shared_general/comparison_jrc_definitions_zero_shot: [PNG](best_vs_median/shared_general/comparison_jrc_definitions_zero_shot.png) | [PDF](best_vs_median/shared_general/comparison_jrc_definitions_zero_shot.pdf)
- hardest_pairs/shared_general/hardest_jrc_definitions_zero_shot: [PNG](hardest_pairs/shared_general/hardest_jrc_definitions_zero_shot.png) | [PDF](hardest_pairs/shared_general/hardest_jrc_definitions_zero_shot.pdf)
- best_models/shared_general/best_jrc_definitions_few_shot: [PNG](best_models/shared_general/best_jrc_definitions_few_shot.png) | [PDF](best_models/shared_general/best_jrc_definitions_few_shot.pdf)
- best_vs_median/shared_general/comparison_jrc_definitions_few_shot: [PNG](best_vs_median/shared_general/comparison_jrc_definitions_few_shot.png) | [PDF](best_vs_median/shared_general/comparison_jrc_definitions_few_shot.pdf)
- hardest_pairs/shared_general/hardest_jrc_definitions_few_shot: [PNG](hardest_pairs/shared_general/hardest_jrc_definitions_few_shot.png) | [PDF](hardest_pairs/shared_general/hardest_jrc_definitions_few_shot.pdf)
- best_models/original_glm/best_google_patents_zero_shot: [PNG](best_models/original_glm/best_google_patents_zero_shot.png) | [PDF](best_models/original_glm/best_google_patents_zero_shot.pdf)
- best_vs_median/original_glm/comparison_google_patents_zero_shot: [PNG](best_vs_median/original_glm/comparison_google_patents_zero_shot.png) | [PDF](best_vs_median/original_glm/comparison_google_patents_zero_shot.pdf)
- hardest_pairs/original_glm/hardest_google_patents_zero_shot: [PNG](hardest_pairs/original_glm/hardest_google_patents_zero_shot.png) | [PDF](hardest_pairs/original_glm/hardest_google_patents_zero_shot.pdf)
- best_models/original_glm/best_google_patents_few_shot: [PNG](best_models/original_glm/best_google_patents_few_shot.png) | [PDF](best_models/original_glm/best_google_patents_few_shot.pdf)
- best_vs_median/original_glm/comparison_google_patents_few_shot: [PNG](best_vs_median/original_glm/comparison_google_patents_few_shot.png) | [PDF](best_vs_median/original_glm/comparison_google_patents_few_shot.pdf)
- hardest_pairs/original_glm/hardest_google_patents_few_shot: [PNG](hardest_pairs/original_glm/hardest_google_patents_few_shot.png) | [PDF](hardest_pairs/original_glm/hardest_google_patents_few_shot.pdf)
- best_models/original_glm/best_jrc_articles_zero_shot: [PNG](best_models/original_glm/best_jrc_articles_zero_shot.png) | [PDF](best_models/original_glm/best_jrc_articles_zero_shot.pdf)
- best_vs_median/original_glm/comparison_jrc_articles_zero_shot: [PNG](best_vs_median/original_glm/comparison_jrc_articles_zero_shot.png) | [PDF](best_vs_median/original_glm/comparison_jrc_articles_zero_shot.pdf)
- hardest_pairs/original_glm/hardest_jrc_articles_zero_shot: [PNG](hardest_pairs/original_glm/hardest_jrc_articles_zero_shot.png) | [PDF](hardest_pairs/original_glm/hardest_jrc_articles_zero_shot.pdf)
- best_models/original_glm/best_jrc_articles_few_shot: [PNG](best_models/original_glm/best_jrc_articles_few_shot.png) | [PDF](best_models/original_glm/best_jrc_articles_few_shot.pdf)
- best_vs_median/original_glm/comparison_jrc_articles_few_shot: [PNG](best_vs_median/original_glm/comparison_jrc_articles_few_shot.png) | [PDF](best_vs_median/original_glm/comparison_jrc_articles_few_shot.pdf)
- hardest_pairs/original_glm/hardest_jrc_articles_few_shot: [PNG](hardest_pairs/original_glm/hardest_jrc_articles_few_shot.png) | [PDF](hardest_pairs/original_glm/hardest_jrc_articles_few_shot.pdf)
- best_models/original_glm/best_jrc_definitions_zero_shot: [PNG](best_models/original_glm/best_jrc_definitions_zero_shot.png) | [PDF](best_models/original_glm/best_jrc_definitions_zero_shot.pdf)
- best_vs_median/original_glm/comparison_jrc_definitions_zero_shot: [PNG](best_vs_median/original_glm/comparison_jrc_definitions_zero_shot.png) | [PDF](best_vs_median/original_glm/comparison_jrc_definitions_zero_shot.pdf)
- hardest_pairs/original_glm/hardest_jrc_definitions_zero_shot: [PNG](hardest_pairs/original_glm/hardest_jrc_definitions_zero_shot.png) | [PDF](hardest_pairs/original_glm/hardest_jrc_definitions_zero_shot.pdf)
- best_models/original_glm/best_jrc_definitions_few_shot: [PNG](best_models/original_glm/best_jrc_definitions_few_shot.png) | [PDF](best_models/original_glm/best_jrc_definitions_few_shot.pdf)
- best_vs_median/original_glm/comparison_jrc_definitions_few_shot: [PNG](best_vs_median/original_glm/comparison_jrc_definitions_few_shot.png) | [PDF](best_vs_median/original_glm/comparison_jrc_definitions_few_shot.pdf)
- hardest_pairs/original_glm/hardest_jrc_definitions_few_shot: [PNG](hardest_pairs/original_glm/hardest_jrc_definitions_few_shot.png) | [PDF](hardest_pairs/original_glm/hardest_jrc_definitions_few_shot.pdf)
- best_models/luna/best_google_patents_zero_shot: [PNG](best_models/luna/best_google_patents_zero_shot.png) | [PDF](best_models/luna/best_google_patents_zero_shot.pdf)
- best_vs_median/luna/comparison_google_patents_zero_shot: [PNG](best_vs_median/luna/comparison_google_patents_zero_shot.png) | [PDF](best_vs_median/luna/comparison_google_patents_zero_shot.pdf)
- hardest_pairs/luna/hardest_google_patents_zero_shot: [PNG](hardest_pairs/luna/hardest_google_patents_zero_shot.png) | [PDF](hardest_pairs/luna/hardest_google_patents_zero_shot.pdf)
- best_models/luna/best_google_patents_few_shot: [PNG](best_models/luna/best_google_patents_few_shot.png) | [PDF](best_models/luna/best_google_patents_few_shot.pdf)
- best_vs_median/luna/comparison_google_patents_few_shot: [PNG](best_vs_median/luna/comparison_google_patents_few_shot.png) | [PDF](best_vs_median/luna/comparison_google_patents_few_shot.pdf)
- hardest_pairs/luna/hardest_google_patents_few_shot: [PNG](hardest_pairs/luna/hardest_google_patents_few_shot.png) | [PDF](hardest_pairs/luna/hardest_google_patents_few_shot.pdf)
- best_models/luna/best_jrc_articles_zero_shot: [PNG](best_models/luna/best_jrc_articles_zero_shot.png) | [PDF](best_models/luna/best_jrc_articles_zero_shot.pdf)
- best_vs_median/luna/comparison_jrc_articles_zero_shot: [PNG](best_vs_median/luna/comparison_jrc_articles_zero_shot.png) | [PDF](best_vs_median/luna/comparison_jrc_articles_zero_shot.pdf)
- hardest_pairs/luna/hardest_jrc_articles_zero_shot: [PNG](hardest_pairs/luna/hardest_jrc_articles_zero_shot.png) | [PDF](hardest_pairs/luna/hardest_jrc_articles_zero_shot.pdf)
- best_models/luna/best_jrc_articles_few_shot: [PNG](best_models/luna/best_jrc_articles_few_shot.png) | [PDF](best_models/luna/best_jrc_articles_few_shot.pdf)
- best_vs_median/luna/comparison_jrc_articles_few_shot: [PNG](best_vs_median/luna/comparison_jrc_articles_few_shot.png) | [PDF](best_vs_median/luna/comparison_jrc_articles_few_shot.pdf)
- hardest_pairs/luna/hardest_jrc_articles_few_shot: [PNG](hardest_pairs/luna/hardest_jrc_articles_few_shot.png) | [PDF](hardest_pairs/luna/hardest_jrc_articles_few_shot.pdf)
- best_models/luna/best_jrc_definitions_zero_shot: [PNG](best_models/luna/best_jrc_definitions_zero_shot.png) | [PDF](best_models/luna/best_jrc_definitions_zero_shot.pdf)
- best_vs_median/luna/comparison_jrc_definitions_zero_shot: [PNG](best_vs_median/luna/comparison_jrc_definitions_zero_shot.png) | [PDF](best_vs_median/luna/comparison_jrc_definitions_zero_shot.pdf)
- hardest_pairs/luna/hardest_jrc_definitions_zero_shot: [PNG](hardest_pairs/luna/hardest_jrc_definitions_zero_shot.png) | [PDF](hardest_pairs/luna/hardest_jrc_definitions_zero_shot.pdf)
- best_models/luna/best_jrc_definitions_few_shot: [PNG](best_models/luna/best_jrc_definitions_few_shot.png) | [PDF](best_models/luna/best_jrc_definitions_few_shot.pdf)
- best_vs_median/luna/comparison_jrc_definitions_few_shot: [PNG](best_vs_median/luna/comparison_jrc_definitions_few_shot.png) | [PDF](best_vs_median/luna/comparison_jrc_definitions_few_shot.pdf)
- hardest_pairs/luna/hardest_jrc_definitions_few_shot: [PNG](hardest_pairs/luna/hardest_jrc_definitions_few_shot.png) | [PDF](hardest_pairs/luna/hardest_jrc_definitions_few_shot.pdf)
