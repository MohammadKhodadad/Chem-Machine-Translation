# Balanced To-Language Rankings: Median Across Models

Rows rank languages, NOT models. From means translating out of a language; To means translating into it. For each metric/dataset/prompt, average supported partner-direction scores equally within each model. Then use the median across models as that language's native metric value. Top does not choose a different model for each direction. The best model may differ between metrics and strata.

Rank languages descending within each metric with average ties. Balance metrics within semantic and lexical families; balance terminology metrics within each term group and the selected groups equally. The three family ranks have equal one-third weights. Final ties share the minimum rank (1, 1, 3).

Overall rankings require every dataset, both prompts and every active metric for each language. Within that overall eligible language cohort, rerank each stratum's metric values, then average dataset/prompt family ranks equally. Displayed overall native cells are equal-stratum means, not pooled medians or global maxima. Dataset-specific cohorts may differ. All-NA metrics are omitted, never scored zero. Coverage CSV records excluded languages and missing components.

Partner populations can differ between languages. These are descriptive supported benchmark rankings, not matched-partner comparisons, intrinsic language difficulty or statistical significance. Original model scorecards are unchanged.

[Language ranks](language_ranks.csv) | [Metric ranks](metric_rank_components.csv) | [Native scores and model values](native_metric_scores.csv) | [Coverage](coverage.csv)

## Overall: all datasets and both prompts | luna

| Rank | Language | Mixed Mean Rank | Semantic | Lexical | Terminology |
| --- | --- | --- | --- | --- | --- |
| 1 | English | 1.924 | 2.633 | 1.583 | 1.556 |
| 2 | Spanish | 2.389 | 2.333 | 2.667 | 2.167 |
| 3 | French | 2.491 | 2.500 | 2.583 | 2.389 |
| 4 | German | 3.196 | 2.533 | 3.167 | 3.889 |

Scorecard: [PNG](../../figures/languages/rankings/median/to/luna/language_rankings_overall.png) | [PDF](../../figures/languages/rankings/median/to/luna/language_rankings_overall.pdf)

Unranked due to incomplete metric/dataset coverage: Japanese, Portuguese, Russian, Chinese.

## Chemical Patents | Few Shot | luna

| Rank | Language | Mixed Mean Rank | Semantic | Lexical | Terminology |
| --- | --- | --- | --- | --- | --- |
| 1 | Spanish | 2.794 | 2.800 | 3.250 | 2.333 |
| 2 | English | 2.994 | 4.400 | 2.250 | 2.333 |
| 3 | Russian | 3.289 | 2.200 | 3.000 | 4.667 |
| 4 | German | 3.722 | 4.000 | 2.500 | 4.667 |
| 5 | Chinese | 4.006 | 3.600 | 4.750 | 3.667 |
| 6 | French | 4.194 | 4.000 | 5.250 | 3.333 |

Scorecard: [PNG](../../figures/languages/rankings/median/to/luna/language_rankings_google_patents_few_shot.png) | [PDF](../../figures/languages/rankings/median/to/luna/language_rankings_google_patents_few_shot.pdf)

Unranked due to incomplete metric/dataset coverage: Japanese.

## Chemical Patents | Zero Shot | luna

| Rank | Language | Mixed Mean Rank | Semantic | Lexical | Terminology |
| --- | --- | --- | --- | --- | --- |
| 1 | Spanish | 2.628 | 2.800 | 2.750 | 2.333 |
| 2 | English | 3.178 | 4.200 | 3.000 | 2.333 |
| 3 | German | 3.389 | 4.000 | 1.500 | 4.667 |
| 4 | Russian | 3.689 | 2.400 | 4.000 | 4.667 |
| 5 | Chinese | 3.939 | 3.400 | 4.750 | 3.667 |
| 6 | French | 4.178 | 4.200 | 5.000 | 3.333 |

Scorecard: [PNG](../../figures/languages/rankings/median/to/luna/language_rankings_google_patents_zero_shot.png) | [PDF](../../figures/languages/rankings/median/to/luna/language_rankings_google_patents_zero_shot.pdf)

Unranked due to incomplete metric/dataset coverage: Japanese.

## JRC Articles | Few Shot | luna

| Rank | Language | Mixed Mean Rank | Semantic | Lexical | Terminology |
| --- | --- | --- | --- | --- | --- |
| 1 | English | 2.133 | 3.400 | 1.000 | 2.000 |
| 2 | Spanish | 2.339 | 2.600 | 2.750 | 1.667 |
| 3 | French | 3.344 | 3.200 | 2.500 | 4.333 |
| 4 | Portuguese | 3.356 | 3.400 | 4.000 | 2.667 |
| 5 | German | 3.828 | 2.400 | 4.750 | 4.333 |

Scorecard: [PNG](../../figures/languages/rankings/median/to/luna/language_rankings_jrc_articles_few_shot.png) | [PDF](../../figures/languages/rankings/median/to/luna/language_rankings_jrc_articles_few_shot.pdf)

## JRC Articles | Zero Shot | luna

| Rank | Language | Mixed Mean Rank | Semantic | Lexical | Terminology |
| --- | --- | --- | --- | --- | --- |
| 1 | English | 1.600 | 2.800 | 1.000 | 1.000 |
| 2 | Spanish | 2.561 | 2.600 | 2.750 | 2.333 |
| 3 | French | 2.750 | 3.000 | 2.250 | 3.000 |
| 4 | German | 4.011 | 3.200 | 4.500 | 4.333 |
| 5 | Portuguese | 4.078 | 3.400 | 4.500 | 4.333 |

Scorecard: [PNG](../../figures/languages/rankings/median/to/luna/language_rankings_jrc_articles_zero_shot.png) | [PDF](../../figures/languages/rankings/median/to/luna/language_rankings_jrc_articles_zero_shot.pdf)

## JRC Definitions | Few Shot | luna

| Rank | Language | Mixed Mean Rank | Semantic | Lexical | Terminology |
| --- | --- | --- | --- | --- | --- |
| 1 | French | 1.400 | 2.200 | 1.000 | 1.000 |
| 2 | English | 2.661 | 3.400 | 2.250 | 2.333 |
| 3 | Spanish | 2.972 | 3.000 | 3.250 | 2.667 |
| 4 | Portuguese | 3.567 | 3.200 | 3.500 | 4.000 |
| 5 | German | 4.400 | 3.200 | 5.000 | 5.000 |

Scorecard: [PNG](../../figures/languages/rankings/median/to/luna/language_rankings_jrc_definitions_few_shot.png) | [PDF](../../figures/languages/rankings/median/to/luna/language_rankings_jrc_definitions_few_shot.pdf)

## JRC Definitions | Zero Shot | luna

| Rank | Language | Mixed Mean Rank | Semantic | Lexical | Terminology |
| --- | --- | --- | --- | --- | --- |
| 1 | English | 1.833 | 3.000 | 1.500 | 1.000 |
| 2 | French | 1.917 | 2.000 | 1.750 | 2.000 |
| 3 | Spanish | 3.217 | 3.400 | 3.250 | 3.000 |
| 4 | Portuguese | 3.633 | 3.400 | 3.500 | 4.000 |
| 5 | German | 4.400 | 3.200 | 5.000 | 5.000 |

Scorecard: [PNG](../../figures/languages/rankings/median/to/luna/language_rankings_jrc_definitions_zero_shot.png) | [PDF](../../figures/languages/rankings/median/to/luna/language_rankings_jrc_definitions_zero_shot.pdf)

