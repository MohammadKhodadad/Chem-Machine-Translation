# Figure 3: Language-Level Prompting Changes

Compact heatmaps: X = language, Y = metric; one panel per dataset. Each cell shows only relative percentage change: 100 * (few - zero) / zero, computed from the equal-model mean scores, not the mean of per-model ratios. Green = gain, red = loss, white = zero, grey = NA. Missing comparisons and nonpositive zero-shot baselines are NA; percentage change is misleading there. All panels share one symmetric percentage-change color scale across datasets, metrics, annotation views, groups and roles. Coverage changes are relative percentages here, not percentage points. Percentages describe metric scores, not translation quality. Raw scores and absolute deltas remain in the CSV. Rows contain COMET, variant-aware target-term coverage and term BERTScore recall. Datasets, From/To roles, annotation views and term groups remain separate.

Within each model, average identical supported partner directions for both prompts; then average models equally. These are averages across the evaluated models, not guarantees for every model. All selected models and both prompts are required for each direction. Differing row counts are flagged with * and exported, not silently excluded. Equal counts do not establish matched rows. No significance inference.

[Language scores and support](../../../tables/language_prompting_scores.csv) | [Per-model partner means](../../../tables/language_prompting_model_means.csv)

- original_glm/from_all_terms: [PNG](original_glm/from_all_terms.png) | [PDF](original_glm/from_all_terms.pdf)
- original_glm/from_externally_verified: [PNG](original_glm/from_externally_verified.png) | [PDF](original_glm/from_externally_verified.pdf)
- original_glm/from_llm_enriched: [PNG](original_glm/from_llm_enriched.png) | [PDF](original_glm/from_llm_enriched.pdf)
- original_glm/to_all_terms: [PNG](original_glm/to_all_terms.png) | [PDF](original_glm/to_all_terms.pdf)
- original_glm/to_externally_verified: [PNG](original_glm/to_externally_verified.png) | [PDF](original_glm/to_externally_verified.pdf)
- original_glm/to_llm_enriched: [PNG](original_glm/to_llm_enriched.png) | [PDF](original_glm/to_llm_enriched.pdf)
- luna/from_all_terms: [PNG](luna/from_all_terms.png) | [PDF](luna/from_all_terms.pdf)
- luna/from_externally_verified: [PNG](luna/from_externally_verified.png) | [PDF](luna/from_externally_verified.pdf)
- luna/from_llm_enriched: [PNG](luna/from_llm_enriched.png) | [PDF](luna/from_llm_enriched.pdf)
- luna/to_all_terms: [PNG](luna/to_all_terms.png) | [PDF](luna/to_all_terms.pdf)
- luna/to_externally_verified: [PNG](luna/to_externally_verified.png) | [PDF](luna/to_externally_verified.pdf)
- luna/to_llm_enriched: [PNG](luna/to_llm_enriched.png) | [PDF](luna/to_llm_enriched.pdf)
