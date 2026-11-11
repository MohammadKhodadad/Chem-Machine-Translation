# Metric Analysis

## Method

Nine representative metrics cover lexical overlap (BLEU, chrF++), reference-based semantic scores (BERTScore, BLEURT, COMET, XCOMET-XL), reference-free QE (COMETKiwi-QE), and terminology (variant-aware coverage, term BERTScore recall). New terminology analyses use only Luna LLM-enriched annotations.

For each metric pair and dataset, intersect finite direction scores across every selected model and both prompts. Average those directions equally within each model; do not pool datasets or treat model-direction points as independent. Prompt changes are few-shot minus zero-shot in native metric units. From/To sensitivity repeats the calculation on each language's supported partners. Pearson, Spearman and Kendall tau-b require at least three models and nonconstant vectors; otherwise NA. Top-model overlap is tie-aware Jaccard overlap. Same direction IDs or scored-row counts do not establish matched text rows. Counts and unknown-count flags are exported. No significance or causal claims.

## Figures

- Cross-Family Metric Relationships: [PNG](quality_terminology_relations.png) | [PDF](quality_terminology_relations.pdf)
- Metric Correlations by Dataset | Zero-Shot: [PNG](dataset_correlations_zero_shot.png) | [PDF](dataset_correlations_zero_shot.pdf)
- Metric Correlations by Dataset | Few-Shot: [PNG](dataset_correlations_few_shot.png) | [PDF](dataset_correlations_few_shot.pdf)
- Do Metrics Agree About Prompting Changes?: [PNG](prompting_change_agreement.png) | [PDF](prompting_change_agreement.pdf)
- Cross-Family Prompting Changes: [PNG](prompting_change_relations.png) | [PDF](prompting_change_relations.pdf)
- Model-Ranking Agreement | Zero-Shot: [PNG](ranking_agreement_zero_shot.png) | [PDF](ranking_agreement_zero_shot.pdf)
- Model-Ranking Agreement | Few-Shot: [PNG](ranking_agreement_few_shot.png) | [PDF](ranking_agreement_few_shot.pdf)
- Opposing Metric Changes on Individual Directions: [PNG](prompting_disagreements.png) | [PDF](prompting_disagreements.pdf)
- Metric Relationships by Source Language: [PNG](from_sensitivity.png) | [PDF](from_sensitivity.pdf)
- Metric Relationships by Target Language: [PNG](to_sensitivity.png) | [PDF](to_sensitivity.pdf)

## Native Scores and Supports

- [paired_model_scores](../../tables/metric_analysis/paired_model_scores.csv)
- [metric_relations](../../tables/metric_analysis/metric_relations.csv)
- [direction_changes](../../tables/metric_analysis/direction_changes.csv)
- [language_sensitivity](../../tables/metric_analysis/language_sensitivity.csv)
- [disagreement_cases](../../tables/metric_analysis/disagreement_cases.csv)

## Illustrative Opposing Changes

Examples are sorted by absolute delta product within each dataset/metric pair; they are metric disagreements, not verified translation errors. Inspect the underlying translations before interpreting them. An asterisk flags unequal scored-row counts; all row identities are unverified.

| Dataset | Metrics | Model | Direction | Change X | Change Y |
|---|---|---|---|---|---|
| Chemical Patents | chrF++ / COMET | Tiny Aya Global | en-zh | +5.04470 | -0.00663 |
| Chemical Patents | chrF++ / COMET | Granite 4.2 30B | zh-en | +2.24469 | -0.01154 |
| Chemical Patents | chrF++ / COMET | Nemotron 3.5 Lightning | ja-en | +1.38091 | -0.00320 |
| Chemical Patents | COMET / COMETKiwi-QE | Tiny Aya Global | ja-en | +0.02593 | -0.02657 |
| Chemical Patents | COMET / COMETKiwi-QE | Qwen3.8 27B | ru-en | +0.00582 | -0.03464 |
| Chemical Patents | COMET / COMETKiwi-QE | Gemma 4 31B | en-zh | -0.01196 | +0.01319 |
| Chemical Patents | COMET / Variant coverage | Gemma 4 31B | en-zh* | -0.01196 | +1.91998 |
| Chemical Patents | COMET / Variant coverage | Tiny Aya Global | de-en* | +0.00562 | -4.00012 |
| Chemical Patents | COMET / Variant coverage | Tiny Aya Global | en-zh* | -0.00663 | +1.72306 |
| Chemical Patents | COMET / Term BERTScore | Tiny Aya Global | de-en* | +0.00562 | -0.00136 |
| Chemical Patents | COMET / Term BERTScore | Nemotron 3.5 Lightning | fr-en* | +0.00631 | -0.00042 |
| Chemical Patents | COMET / Term BERTScore | Muse Glimmer 30B | en-zh* | -0.00330 | +0.00069 |
| JRC Articles | chrF++ / COMET | Tiny Aya Global | es-de | +6.60491 | -0.01267 |
| JRC Articles | chrF++ / COMET | Tiny Aya Global | fr-de | +9.25081 | -0.00657 |
| JRC Articles | chrF++ / COMET | Tiny Aya Global | pt-de | +8.56133 | -0.00538 |
| JRC Articles | COMET / COMETKiwi-QE | Muse Glimmer 30B | de-pt | +0.08922 | -0.01812 |
| JRC Articles | COMET / COMETKiwi-QE | Muse Glimmer 30B | de-es | +0.07144 | -0.01079 |
| JRC Articles | COMET / COMETKiwi-QE | Gemma 4 31B | en-fr | +0.01123 | -0.03132 |
| JRC Articles | COMET / Variant coverage | Tiny Aya Global | de-pt | -0.03125 | +13.46899 |
| JRC Articles | COMET / Variant coverage | Tiny Aya Global | de-fr | -0.03810 | +7.16761 |
| JRC Articles | COMET / Variant coverage | Tiny Aya Global | es-de | -0.01267 | +14.02712 |
| JRC Articles | COMET / Term BERTScore | Tiny Aya Global | es-de | -0.01267 | +0.00398 |
| JRC Articles | COMET / Term BERTScore | Tiny Aya Global | pt-de | -0.00538 | +0.00737 |
| JRC Articles | COMET / Term BERTScore | Tiny Aya Global | fr-de | -0.00657 | +0.00544 |
| JRC Definitions | chrF++ / COMET | Tiny Aya Global | fr-en | +1.68522 | -0.00270 |
| JRC Definitions | chrF++ / COMET | Nemotron 3.5 Lightning | de-en | +0.38236 | -0.00706 |
| JRC Definitions | chrF++ / COMET | Tiny Aya Global | pt-fr | +0.69468 | -0.00299 |
| JRC Definitions | COMET / COMETKiwi-QE | Tiny Aya Global | es-de | -0.08847 | +0.01234 |
| JRC Definitions | COMET / COMETKiwi-QE | Tiny Aya Global | de-es | -0.04810 | +0.00589 |
| JRC Definitions | COMET / COMETKiwi-QE | Tiny Aya Global | es-en | +0.00374 | -0.02643 |
| JRC Definitions | COMET / Variant coverage | Nemotron 3.5 Lightning | fr-de | -0.01158 | +2.15565 |
| JRC Definitions | COMET / Variant coverage | Tiny Aya Global | es-en | +0.00374 | -2.98649 |
| JRC Definitions | COMET / Variant coverage | Nemotron 3.5 Lightning | de-es | -0.00491 | +2.06686 |
| JRC Definitions | COMET / Term BERTScore | Tiny Aya Global | en-fr | -0.00488 | +0.00173 |
| JRC Definitions | COMET / Term BERTScore | Tiny Aya Global | pt-fr | -0.00299 | +0.00161 |
| JRC Definitions | COMET / Term BERTScore | Nemotron 3.5 Lightning | en-de | +0.00575 | -0.00081 |
