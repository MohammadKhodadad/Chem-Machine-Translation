# Story-Focused Chosen Figures

Preferred working collection for the language-first narrative. Sections 1-3 use only Luna LLM-enriched terminology, with both From and To views. Rankings are recomputed from that group; general scores remain shared. The full original analysis and older Chosen collection remain unchanged outside this curated folder.

## Working Story

Multilingual support should not be confused with uniformly strong performance on every evaluated direction. Start with language summaries, inspect native direction results, then ask whether prompting and model choice change the picture. The evidence supports uneven automatic-metric performance on these benchmark subsets, not training-data coverage, intrinsic language difficulty or a universal quality threshold.

## Suggested Manuscript Order

1. Language tables: median and best-model summaries, From/To roles and every dataset/prompt, with terminology restricted to Luna LLM-enriched. Start with dataset-specific coverage; overall tables cover only the common eligible language subset. Select compact panels for publication rather than all scorecards.
2. Direction performance: native median/best heatmaps across chemical patents, JRC articles and definitions. Terminology shows variant-aware target-term coverage and term BERTScore recall using only Luna LLM-enriched terms. Each dataset has From-language-row and To-language-row matrices (transposes of the same pair scores).
3. Figure 3: grouped bars with languages on X and signed percentage changes on Y. Each language has COMET, variant-aware coverage and term BERTScore recall bars; one panel per dataset. Green/red shades and patterns distinguish metric gains/losses. A shared symmetric-log Y scale shows smaller changes, negatives and zero. Only the Luna LLM-enriched From and To figures are included. Models are averaged equally; model-specific violins are not in this section.
4. Model comparison: combined-metric mixed-rank scorecards, the original Chosen zoomed native-score violins, and zoomed API-cost/rank plots with latency bubbles. Retain native values, all plotted points and the original latency-area scale.
5. Correlation matrices only, grouped into Metrics, Languages and Models. Show both Pearson and Spearman; keep datasets and metric scales separate. Language/model matrices have separate From/To views and average prompts equally. Other metric analyses remain outside this chosen collection.

The language-table section contains all 28 ranking figure sets. The collection is a working library, not a proposal to publish every table. Section 4 contains seven Luna combined-metric scorecards, nine original Chosen zoomed violin figures and seven zoomed cost/rank/latency figures. Section 5 contains five metric matrices plus sixteen language/model matrix figures.

## Interpretation Rules

- Median language tables first average supported partners within each model, then take the median across models per metric. Overall ranks balance dataset/prompt strata and semantic/lexical/terminology families. Rank differences are not native-score gaps.
- Language partner sets and text populations differ. Perform common-partner and annotation-view sensitivity checks before treating language order as a headline finding. Unranked languages have incomplete coverage, not zero performance.
- Sections 1-3 use one requested terminology definition: Luna LLM-enriched. This selection does not prove annotation-source superiority or view-robust effects. Other views/groups remain available in the full original analysis, not here.
- Best-observed results are selected on the test set. They are not validated deployment policies or per-translation oracles; model identity can vary by direction and metric.
- Violin points are direction aggregates, not individual translations. Prompt contrasts are descriptive; shared directions do not establish matched rows or significance.
- Figure 3 first averages identical partner directions within each model/prompt, then averages the selected models equally. Bars show 100 * (few - zero) / zero, not percentage points; nonpositive baselines are NA. These are relative metric-score changes, not percentage gains in translation quality. Row-count flags do not verify row identities, and equal counts do not prove matched rows. No significance inference.
- Terminology annotation subsets have different applicability/support. Higher coverage on verified terms is not proof that refinement improved translation quality. Reference term coverage is not language-support or training-data coverage.
- Metric/language correlations use model observations; model-to-model correlations use supported language profiles. These are small, dependent cohorts, not pooled independent translations. Different metrics and languages can use different supports. Constant vectors or fewer than three observations are NA, not zero. Correlations do not establish significance, causes or intrinsic language difficulty.
- Zoomed API-cost panels use different native axis ranges, but preserve all points, original model ranks and the same latency bubble-area scale. Prices are hypothetical hosted repricing, not actual bills; latency comes from original deployments. Quality, cost and timing populations are not proven row-matched.

## Sources and Sensitivity

[Selected language tables](../../story_luna_llm_enriched/tables/language_rankings/README.md) | [Selected coverage CSV](../../story_luna_llm_enriched/tables/language_rankings/coverage.csv) | [All original language figures](../languages/README.md) | [Original Chosen collection](../chosen/README.md) | [Copy checksums](selection.csv)

Rebuild: `uv run --no-sync python scripts/render_evaluation_results.py --story-chosen-only`.

## 01 Language Tables

Ranking hierarchy: `median|top / from|to / luna / dataset_prompt|overall`. Terminology uses only LLM-enriched terms. PNG and PDF are available.

### Median From Luna Llm Enriched Overall

Common-language subset across all datasets and both prompts; median from-language ranks. Terminology uses only Luna LLM-enriched scores. Incomplete support is unranked, not zero.

[PNG](01_language_tables/median/from/luna/language_rankings_overall.png) | [PDF](01_language_tables/median/from/luna/language_rankings_overall.pdf) | [Original PNG](../../story_luna_llm_enriched/figures/languages/rankings/median/from/luna/language_rankings_overall.png)

### Median From Luna Llm Enriched Google Patents Zero Shot

Chemical Patents, zero shot; median from-language ranks. Terminology uses only Luna LLM-enriched scores. Incomplete support is unranked, not zero.

[PNG](01_language_tables/median/from/luna/language_rankings_google_patents_zero_shot.png) | [PDF](01_language_tables/median/from/luna/language_rankings_google_patents_zero_shot.pdf) | [Original PNG](../../story_luna_llm_enriched/figures/languages/rankings/median/from/luna/language_rankings_google_patents_zero_shot.png)

### Median From Luna Llm Enriched Google Patents Few Shot

Chemical Patents, few shot; median from-language ranks. Terminology uses only Luna LLM-enriched scores. Incomplete support is unranked, not zero.

[PNG](01_language_tables/median/from/luna/language_rankings_google_patents_few_shot.png) | [PDF](01_language_tables/median/from/luna/language_rankings_google_patents_few_shot.pdf) | [Original PNG](../../story_luna_llm_enriched/figures/languages/rankings/median/from/luna/language_rankings_google_patents_few_shot.png)

### Median From Luna Llm Enriched Jrc Articles Zero Shot

JRC Articles, zero shot; median from-language ranks. Terminology uses only Luna LLM-enriched scores. Incomplete support is unranked, not zero.

[PNG](01_language_tables/median/from/luna/language_rankings_jrc_articles_zero_shot.png) | [PDF](01_language_tables/median/from/luna/language_rankings_jrc_articles_zero_shot.pdf) | [Original PNG](../../story_luna_llm_enriched/figures/languages/rankings/median/from/luna/language_rankings_jrc_articles_zero_shot.png)

### Median From Luna Llm Enriched Jrc Articles Few Shot

JRC Articles, few shot; median from-language ranks. Terminology uses only Luna LLM-enriched scores. Incomplete support is unranked, not zero.

[PNG](01_language_tables/median/from/luna/language_rankings_jrc_articles_few_shot.png) | [PDF](01_language_tables/median/from/luna/language_rankings_jrc_articles_few_shot.pdf) | [Original PNG](../../story_luna_llm_enriched/figures/languages/rankings/median/from/luna/language_rankings_jrc_articles_few_shot.png)

### Median From Luna Llm Enriched Jrc Definitions Zero Shot

JRC Definitions, zero shot; median from-language ranks. Terminology uses only Luna LLM-enriched scores. Incomplete support is unranked, not zero.

[PNG](01_language_tables/median/from/luna/language_rankings_jrc_definitions_zero_shot.png) | [PDF](01_language_tables/median/from/luna/language_rankings_jrc_definitions_zero_shot.pdf) | [Original PNG](../../story_luna_llm_enriched/figures/languages/rankings/median/from/luna/language_rankings_jrc_definitions_zero_shot.png)

### Median From Luna Llm Enriched Jrc Definitions Few Shot

JRC Definitions, few shot; median from-language ranks. Terminology uses only Luna LLM-enriched scores. Incomplete support is unranked, not zero.

[PNG](01_language_tables/median/from/luna/language_rankings_jrc_definitions_few_shot.png) | [PDF](01_language_tables/median/from/luna/language_rankings_jrc_definitions_few_shot.pdf) | [Original PNG](../../story_luna_llm_enriched/figures/languages/rankings/median/from/luna/language_rankings_jrc_definitions_few_shot.png)

### Median To Luna Llm Enriched Overall

Common-language subset across all datasets and both prompts; median to-language ranks. Terminology uses only Luna LLM-enriched scores. Incomplete support is unranked, not zero.

[PNG](01_language_tables/median/to/luna/language_rankings_overall.png) | [PDF](01_language_tables/median/to/luna/language_rankings_overall.pdf) | [Original PNG](../../story_luna_llm_enriched/figures/languages/rankings/median/to/luna/language_rankings_overall.png)

### Median To Luna Llm Enriched Google Patents Zero Shot

Chemical Patents, zero shot; median to-language ranks. Terminology uses only Luna LLM-enriched scores. Incomplete support is unranked, not zero.

[PNG](01_language_tables/median/to/luna/language_rankings_google_patents_zero_shot.png) | [PDF](01_language_tables/median/to/luna/language_rankings_google_patents_zero_shot.pdf) | [Original PNG](../../story_luna_llm_enriched/figures/languages/rankings/median/to/luna/language_rankings_google_patents_zero_shot.png)

### Median To Luna Llm Enriched Google Patents Few Shot

Chemical Patents, few shot; median to-language ranks. Terminology uses only Luna LLM-enriched scores. Incomplete support is unranked, not zero.

[PNG](01_language_tables/median/to/luna/language_rankings_google_patents_few_shot.png) | [PDF](01_language_tables/median/to/luna/language_rankings_google_patents_few_shot.pdf) | [Original PNG](../../story_luna_llm_enriched/figures/languages/rankings/median/to/luna/language_rankings_google_patents_few_shot.png)

### Median To Luna Llm Enriched Jrc Articles Zero Shot

JRC Articles, zero shot; median to-language ranks. Terminology uses only Luna LLM-enriched scores. Incomplete support is unranked, not zero.

[PNG](01_language_tables/median/to/luna/language_rankings_jrc_articles_zero_shot.png) | [PDF](01_language_tables/median/to/luna/language_rankings_jrc_articles_zero_shot.pdf) | [Original PNG](../../story_luna_llm_enriched/figures/languages/rankings/median/to/luna/language_rankings_jrc_articles_zero_shot.png)

### Median To Luna Llm Enriched Jrc Articles Few Shot

JRC Articles, few shot; median to-language ranks. Terminology uses only Luna LLM-enriched scores. Incomplete support is unranked, not zero.

[PNG](01_language_tables/median/to/luna/language_rankings_jrc_articles_few_shot.png) | [PDF](01_language_tables/median/to/luna/language_rankings_jrc_articles_few_shot.pdf) | [Original PNG](../../story_luna_llm_enriched/figures/languages/rankings/median/to/luna/language_rankings_jrc_articles_few_shot.png)

### Median To Luna Llm Enriched Jrc Definitions Zero Shot

JRC Definitions, zero shot; median to-language ranks. Terminology uses only Luna LLM-enriched scores. Incomplete support is unranked, not zero.

[PNG](01_language_tables/median/to/luna/language_rankings_jrc_definitions_zero_shot.png) | [PDF](01_language_tables/median/to/luna/language_rankings_jrc_definitions_zero_shot.pdf) | [Original PNG](../../story_luna_llm_enriched/figures/languages/rankings/median/to/luna/language_rankings_jrc_definitions_zero_shot.png)

### Median To Luna Llm Enriched Jrc Definitions Few Shot

JRC Definitions, few shot; median to-language ranks. Terminology uses only Luna LLM-enriched scores. Incomplete support is unranked, not zero.

[PNG](01_language_tables/median/to/luna/language_rankings_jrc_definitions_few_shot.png) | [PDF](01_language_tables/median/to/luna/language_rankings_jrc_definitions_few_shot.pdf) | [Original PNG](../../story_luna_llm_enriched/figures/languages/rankings/median/to/luna/language_rankings_jrc_definitions_few_shot.png)

### Top From Luna Llm Enriched Overall

Common-language subset across all datasets and both prompts; top from-language ranks. Terminology uses only Luna LLM-enriched scores. Incomplete support is unranked, not zero.

[PNG](01_language_tables/top/from/luna/language_rankings_overall.png) | [PDF](01_language_tables/top/from/luna/language_rankings_overall.pdf) | [Original PNG](../../story_luna_llm_enriched/figures/languages/rankings/top/from/luna/language_rankings_overall.png)

### Top From Luna Llm Enriched Google Patents Zero Shot

Chemical Patents, zero shot; top from-language ranks. Terminology uses only Luna LLM-enriched scores. Incomplete support is unranked, not zero.

[PNG](01_language_tables/top/from/luna/language_rankings_google_patents_zero_shot.png) | [PDF](01_language_tables/top/from/luna/language_rankings_google_patents_zero_shot.pdf) | [Original PNG](../../story_luna_llm_enriched/figures/languages/rankings/top/from/luna/language_rankings_google_patents_zero_shot.png)

### Top From Luna Llm Enriched Google Patents Few Shot

Chemical Patents, few shot; top from-language ranks. Terminology uses only Luna LLM-enriched scores. Incomplete support is unranked, not zero.

[PNG](01_language_tables/top/from/luna/language_rankings_google_patents_few_shot.png) | [PDF](01_language_tables/top/from/luna/language_rankings_google_patents_few_shot.pdf) | [Original PNG](../../story_luna_llm_enriched/figures/languages/rankings/top/from/luna/language_rankings_google_patents_few_shot.png)

### Top From Luna Llm Enriched Jrc Articles Zero Shot

JRC Articles, zero shot; top from-language ranks. Terminology uses only Luna LLM-enriched scores. Incomplete support is unranked, not zero.

[PNG](01_language_tables/top/from/luna/language_rankings_jrc_articles_zero_shot.png) | [PDF](01_language_tables/top/from/luna/language_rankings_jrc_articles_zero_shot.pdf) | [Original PNG](../../story_luna_llm_enriched/figures/languages/rankings/top/from/luna/language_rankings_jrc_articles_zero_shot.png)

### Top From Luna Llm Enriched Jrc Articles Few Shot

JRC Articles, few shot; top from-language ranks. Terminology uses only Luna LLM-enriched scores. Incomplete support is unranked, not zero.

[PNG](01_language_tables/top/from/luna/language_rankings_jrc_articles_few_shot.png) | [PDF](01_language_tables/top/from/luna/language_rankings_jrc_articles_few_shot.pdf) | [Original PNG](../../story_luna_llm_enriched/figures/languages/rankings/top/from/luna/language_rankings_jrc_articles_few_shot.png)

### Top From Luna Llm Enriched Jrc Definitions Zero Shot

JRC Definitions, zero shot; top from-language ranks. Terminology uses only Luna LLM-enriched scores. Incomplete support is unranked, not zero.

[PNG](01_language_tables/top/from/luna/language_rankings_jrc_definitions_zero_shot.png) | [PDF](01_language_tables/top/from/luna/language_rankings_jrc_definitions_zero_shot.pdf) | [Original PNG](../../story_luna_llm_enriched/figures/languages/rankings/top/from/luna/language_rankings_jrc_definitions_zero_shot.png)

### Top From Luna Llm Enriched Jrc Definitions Few Shot

JRC Definitions, few shot; top from-language ranks. Terminology uses only Luna LLM-enriched scores. Incomplete support is unranked, not zero.

[PNG](01_language_tables/top/from/luna/language_rankings_jrc_definitions_few_shot.png) | [PDF](01_language_tables/top/from/luna/language_rankings_jrc_definitions_few_shot.pdf) | [Original PNG](../../story_luna_llm_enriched/figures/languages/rankings/top/from/luna/language_rankings_jrc_definitions_few_shot.png)

### Top To Luna Llm Enriched Overall

Common-language subset across all datasets and both prompts; top to-language ranks. Terminology uses only Luna LLM-enriched scores. Incomplete support is unranked, not zero.

[PNG](01_language_tables/top/to/luna/language_rankings_overall.png) | [PDF](01_language_tables/top/to/luna/language_rankings_overall.pdf) | [Original PNG](../../story_luna_llm_enriched/figures/languages/rankings/top/to/luna/language_rankings_overall.png)

### Top To Luna Llm Enriched Google Patents Zero Shot

Chemical Patents, zero shot; top to-language ranks. Terminology uses only Luna LLM-enriched scores. Incomplete support is unranked, not zero.

[PNG](01_language_tables/top/to/luna/language_rankings_google_patents_zero_shot.png) | [PDF](01_language_tables/top/to/luna/language_rankings_google_patents_zero_shot.pdf) | [Original PNG](../../story_luna_llm_enriched/figures/languages/rankings/top/to/luna/language_rankings_google_patents_zero_shot.png)

### Top To Luna Llm Enriched Google Patents Few Shot

Chemical Patents, few shot; top to-language ranks. Terminology uses only Luna LLM-enriched scores. Incomplete support is unranked, not zero.

[PNG](01_language_tables/top/to/luna/language_rankings_google_patents_few_shot.png) | [PDF](01_language_tables/top/to/luna/language_rankings_google_patents_few_shot.pdf) | [Original PNG](../../story_luna_llm_enriched/figures/languages/rankings/top/to/luna/language_rankings_google_patents_few_shot.png)

### Top To Luna Llm Enriched Jrc Articles Zero Shot

JRC Articles, zero shot; top to-language ranks. Terminology uses only Luna LLM-enriched scores. Incomplete support is unranked, not zero.

[PNG](01_language_tables/top/to/luna/language_rankings_jrc_articles_zero_shot.png) | [PDF](01_language_tables/top/to/luna/language_rankings_jrc_articles_zero_shot.pdf) | [Original PNG](../../story_luna_llm_enriched/figures/languages/rankings/top/to/luna/language_rankings_jrc_articles_zero_shot.png)

### Top To Luna Llm Enriched Jrc Articles Few Shot

JRC Articles, few shot; top to-language ranks. Terminology uses only Luna LLM-enriched scores. Incomplete support is unranked, not zero.

[PNG](01_language_tables/top/to/luna/language_rankings_jrc_articles_few_shot.png) | [PDF](01_language_tables/top/to/luna/language_rankings_jrc_articles_few_shot.pdf) | [Original PNG](../../story_luna_llm_enriched/figures/languages/rankings/top/to/luna/language_rankings_jrc_articles_few_shot.png)

### Top To Luna Llm Enriched Jrc Definitions Zero Shot

JRC Definitions, zero shot; top to-language ranks. Terminology uses only Luna LLM-enriched scores. Incomplete support is unranked, not zero.

[PNG](01_language_tables/top/to/luna/language_rankings_jrc_definitions_zero_shot.png) | [PDF](01_language_tables/top/to/luna/language_rankings_jrc_definitions_zero_shot.pdf) | [Original PNG](../../story_luna_llm_enriched/figures/languages/rankings/top/to/luna/language_rankings_jrc_definitions_zero_shot.png)

### Top To Luna Llm Enriched Jrc Definitions Few Shot

JRC Definitions, few shot; top to-language ranks. Terminology uses only Luna LLM-enriched scores. Incomplete support is unranked, not zero.

[PNG](01_language_tables/top/to/luna/language_rankings_jrc_definitions_few_shot.png) | [PDF](01_language_tables/top/to/luna/language_rankings_jrc_definitions_few_shot.pdf) | [Original PNG](../../story_luna_llm_enriched/figures/languages/rankings/top/to/luna/language_rankings_jrc_definitions_few_shot.png)

## 02 Direction Performance

### Google Patents General From

Chemical Patents: best/median general scores with from-language rows. Terminology uses only Luna LLM-enriched variant-aware coverage and term BERTScore recall. From/To matrices transpose the same pair scores.

[PNG](02_direction_performance/from/google_patents_general.png) | [PDF](02_direction_performance/from/google_patents_general.pdf) | [Original PNG](../../story_luna_llm_enriched/figures/languages/direction_general/shared_general/from/comparison_google_patents_zero_shot.png)

### Google Patents Terminology From

Chemical Patents: best/median terminology scores with from-language rows. Terminology uses only Luna LLM-enriched variant-aware coverage and term BERTScore recall. From/To matrices transpose the same pair scores.

[PNG](02_direction_performance/from/google_patents_terminology.png) | [PDF](02_direction_performance/from/google_patents_terminology.pdf) | [Original PNG](../../story_luna_llm_enriched/figures/languages/direction_terminology/luna/from/comparison_google_patents_zero_shot.png)

### Jrc Articles General From

JRC Articles: best/median general scores with from-language rows. Terminology uses only Luna LLM-enriched variant-aware coverage and term BERTScore recall. From/To matrices transpose the same pair scores.

[PNG](02_direction_performance/from/jrc_articles_general.png) | [PDF](02_direction_performance/from/jrc_articles_general.pdf) | [Original PNG](../../story_luna_llm_enriched/figures/languages/direction_general/shared_general/from/comparison_jrc_articles_zero_shot.png)

### Jrc Articles Terminology From

JRC Articles: best/median terminology scores with from-language rows. Terminology uses only Luna LLM-enriched variant-aware coverage and term BERTScore recall. From/To matrices transpose the same pair scores.

[PNG](02_direction_performance/from/jrc_articles_terminology.png) | [PDF](02_direction_performance/from/jrc_articles_terminology.pdf) | [Original PNG](../../story_luna_llm_enriched/figures/languages/direction_terminology/luna/from/comparison_jrc_articles_zero_shot.png)

### Jrc Definitions General From

JRC Definitions: best/median general scores with from-language rows. Terminology uses only Luna LLM-enriched variant-aware coverage and term BERTScore recall. From/To matrices transpose the same pair scores.

[PNG](02_direction_performance/from/jrc_definitions_general.png) | [PDF](02_direction_performance/from/jrc_definitions_general.pdf) | [Original PNG](../../story_luna_llm_enriched/figures/languages/direction_general/shared_general/from/comparison_jrc_definitions_zero_shot.png)

### Jrc Definitions Terminology From

JRC Definitions: best/median terminology scores with from-language rows. Terminology uses only Luna LLM-enriched variant-aware coverage and term BERTScore recall. From/To matrices transpose the same pair scores.

[PNG](02_direction_performance/from/jrc_definitions_terminology.png) | [PDF](02_direction_performance/from/jrc_definitions_terminology.pdf) | [Original PNG](../../story_luna_llm_enriched/figures/languages/direction_terminology/luna/from/comparison_jrc_definitions_zero_shot.png)

### Google Patents General To

Chemical Patents: best/median general scores with to-language rows. Terminology uses only Luna LLM-enriched variant-aware coverage and term BERTScore recall. From/To matrices transpose the same pair scores.

[PNG](02_direction_performance/to/google_patents_general.png) | [PDF](02_direction_performance/to/google_patents_general.pdf) | [Original PNG](../../story_luna_llm_enriched/figures/languages/direction_general/shared_general/to/comparison_google_patents_zero_shot.png)

### Google Patents Terminology To

Chemical Patents: best/median terminology scores with to-language rows. Terminology uses only Luna LLM-enriched variant-aware coverage and term BERTScore recall. From/To matrices transpose the same pair scores.

[PNG](02_direction_performance/to/google_patents_terminology.png) | [PDF](02_direction_performance/to/google_patents_terminology.pdf) | [Original PNG](../../story_luna_llm_enriched/figures/languages/direction_terminology/luna/to/comparison_google_patents_zero_shot.png)

### Jrc Articles General To

JRC Articles: best/median general scores with to-language rows. Terminology uses only Luna LLM-enriched variant-aware coverage and term BERTScore recall. From/To matrices transpose the same pair scores.

[PNG](02_direction_performance/to/jrc_articles_general.png) | [PDF](02_direction_performance/to/jrc_articles_general.pdf) | [Original PNG](../../story_luna_llm_enriched/figures/languages/direction_general/shared_general/to/comparison_jrc_articles_zero_shot.png)

### Jrc Articles Terminology To

JRC Articles: best/median terminology scores with to-language rows. Terminology uses only Luna LLM-enriched variant-aware coverage and term BERTScore recall. From/To matrices transpose the same pair scores.

[PNG](02_direction_performance/to/jrc_articles_terminology.png) | [PDF](02_direction_performance/to/jrc_articles_terminology.pdf) | [Original PNG](../../story_luna_llm_enriched/figures/languages/direction_terminology/luna/to/comparison_jrc_articles_zero_shot.png)

### Jrc Definitions General To

JRC Definitions: best/median general scores with to-language rows. Terminology uses only Luna LLM-enriched variant-aware coverage and term BERTScore recall. From/To matrices transpose the same pair scores.

[PNG](02_direction_performance/to/jrc_definitions_general.png) | [PDF](02_direction_performance/to/jrc_definitions_general.pdf) | [Original PNG](../../story_luna_llm_enriched/figures/languages/direction_general/shared_general/to/comparison_jrc_definitions_zero_shot.png)

### Jrc Definitions Terminology To

JRC Definitions: best/median terminology scores with to-language rows. Terminology uses only Luna LLM-enriched variant-aware coverage and term BERTScore recall. From/To matrices transpose the same pair scores.

[PNG](02_direction_performance/to/jrc_definitions_terminology.png) | [PDF](02_direction_performance/to/jrc_definitions_terminology.pdf) | [Original PNG](../../story_luna_llm_enriched/figures/languages/direction_terminology/luna/to/comparison_jrc_definitions_zero_shot.png)

## 03 Zero-Shot vs Few-Shot

Only two grouped bar plots: From and To, Luna LLM-enriched. Languages are on X; three adjacent, differently shaded/patterned metric bars show gains in green and losses in red. The shared symmetric-log Y axis retains actual percentage labels and a linear region around zero. Other groups/views and model-specific violins are omitted here. [Method and support exports](../../story_luna_llm_enriched/figures/prompting/language_changes/README.md).

### Figure 03 Luna From Llm Enriched

Figure 3: from-language grouped percentage-change bars with symmetric-log Y. COMET plus Luna LLM-enriched variant-aware coverage and term BERTScore recall.

[PNG](03_prompting/from/figure_03_luna_from_llm_enriched.png) | [PDF](03_prompting/from/figure_03_luna_from_llm_enriched.pdf) | [Original PNG](../../story_luna_llm_enriched/figures/prompting/language_changes/luna/from_llm_enriched.png)

### Figure 03 Luna To Llm Enriched

Figure 3: to-language grouped percentage-change bars with symmetric-log Y. COMET plus Luna LLM-enriched variant-aware coverage and term BERTScore recall.

[PNG](03_prompting/to/figure_03_luna_to_llm_enriched.png) | [PDF](03_prompting/to/figure_03_luna_to_llm_enriched.pdf) | [Original PNG](../../story_luna_llm_enriched/figures/prompting/language_changes/luna/to_llm_enriched.png)

## 04 Model Comparison

Combined metric = the original balanced mixed rank across semantic, lexical and terminology families, not a new raw-score average. Scorecards use Luna; copied Chosen violins retain general metrics and both terminology annotation views/groups. These are native-score zooms, not normalization. Cost/rank axes zoom independently for each panel; latency bubble sizes keep the original common scale. [Cost/latency method and native data](../../story_luna_llm_enriched/figures/cost_rank_latency_zoomed/README.md).

Rebuild the zoomed efficiency figures: `uv run --no-sync python scripts/render_evaluation_results.py --model-comparison-only`.

### Balanced Model Overall

Common-language subset across all datasets and both prompts: combined semantic, lexical and terminology mixed-rank scorecard. Original Luna ranking across all term groups; descriptive equal family weights.

[PNG](04_model_behavior/combined_metric/luna/overall.png) | [PDF](04_model_behavior/combined_metric/luna/overall.pdf) | [Original PNG](../chosen/01_balanced_mixed_rank/luna/chosen_01_balanced_mixed_rank_overall.png)

### Api Cost Rank Latency Overall

Common-language subset across all datasets and both prompts: zoomed API cost versus mixed rank with observed-latency bubbles. Per-panel native axes; no points clipped, rank changes or bubble rescaling. Hosted reference repricing is not actual billing or the timed deployment.

[PNG](04_model_behavior/api_cost_rank_latency_zoomed/luna/overall.png) | [PDF](04_model_behavior/api_cost_rank_latency_zoomed/luna/overall.pdf) | [Original PNG](../../story_luna_llm_enriched/figures/cost_rank_latency_zoomed/luna/cost_rank_latency_overall.png)

### Balanced Model Google Patents Zero Shot

Chemical Patents, zero shot: combined semantic, lexical and terminology mixed-rank scorecard. Original Luna ranking across all term groups; descriptive equal family weights.

[PNG](04_model_behavior/combined_metric/luna/google_patents_zero_shot.png) | [PDF](04_model_behavior/combined_metric/luna/google_patents_zero_shot.pdf) | [Original PNG](../chosen/01_balanced_mixed_rank/luna/chosen_01_balanced_mixed_rank_google_patents_zero_shot.png)

### Api Cost Rank Latency Google Patents Zero Shot

Chemical Patents, zero shot: zoomed API cost versus mixed rank with observed-latency bubbles. Per-panel native axes; no points clipped, rank changes or bubble rescaling. Hosted reference repricing is not actual billing or the timed deployment.

[PNG](04_model_behavior/api_cost_rank_latency_zoomed/luna/google_patents_zero_shot.png) | [PDF](04_model_behavior/api_cost_rank_latency_zoomed/luna/google_patents_zero_shot.pdf) | [Original PNG](../../story_luna_llm_enriched/figures/cost_rank_latency_zoomed/luna/cost_rank_latency_google_patents_zero_shot.png)

### Balanced Model Google Patents Few Shot

Chemical Patents, few shot: combined semantic, lexical and terminology mixed-rank scorecard. Original Luna ranking across all term groups; descriptive equal family weights.

[PNG](04_model_behavior/combined_metric/luna/google_patents_few_shot.png) | [PDF](04_model_behavior/combined_metric/luna/google_patents_few_shot.pdf) | [Original PNG](../chosen/01_balanced_mixed_rank/luna/chosen_01_balanced_mixed_rank_google_patents_few_shot.png)

### Api Cost Rank Latency Google Patents Few Shot

Chemical Patents, few shot: zoomed API cost versus mixed rank with observed-latency bubbles. Per-panel native axes; no points clipped, rank changes or bubble rescaling. Hosted reference repricing is not actual billing or the timed deployment.

[PNG](04_model_behavior/api_cost_rank_latency_zoomed/luna/google_patents_few_shot.png) | [PDF](04_model_behavior/api_cost_rank_latency_zoomed/luna/google_patents_few_shot.pdf) | [Original PNG](../../story_luna_llm_enriched/figures/cost_rank_latency_zoomed/luna/cost_rank_latency_google_patents_few_shot.png)

### Balanced Model Jrc Articles Zero Shot

JRC Articles, zero shot: combined semantic, lexical and terminology mixed-rank scorecard. Original Luna ranking across all term groups; descriptive equal family weights.

[PNG](04_model_behavior/combined_metric/luna/jrc_articles_zero_shot.png) | [PDF](04_model_behavior/combined_metric/luna/jrc_articles_zero_shot.pdf) | [Original PNG](../chosen/01_balanced_mixed_rank/luna/chosen_01_balanced_mixed_rank_jrc_articles_zero_shot.png)

### Api Cost Rank Latency Jrc Articles Zero Shot

JRC Articles, zero shot: zoomed API cost versus mixed rank with observed-latency bubbles. Per-panel native axes; no points clipped, rank changes or bubble rescaling. Hosted reference repricing is not actual billing or the timed deployment.

[PNG](04_model_behavior/api_cost_rank_latency_zoomed/luna/jrc_articles_zero_shot.png) | [PDF](04_model_behavior/api_cost_rank_latency_zoomed/luna/jrc_articles_zero_shot.pdf) | [Original PNG](../../story_luna_llm_enriched/figures/cost_rank_latency_zoomed/luna/cost_rank_latency_jrc_articles_zero_shot.png)

### Balanced Model Jrc Articles Few Shot

JRC Articles, few shot: combined semantic, lexical and terminology mixed-rank scorecard. Original Luna ranking across all term groups; descriptive equal family weights.

[PNG](04_model_behavior/combined_metric/luna/jrc_articles_few_shot.png) | [PDF](04_model_behavior/combined_metric/luna/jrc_articles_few_shot.pdf) | [Original PNG](../chosen/01_balanced_mixed_rank/luna/chosen_01_balanced_mixed_rank_jrc_articles_few_shot.png)

### Api Cost Rank Latency Jrc Articles Few Shot

JRC Articles, few shot: zoomed API cost versus mixed rank with observed-latency bubbles. Per-panel native axes; no points clipped, rank changes or bubble rescaling. Hosted reference repricing is not actual billing or the timed deployment.

[PNG](04_model_behavior/api_cost_rank_latency_zoomed/luna/jrc_articles_few_shot.png) | [PDF](04_model_behavior/api_cost_rank_latency_zoomed/luna/jrc_articles_few_shot.pdf) | [Original PNG](../../story_luna_llm_enriched/figures/cost_rank_latency_zoomed/luna/cost_rank_latency_jrc_articles_few_shot.png)

### Balanced Model Jrc Definitions Zero Shot

JRC Definitions, zero shot: combined semantic, lexical and terminology mixed-rank scorecard. Original Luna ranking across all term groups; descriptive equal family weights.

[PNG](04_model_behavior/combined_metric/luna/jrc_definitions_zero_shot.png) | [PDF](04_model_behavior/combined_metric/luna/jrc_definitions_zero_shot.pdf) | [Original PNG](../chosen/01_balanced_mixed_rank/luna/chosen_01_balanced_mixed_rank_jrc_definitions_zero_shot.png)

### Api Cost Rank Latency Jrc Definitions Zero Shot

JRC Definitions, zero shot: zoomed API cost versus mixed rank with observed-latency bubbles. Per-panel native axes; no points clipped, rank changes or bubble rescaling. Hosted reference repricing is not actual billing or the timed deployment.

[PNG](04_model_behavior/api_cost_rank_latency_zoomed/luna/jrc_definitions_zero_shot.png) | [PDF](04_model_behavior/api_cost_rank_latency_zoomed/luna/jrc_definitions_zero_shot.pdf) | [Original PNG](../../story_luna_llm_enriched/figures/cost_rank_latency_zoomed/luna/cost_rank_latency_jrc_definitions_zero_shot.png)

### Balanced Model Jrc Definitions Few Shot

JRC Definitions, few shot: combined semantic, lexical and terminology mixed-rank scorecard. Original Luna ranking across all term groups; descriptive equal family weights.

[PNG](04_model_behavior/combined_metric/luna/jrc_definitions_few_shot.png) | [PDF](04_model_behavior/combined_metric/luna/jrc_definitions_few_shot.pdf) | [Original PNG](../chosen/01_balanced_mixed_rank/luna/chosen_01_balanced_mixed_rank_jrc_definitions_few_shot.png)

### Api Cost Rank Latency Jrc Definitions Few Shot

JRC Definitions, few shot: zoomed API cost versus mixed rank with observed-latency bubbles. Per-panel native axes; no points clipped, rank changes or bubble rescaling. Hosted reference repricing is not actual billing or the timed deployment.

[PNG](04_model_behavior/api_cost_rank_latency_zoomed/luna/jrc_definitions_few_shot.png) | [PDF](04_model_behavior/api_cost_rank_latency_zoomed/luna/jrc_definitions_few_shot.pdf) | [Original PNG](../../story_luna_llm_enriched/figures/cost_rank_latency_zoomed/luna/cost_rank_latency_jrc_definitions_few_shot.png)

### Zoomed Violins Shared General Google Patents

Chemical Patents: original Chosen zoomed native-score general violins, shared_general. Zero/few-shot direction distributions; native scores, not normalized values.

[PNG](04_model_behavior/zoomed_native_violins/shared_general/google_patents.png) | [PDF](04_model_behavior/zoomed_native_violins/shared_general/google_patents.pdf) | [Original PNG](../chosen/05_zoomed_native_violins/shared_general/chosen_05_prompting_violins_zoomed_general_google_patents.png)

### Zoomed Violins Original Glm Google Patents

Chemical Patents: original Chosen zoomed native-score terminology violins, original_glm. Zero/few-shot direction distributions; native scores, not normalized values.

[PNG](04_model_behavior/zoomed_native_violins/original_glm/google_patents.png) | [PDF](04_model_behavior/zoomed_native_violins/original_glm/google_patents.pdf) | [Original PNG](../chosen/05_zoomed_native_violins/original_glm/chosen_05_prompting_violins_zoomed_terminology_google_patents.png)

### Zoomed Violins Luna Google Patents

Chemical Patents: original Chosen zoomed native-score terminology violins, luna. Zero/few-shot direction distributions; native scores, not normalized values.

[PNG](04_model_behavior/zoomed_native_violins/luna/google_patents.png) | [PDF](04_model_behavior/zoomed_native_violins/luna/google_patents.pdf) | [Original PNG](../chosen/05_zoomed_native_violins/luna/chosen_05_prompting_violins_zoomed_terminology_google_patents.png)

### Zoomed Violins Shared General Jrc Articles

JRC Articles: original Chosen zoomed native-score general violins, shared_general. Zero/few-shot direction distributions; native scores, not normalized values.

[PNG](04_model_behavior/zoomed_native_violins/shared_general/jrc_articles.png) | [PDF](04_model_behavior/zoomed_native_violins/shared_general/jrc_articles.pdf) | [Original PNG](../chosen/05_zoomed_native_violins/shared_general/chosen_05_prompting_violins_zoomed_general_jrc_articles.png)

### Zoomed Violins Original Glm Jrc Articles

JRC Articles: original Chosen zoomed native-score terminology violins, original_glm. Zero/few-shot direction distributions; native scores, not normalized values.

[PNG](04_model_behavior/zoomed_native_violins/original_glm/jrc_articles.png) | [PDF](04_model_behavior/zoomed_native_violins/original_glm/jrc_articles.pdf) | [Original PNG](../chosen/05_zoomed_native_violins/original_glm/chosen_05_prompting_violins_zoomed_terminology_jrc_articles.png)

### Zoomed Violins Luna Jrc Articles

JRC Articles: original Chosen zoomed native-score terminology violins, luna. Zero/few-shot direction distributions; native scores, not normalized values.

[PNG](04_model_behavior/zoomed_native_violins/luna/jrc_articles.png) | [PDF](04_model_behavior/zoomed_native_violins/luna/jrc_articles.pdf) | [Original PNG](../chosen/05_zoomed_native_violins/luna/chosen_05_prompting_violins_zoomed_terminology_jrc_articles.png)

### Zoomed Violins Shared General Jrc Definitions

JRC Definitions: original Chosen zoomed native-score general violins, shared_general. Zero/few-shot direction distributions; native scores, not normalized values.

[PNG](04_model_behavior/zoomed_native_violins/shared_general/jrc_definitions.png) | [PDF](04_model_behavior/zoomed_native_violins/shared_general/jrc_definitions.pdf) | [Original PNG](../chosen/05_zoomed_native_violins/shared_general/chosen_05_prompting_violins_zoomed_general_jrc_definitions.png)

### Zoomed Violins Original Glm Jrc Definitions

JRC Definitions: original Chosen zoomed native-score terminology violins, original_glm. Zero/few-shot direction distributions; native scores, not normalized values.

[PNG](04_model_behavior/zoomed_native_violins/original_glm/jrc_definitions.png) | [PDF](04_model_behavior/zoomed_native_violins/original_glm/jrc_definitions.pdf) | [Original PNG](../chosen/05_zoomed_native_violins/original_glm/chosen_05_prompting_violins_zoomed_terminology_jrc_definitions.png)

### Zoomed Violins Luna Jrc Definitions

JRC Definitions: original Chosen zoomed native-score terminology violins, luna. Zero/few-shot direction distributions; native scores, not normalized values.

[PNG](04_model_behavior/zoomed_native_violins/luna/jrc_definitions.png) | [PDF](04_model_behavior/zoomed_native_violins/luna/jrc_definitions.pdf) | [Original PNG](../chosen/05_zoomed_native_violins/luna/chosen_05_prompting_violins_zoomed_terminology_jrc_definitions.png)

## 05 Correlations

Only square correlation matrices are selected here, under `metrics/`, `languages/` and `models/`. Metric matrices compare score/prompting-change relationships across models. Language matrices correlate languages across the selected models; model matrices correlate models across supported languages. New language/model matrices cover COMET, chrF++, variant-aware coverage and term BERTScore recall, with separate From/To views and equal prompt averages. New terminology uses Luna LLM-enriched terms; the retained original metric matrices include all Luna term groups. [Language/model method and native vectors](../../story_luna_llm_enriched/figures/entity_correlations/README.md). Scatterplots, sensitivity maps, ranking/overlap and disagreement analyses remain outside Chosen in the [supplementary metric analysis](../../story_luna_llm_enriched/figures/metric_analysis/README.md).

Rebuild section 5: `uv run --no-sync python scripts/render_evaluation_results.py --story-correlations-only`.

### Dataset Correlations Zero Shot

Metric Correlations by Dataset | Zero-Shot. Dataset-specific comparisons of lexical, semantic, QE and terminology scores; new terminology analyses use Luna LLM-enriched annotations. Common-direction support; native scores and support details are exported.

[PNG](05_metric_analysis/metrics/dataset_correlations_zero_shot.png) | [PDF](05_metric_analysis/metrics/dataset_correlations_zero_shot.pdf) | [Original PNG](../../story_luna_llm_enriched/figures/metric_analysis/dataset_correlations_zero_shot.png)

### Dataset Correlations Few Shot

Metric Correlations by Dataset | Few-Shot. Dataset-specific comparisons of lexical, semantic, QE and terminology scores; new terminology analyses use Luna LLM-enriched annotations. Common-direction support; native scores and support details are exported.

[PNG](05_metric_analysis/metrics/dataset_correlations_few_shot.png) | [PDF](05_metric_analysis/metrics/dataset_correlations_few_shot.pdf) | [Original PNG](../../story_luna_llm_enriched/figures/metric_analysis/dataset_correlations_few_shot.png)

### Prompting Change Agreement

Do Metrics Agree About Prompting Changes?. Dataset-specific comparisons of lexical, semantic, QE and terminology scores; new terminology analyses use Luna LLM-enriched annotations. Common-direction support; native scores and support details are exported.

[PNG](05_metric_analysis/metrics/prompting_change_agreement.png) | [PDF](05_metric_analysis/metrics/prompting_change_agreement.pdf) | [Original PNG](../../story_luna_llm_enriched/figures/metric_analysis/prompting_change_agreement.png)

### Languages From Comet

Pearson/Spearman languages correlations for COMET, from-language profiles; datasets separate, both prompts averaged equally. Language matrices use model observations; model matrices use languages. Terminology uses Luna LLM-enriched annotations; support vectors exported.

[PNG](05_metric_analysis/languages/from_comet.png) | [PDF](05_metric_analysis/languages/from_comet.pdf) | [Original PNG](../../story_luna_llm_enriched/figures/entity_correlations/languages/from_comet.png)

### Languages From Chrf2++

Pearson/Spearman languages correlations for chrF++, from-language profiles; datasets separate, both prompts averaged equally. Language matrices use model observations; model matrices use languages. Terminology uses Luna LLM-enriched annotations; support vectors exported.

[PNG](05_metric_analysis/languages/from_chrf2++.png) | [PDF](05_metric_analysis/languages/from_chrf2++.pdf) | [Original PNG](../../story_luna_llm_enriched/figures/entity_correlations/languages/from_chrf2++.png)

### Languages From Variant Aware Target Term Coverage

Pearson/Spearman languages correlations for Variant-Aware Coverage, from-language profiles; datasets separate, both prompts averaged equally. Language matrices use model observations; model matrices use languages. Terminology uses Luna LLM-enriched annotations; support vectors exported.

[PNG](05_metric_analysis/languages/from_variant_aware_target_term_coverage.png) | [PDF](05_metric_analysis/languages/from_variant_aware_target_term_coverage.pdf) | [Original PNG](../../story_luna_llm_enriched/figures/entity_correlations/languages/from_variant_aware_target_term_coverage.png)

### Languages From Term Bertscore Recall

Pearson/Spearman languages correlations for Term BERTScore Recall, from-language profiles; datasets separate, both prompts averaged equally. Language matrices use model observations; model matrices use languages. Terminology uses Luna LLM-enriched annotations; support vectors exported.

[PNG](05_metric_analysis/languages/from_term_bertscore_recall.png) | [PDF](05_metric_analysis/languages/from_term_bertscore_recall.pdf) | [Original PNG](../../story_luna_llm_enriched/figures/entity_correlations/languages/from_term_bertscore_recall.png)

### Languages To Comet

Pearson/Spearman languages correlations for COMET, to-language profiles; datasets separate, both prompts averaged equally. Language matrices use model observations; model matrices use languages. Terminology uses Luna LLM-enriched annotations; support vectors exported.

[PNG](05_metric_analysis/languages/to_comet.png) | [PDF](05_metric_analysis/languages/to_comet.pdf) | [Original PNG](../../story_luna_llm_enriched/figures/entity_correlations/languages/to_comet.png)

### Languages To Chrf2++

Pearson/Spearman languages correlations for chrF++, to-language profiles; datasets separate, both prompts averaged equally. Language matrices use model observations; model matrices use languages. Terminology uses Luna LLM-enriched annotations; support vectors exported.

[PNG](05_metric_analysis/languages/to_chrf2++.png) | [PDF](05_metric_analysis/languages/to_chrf2++.pdf) | [Original PNG](../../story_luna_llm_enriched/figures/entity_correlations/languages/to_chrf2++.png)

### Languages To Variant Aware Target Term Coverage

Pearson/Spearman languages correlations for Variant-Aware Coverage, to-language profiles; datasets separate, both prompts averaged equally. Language matrices use model observations; model matrices use languages. Terminology uses Luna LLM-enriched annotations; support vectors exported.

[PNG](05_metric_analysis/languages/to_variant_aware_target_term_coverage.png) | [PDF](05_metric_analysis/languages/to_variant_aware_target_term_coverage.pdf) | [Original PNG](../../story_luna_llm_enriched/figures/entity_correlations/languages/to_variant_aware_target_term_coverage.png)

### Languages To Term Bertscore Recall

Pearson/Spearman languages correlations for Term BERTScore Recall, to-language profiles; datasets separate, both prompts averaged equally. Language matrices use model observations; model matrices use languages. Terminology uses Luna LLM-enriched annotations; support vectors exported.

[PNG](05_metric_analysis/languages/to_term_bertscore_recall.png) | [PDF](05_metric_analysis/languages/to_term_bertscore_recall.pdf) | [Original PNG](../../story_luna_llm_enriched/figures/entity_correlations/languages/to_term_bertscore_recall.png)

### Models From Comet

Pearson/Spearman models correlations for COMET, from-language profiles; datasets separate, both prompts averaged equally. Language matrices use model observations; model matrices use languages. Terminology uses Luna LLM-enriched annotations; support vectors exported.

[PNG](05_metric_analysis/models/from_comet.png) | [PDF](05_metric_analysis/models/from_comet.pdf) | [Original PNG](../../story_luna_llm_enriched/figures/entity_correlations/models/from_comet.png)

### Models From Chrf2++

Pearson/Spearman models correlations for chrF++, from-language profiles; datasets separate, both prompts averaged equally. Language matrices use model observations; model matrices use languages. Terminology uses Luna LLM-enriched annotations; support vectors exported.

[PNG](05_metric_analysis/models/from_chrf2++.png) | [PDF](05_metric_analysis/models/from_chrf2++.pdf) | [Original PNG](../../story_luna_llm_enriched/figures/entity_correlations/models/from_chrf2++.png)

### Models From Variant Aware Target Term Coverage

Pearson/Spearman models correlations for Variant-Aware Coverage, from-language profiles; datasets separate, both prompts averaged equally. Language matrices use model observations; model matrices use languages. Terminology uses Luna LLM-enriched annotations; support vectors exported.

[PNG](05_metric_analysis/models/from_variant_aware_target_term_coverage.png) | [PDF](05_metric_analysis/models/from_variant_aware_target_term_coverage.pdf) | [Original PNG](../../story_luna_llm_enriched/figures/entity_correlations/models/from_variant_aware_target_term_coverage.png)

### Models From Term Bertscore Recall

Pearson/Spearman models correlations for Term BERTScore Recall, from-language profiles; datasets separate, both prompts averaged equally. Language matrices use model observations; model matrices use languages. Terminology uses Luna LLM-enriched annotations; support vectors exported.

[PNG](05_metric_analysis/models/from_term_bertscore_recall.png) | [PDF](05_metric_analysis/models/from_term_bertscore_recall.pdf) | [Original PNG](../../story_luna_llm_enriched/figures/entity_correlations/models/from_term_bertscore_recall.png)

### Models To Comet

Pearson/Spearman models correlations for COMET, to-language profiles; datasets separate, both prompts averaged equally. Language matrices use model observations; model matrices use languages. Terminology uses Luna LLM-enriched annotations; support vectors exported.

[PNG](05_metric_analysis/models/to_comet.png) | [PDF](05_metric_analysis/models/to_comet.pdf) | [Original PNG](../../story_luna_llm_enriched/figures/entity_correlations/models/to_comet.png)

### Models To Chrf2++

Pearson/Spearman models correlations for chrF++, to-language profiles; datasets separate, both prompts averaged equally. Language matrices use model observations; model matrices use languages. Terminology uses Luna LLM-enriched annotations; support vectors exported.

[PNG](05_metric_analysis/models/to_chrf2++.png) | [PDF](05_metric_analysis/models/to_chrf2++.pdf) | [Original PNG](../../story_luna_llm_enriched/figures/entity_correlations/models/to_chrf2++.png)

### Models To Variant Aware Target Term Coverage

Pearson/Spearman models correlations for Variant-Aware Coverage, to-language profiles; datasets separate, both prompts averaged equally. Language matrices use model observations; model matrices use languages. Terminology uses Luna LLM-enriched annotations; support vectors exported.

[PNG](05_metric_analysis/models/to_variant_aware_target_term_coverage.png) | [PDF](05_metric_analysis/models/to_variant_aware_target_term_coverage.pdf) | [Original PNG](../../story_luna_llm_enriched/figures/entity_correlations/models/to_variant_aware_target_term_coverage.png)

### Models To Term Bertscore Recall

Pearson/Spearman models correlations for Term BERTScore Recall, to-language profiles; datasets separate, both prompts averaged equally. Language matrices use model observations; model matrices use languages. Terminology uses Luna LLM-enriched annotations; support vectors exported.

[PNG](05_metric_analysis/models/to_term_bertscore_recall.png) | [PDF](05_metric_analysis/models/to_term_bertscore_recall.pdf) | [Original PNG](../../story_luna_llm_enriched/figures/entity_correlations/models/to_term_bertscore_recall.png)

### Metrics Luna Zero Shot

Metric-to-metric Pearson and Spearman correlations, zero shot. All datasets weighted equally; seven model observations per metric pair. General metrics and all Luna terminology groups; exploratory, not significance tests.

[PNG](05_metric_analysis/metrics/metrics_luna_zero_shot.png) | [PDF](05_metric_analysis/metrics/metrics_luna_zero_shot.pdf) | [Original PNG](../correlations/luna/metric_correlations_all_datasets_zero_shot.png)

### Metrics Luna Few Shot

Metric-to-metric Pearson and Spearman correlations, few shot. All datasets weighted equally; seven model observations per metric pair. General metrics and all Luna terminology groups; exploratory, not significance tests.

[PNG](05_metric_analysis/metrics/metrics_luna_few_shot.png) | [PDF](05_metric_analysis/metrics/metrics_luna_few_shot.pdf) | [Original PNG](../correlations/luna/metric_correlations_all_datasets_few_shot.png)

