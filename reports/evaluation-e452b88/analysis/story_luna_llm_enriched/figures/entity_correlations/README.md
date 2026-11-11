# Language and Model Correlations

Matrices keep metric, dataset and From/To role separate. Each direction requires finite scores for all selected models and both prompts. Within each model, average its supported partner directions for each language, then average the two prompts equally. New terminology matrices use Luna LLM-enriched terms only.

Language-to-language correlations use one observation per model. Model-to-model correlations use one observation per supported source/target language. Each model uses the same directions for a given language, but partner sets can differ between languages; those aggregated observations can be dependent. No cross-metric scale pooling, dataset pooling, causal claims or significance inference. Constant vectors and fewer than three observations are NA, including constant diagonal entries. Scores/support vectors, row-count flags and unknown counts are exported; equal counts do not establish matched rows.

[Coefficients and exact vectors](../../tables/entity_correlations/correlations.csv) | [Native model-language means and support](../../tables/entity_correlations/language_model_scores.csv)

- languages/from_comet: [PNG](languages/from_comet.png) | [PDF](languages/from_comet.pdf)
- languages/from_chrf2++: [PNG](languages/from_chrf2++.png) | [PDF](languages/from_chrf2++.pdf)
- languages/from_variant_aware_target_term_coverage: [PNG](languages/from_variant_aware_target_term_coverage.png) | [PDF](languages/from_variant_aware_target_term_coverage.pdf)
- languages/from_term_bertscore_recall: [PNG](languages/from_term_bertscore_recall.png) | [PDF](languages/from_term_bertscore_recall.pdf)
- languages/to_comet: [PNG](languages/to_comet.png) | [PDF](languages/to_comet.pdf)
- languages/to_chrf2++: [PNG](languages/to_chrf2++.png) | [PDF](languages/to_chrf2++.pdf)
- languages/to_variant_aware_target_term_coverage: [PNG](languages/to_variant_aware_target_term_coverage.png) | [PDF](languages/to_variant_aware_target_term_coverage.pdf)
- languages/to_term_bertscore_recall: [PNG](languages/to_term_bertscore_recall.png) | [PDF](languages/to_term_bertscore_recall.pdf)
- models/from_comet: [PNG](models/from_comet.png) | [PDF](models/from_comet.pdf)
- models/from_chrf2++: [PNG](models/from_chrf2++.png) | [PDF](models/from_chrf2++.pdf)
- models/from_variant_aware_target_term_coverage: [PNG](models/from_variant_aware_target_term_coverage.png) | [PDF](models/from_variant_aware_target_term_coverage.pdf)
- models/from_term_bertscore_recall: [PNG](models/from_term_bertscore_recall.png) | [PDF](models/from_term_bertscore_recall.pdf)
- models/to_comet: [PNG](models/to_comet.png) | [PDF](models/to_comet.pdf)
- models/to_chrf2++: [PNG](models/to_chrf2++.png) | [PDF](models/to_chrf2++.pdf)
- models/to_variant_aware_target_term_coverage: [PNG](models/to_variant_aware_target_term_coverage.png) | [PDF](models/to_variant_aware_target_term_coverage.pdf)
- models/to_term_bertscore_recall: [PNG](models/to_term_bertscore_recall.png) | [PDF](models/to_term_bertscore_recall.pdf)
