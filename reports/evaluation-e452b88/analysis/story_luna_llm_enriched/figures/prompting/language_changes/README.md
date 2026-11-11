# Figure 3: Language-Level Prompting Changes

Grouped bars: languages on X, signed relative metric-score changes on Y, three adjacent bars per language (COMET, variant-aware coverage, term BERTScore recall). Green/red encode gains/losses; shade and hatch identify the metric. Separate panels show each dataset; From and To figures remain separate.

Bar heights are 100 * (few - zero) / zero, calculated from equal-model mean scores, not means of per-model ratios. The symmetric-log Y axis preserves negative values and zero, and expands smaller changes. All panels and both roles share the same symmetric limits and linear threshold. The threshold is the decade at or below the smallest nonzero change, bounded to 0.0001%-0.1%, and printed on the figure. Labels are actual percentages, not logged values. Coverage changes are relative percentages, not percentage points or percentage gains in human translation quality.

Within each model, average identical supported partner directions for both prompts, then average models equally. Missing values or nonpositive zero-shot baselines are NA, not zero-height scores. A true zero is labeled 0%. * flags unequal scored-row counts. Equal counts do not prove matched rows; no significance inference. Native scores and deltas remain unchanged in the CSVs.

[Language scores and support](../../../tables/language_prompting_scores.csv) | [Per-model partner means](../../../tables/language_prompting_model_means.csv)

- luna/from_llm_enriched: [PNG](luna/from_llm_enriched.png) | [PDF](luna/from_llm_enriched.pdf)
- luna/to_llm_enriched: [PNG](luna/to_llm_enriched.png) | [PDF](luna/to_llm_enriched.pdf)
