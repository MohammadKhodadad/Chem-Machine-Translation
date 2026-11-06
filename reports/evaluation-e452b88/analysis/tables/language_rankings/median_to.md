# Balanced To-Language Rankings: Median Across Models

Rows rank languages, NOT models. From means translating out of a language; To means translating into it. For each metric/dataset/prompt, average supported partner-direction scores equally within each model. Then use the median across models as that language's native metric value. Top does not choose a different model for each direction. The best model may differ between metrics and strata.

Rank languages descending within each metric with average ties. Balance metrics within semantic and lexical families; balance terminology metrics within each term group and the three groups equally. The three family ranks have equal one-third weights. Final ties share the minimum rank (1, 1, 3).

Overall rankings require every dataset, both prompts and every active metric for each language. Within that overall eligible language cohort, rerank each stratum's metric values, then average dataset/prompt family ranks equally. Displayed overall native cells are equal-stratum means, not pooled medians or global maxima. Dataset-specific cohorts may differ. All-NA metrics are omitted, never scored zero. Coverage CSV records excluded languages and missing components.

Partner populations can differ between languages. These are descriptive supported benchmark rankings, not matched-partner comparisons, intrinsic language difficulty or statistical significance. Original model scorecards are unchanged.

[Language ranks](language_ranks.csv) | [Metric ranks](metric_rank_components.csv) | [Native scores and model values](native_metric_scores.csv) | [Coverage](coverage.csv)

## Overall: all datasets and both prompts | luna

| Rank | Language | Mixed Mean Rank | Semantic | Lexical | Terminology |
| --- | --- | --- | --- | --- | --- |
| 1 | English | 1.936 | 2.633 | 1.583 | 1.593 |
| 2 | Spanish | 2.451 | 2.333 | 2.667 | 2.352 |
| 3 | French | 2.540 | 2.500 | 2.583 | 2.537 |
| 4 | German | 3.073 | 2.533 | 3.167 | 3.519 |

Scorecard: [PNG](../../figures/languages/rankings/median/to/luna/language_rankings_overall.png) | [PDF](../../figures/languages/rankings/median/to/luna/language_rankings_overall.pdf)

Unranked due to incomplete metric/dataset coverage: Japanese, Portuguese, Russian, Chinese.

## Overall: all datasets and both prompts | original_glm

| Rank | Language | Mixed Mean Rank | Semantic | Lexical | Terminology |
| --- | --- | --- | --- | --- | --- |
| 1 | Spanish | 1.707 | 1.867 | 1.792 | 1.463 |
| 2 | French | 1.927 | 2.100 | 1.792 | 1.889 |
| 3 | German | 2.366 | 2.033 | 2.417 | 2.648 |

Scorecard: [PNG](../../figures/languages/rankings/median/to/original_glm/language_rankings_overall.png) | [PDF](../../figures/languages/rankings/median/to/original_glm/language_rankings_overall.pdf)

Unranked due to incomplete metric/dataset coverage: English, Japanese, Portuguese, Russian, Chinese.

## Chemical Patents | Few Shot | luna

| Rank | Language | Mixed Mean Rank | Semantic | Lexical | Terminology |
| --- | --- | --- | --- | --- | --- |
| 1 | Spanish | 2.757 | 2.800 | 3.250 | 2.222 |
| 2 | English | 3.069 | 4.400 | 2.250 | 2.556 |
| 3 | Russian | 3.289 | 2.200 | 3.000 | 4.667 |
| 4 | German | 3.500 | 4.000 | 2.500 | 4.000 |
| 5 | Chinese | 4.080 | 3.600 | 4.750 | 3.889 |
| 6 | French | 4.306 | 4.000 | 5.250 | 3.667 |

Scorecard: [PNG](../../figures/languages/rankings/median/to/luna/language_rankings_google_patents_few_shot.png) | [PDF](../../figures/languages/rankings/median/to/luna/language_rankings_google_patents_few_shot.pdf)

Unranked due to incomplete metric/dataset coverage: Japanese.

## Chemical Patents | Zero Shot | luna

| Rank | Language | Mixed Mean Rank | Semantic | Lexical | Terminology |
| --- | --- | --- | --- | --- | --- |
| 1 | Spanish | 2.628 | 2.800 | 2.750 | 2.333 |
| 2 | German | 3.204 | 4.000 | 1.500 | 4.111 |
| 3 | English | 3.252 | 4.200 | 3.000 | 2.556 |
| 4 | Russian | 3.652 | 2.400 | 4.000 | 4.556 |
| 5 | Chinese | 3.976 | 3.400 | 4.750 | 3.778 |
| 6 | French | 4.289 | 4.200 | 5.000 | 3.667 |

Scorecard: [PNG](../../figures/languages/rankings/median/to/luna/language_rankings_google_patents_zero_shot.png) | [PDF](../../figures/languages/rankings/median/to/luna/language_rankings_google_patents_zero_shot.pdf)

Unranked due to incomplete metric/dataset coverage: Japanese.

## JRC Articles | Few Shot | luna

| Rank | Language | Mixed Mean Rank | Semantic | Lexical | Terminology |
| --- | --- | --- | --- | --- | --- |
| 1 | English | 2.022 | 3.400 | 1.000 | 1.667 |
| 2 | Spanish | 2.598 | 2.600 | 2.750 | 2.444 |
| 3 | French | 2.974 | 3.200 | 2.500 | 3.222 |
| 4 | Portuguese | 3.615 | 3.400 | 4.000 | 3.444 |
| 5 | German | 3.791 | 2.400 | 4.750 | 4.222 |

Scorecard: [PNG](../../figures/languages/rankings/median/to/luna/language_rankings_jrc_articles_few_shot.png) | [PDF](../../figures/languages/rankings/median/to/luna/language_rankings_jrc_articles_few_shot.pdf)

## JRC Articles | Zero Shot | luna

| Rank | Language | Mixed Mean Rank | Semantic | Lexical | Terminology |
| --- | --- | --- | --- | --- | --- |
| 1 | English | 1.637 | 2.800 | 1.000 | 1.111 |
| 2 | Spanish | 2.635 | 2.600 | 2.750 | 2.556 |
| 3 | French | 2.676 | 3.000 | 2.250 | 2.778 |
| 4 | German | 3.974 | 3.200 | 4.500 | 4.222 |
| 5 | Portuguese | 4.078 | 3.400 | 4.500 | 4.333 |

Scorecard: [PNG](../../figures/languages/rankings/median/to/luna/language_rankings_jrc_articles_zero_shot.png) | [PDF](../../figures/languages/rankings/median/to/luna/language_rankings_jrc_articles_zero_shot.pdf)

## JRC Definitions | Few Shot | luna

| Rank | Language | Mixed Mean Rank | Semantic | Lexical | Terminology |
| --- | --- | --- | --- | --- | --- |
| 1 | French | 1.659 | 2.200 | 1.000 | 1.778 |
| 2 | English | 2.550 | 3.400 | 2.250 | 2.000 |
| 3 | Spanish | 3.194 | 3.000 | 3.250 | 3.333 |
| 4 | Portuguese | 3.344 | 3.200 | 3.500 | 3.333 |
| 5 | German | 4.252 | 3.200 | 5.000 | 4.556 |

Scorecard: [PNG](../../figures/languages/rankings/median/to/luna/language_rankings_jrc_definitions_few_shot.png) | [PDF](../../figures/languages/rankings/median/to/luna/language_rankings_jrc_definitions_few_shot.pdf)

## JRC Definitions | Zero Shot | luna

| Rank | Language | Mixed Mean Rank | Semantic | Lexical | Terminology |
| --- | --- | --- | --- | --- | --- |
| 1 | English | 1.907 | 3.000 | 1.500 | 1.222 |
| 2 | French | 2.065 | 2.000 | 1.750 | 2.444 |
| 3 | Spanish | 3.365 | 3.400 | 3.250 | 3.444 |
| 4 | Portuguese | 3.411 | 3.400 | 3.500 | 3.333 |
| 5 | German | 4.252 | 3.200 | 5.000 | 4.556 |

Scorecard: [PNG](../../figures/languages/rankings/median/to/luna/language_rankings_jrc_definitions_zero_shot.png) | [PDF](../../figures/languages/rankings/median/to/luna/language_rankings_jrc_definitions_zero_shot.pdf)

## Chemical Patents | Few Shot | original_glm

| Rank | Language | Mixed Mean Rank | Semantic | Lexical | Terminology |
| --- | --- | --- | --- | --- | --- |
| 1 | Spanish | 2.546 | 3.000 | 2.750 | 1.889 |
| 2 | Russian | 2.959 | 2.600 | 2.500 | 3.778 |
| 3 | German | 3.446 | 4.200 | 2.250 | 3.889 |
| 4 | Japanese | 3.502 | 3.200 | 4.750 | 2.556 |
| 5 | Chinese | 4.165 | 3.800 | 4.250 | 4.444 |
| 6 | French | 4.381 | 4.200 | 4.500 | 4.444 |

Scorecard: [PNG](../../figures/languages/rankings/median/to/original_glm/language_rankings_google_patents_few_shot.png) | [PDF](../../figures/languages/rankings/median/to/original_glm/language_rankings_google_patents_few_shot.pdf)

Unranked due to incomplete metric/dataset coverage: English.

## Chemical Patents | Zero Shot | original_glm

| Rank | Language | Mixed Mean Rank | Semantic | Lexical | Terminology |
| --- | --- | --- | --- | --- | --- |
| 1 | Spanish | 2.463 | 3.000 | 2.500 | 1.889 |
| 2 | German | 3.056 | 4.000 | 1.500 | 3.667 |
| 3 | Russian | 3.404 | 2.600 | 3.500 | 4.111 |
| 4 | Japanese | 3.809 | 3.400 | 5.250 | 2.778 |
| 5 | Chinese | 3.904 | 3.600 | 4.000 | 4.111 |
| 6 | French | 4.365 | 4.400 | 4.250 | 4.444 |

Scorecard: [PNG](../../figures/languages/rankings/median/to/original_glm/language_rankings_google_patents_zero_shot.png) | [PDF](../../figures/languages/rankings/median/to/original_glm/language_rankings_google_patents_zero_shot.pdf)

Unranked due to incomplete metric/dataset coverage: English.

## JRC Articles | Few Shot | original_glm

| Rank | Language | Mixed Mean Rank | Semantic | Lexical | Terminology |
| --- | --- | --- | --- | --- | --- |
| 1 | English | 1.911 | 3.400 | 1.000 | 1.333 |
| 2 | Spanish | 2.598 | 2.600 | 2.750 | 2.444 |
| 3 | French | 2.974 | 3.200 | 2.500 | 3.222 |
| 4 | Portuguese | 3.652 | 3.400 | 4.000 | 3.556 |
| 5 | German | 3.865 | 2.400 | 4.750 | 4.444 |

Scorecard: [PNG](../../figures/languages/rankings/median/to/original_glm/language_rankings_jrc_articles_few_shot.png) | [PDF](../../figures/languages/rankings/median/to/original_glm/language_rankings_jrc_articles_few_shot.pdf)

## JRC Articles | Zero Shot | original_glm

| Rank | Language | Mixed Mean Rank | Semantic | Lexical | Terminology |
| --- | --- | --- | --- | --- | --- |
| 1 | English | 1.674 | 2.800 | 1.000 | 1.222 |
| 2 | Spanish | 2.487 | 2.600 | 2.750 | 2.111 |
| 3 | French | 2.861 | 3.000 | 2.250 | 3.333 |
| 4 | Portuguese | 3.893 | 3.400 | 4.500 | 3.778 |
| 5 | German | 4.085 | 3.200 | 4.500 | 4.556 |

Scorecard: [PNG](../../figures/languages/rankings/median/to/original_glm/language_rankings_jrc_articles_zero_shot.png) | [PDF](../../figures/languages/rankings/median/to/original_glm/language_rankings_jrc_articles_zero_shot.pdf)

## JRC Definitions | Few Shot | original_glm

| Rank | Language | Mixed Mean Rank | Semantic | Lexical | Terminology |
| --- | --- | --- | --- | --- | --- |
| 1 | French | 1.511 | 2.200 | 1.000 | 1.333 |
| 2 | English | 2.550 | 3.400 | 2.250 | 2.000 |
| 3 | Spanish | 3.269 | 3.000 | 3.250 | 3.556 |
| 4 | Portuguese | 3.307 | 3.200 | 3.500 | 3.222 |
| 5 | German | 4.363 | 3.200 | 5.000 | 4.889 |

Scorecard: [PNG](../../figures/languages/rankings/median/to/original_glm/language_rankings_jrc_definitions_few_shot.png) | [PDF](../../figures/languages/rankings/median/to/original_glm/language_rankings_jrc_definitions_few_shot.pdf)

## JRC Definitions | Zero Shot | original_glm

| Rank | Language | Mixed Mean Rank | Semantic | Lexical | Terminology |
| --- | --- | --- | --- | --- | --- |
| 1 | French | 1.917 | 2.000 | 1.750 | 2.000 |
| 2 | English | 1.981 | 3.000 | 1.500 | 1.444 |
| 3 | Spanish | 3.291 | 3.400 | 3.250 | 3.222 |
| 4 | Portuguese | 3.485 | 3.400 | 3.500 | 3.556 |
| 5 | German | 4.326 | 3.200 | 5.000 | 4.778 |

Scorecard: [PNG](../../figures/languages/rankings/median/to/original_glm/language_rankings_jrc_definitions_zero_shot.png) | [PDF](../../figures/languages/rankings/median/to/original_glm/language_rankings_jrc_definitions_zero_shot.pdf)

