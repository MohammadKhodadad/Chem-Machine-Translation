# Balanced From-Language Rankings: Median Across Models

Rows rank languages, NOT models. From means translating out of a language; To means translating into it. For each metric/dataset/prompt, average supported partner-direction scores equally within each model. Then use the median across models as that language's native metric value. Top does not choose a different model for each direction. The best model may differ between metrics and strata.

Rank languages descending within each metric with average ties. Balance metrics within semantic and lexical families; balance terminology metrics within each term group and the three groups equally. The three family ranks have equal one-third weights. Final ties share the minimum rank (1, 1, 3).

Overall rankings require every dataset, both prompts and every active metric for each language. Within that overall eligible language cohort, rerank each stratum's metric values, then average dataset/prompt family ranks equally. Displayed overall native cells are equal-stratum means, not pooled medians or global maxima. Dataset-specific cohorts may differ. All-NA metrics are omitted, never scored zero. Coverage CSV records excluded languages and missing components.

Partner populations can differ between languages. These are descriptive supported benchmark rankings, not matched-partner comparisons, intrinsic language difficulty or statistical significance. Original model scorecards are unchanged.

[Language ranks](language_ranks.csv) | [Metric ranks](metric_rank_components.csv) | [Native scores and model values](native_metric_scores.csv) | [Coverage](coverage.csv)

## Overall: all datasets and both prompts | luna

| Rank | Language | Mixed Mean Rank | Semantic | Lexical | Terminology |
| --- | --- | --- | --- | --- | --- |
| 1 | French | 1.833 | 1.800 | 1.792 | 1.907 |
| 2 | Spanish | 2.147 | 2.333 | 2.292 | 1.815 |
| 3 | English | 2.623 | 2.133 | 2.792 | 2.944 |
| 4 | German | 3.397 | 3.733 | 3.125 | 3.333 |

Scorecard: [PNG](../../figures/languages/rankings/median/from/luna/language_rankings_overall.png) | [PDF](../../figures/languages/rankings/median/from/luna/language_rankings_overall.pdf)

Unranked due to incomplete metric/dataset coverage: Japanese, Portuguese, Russian, Chinese.

## Overall: all datasets and both prompts | original_glm

| Rank | Language | Mixed Mean Rank | Semantic | Lexical | Terminology |
| --- | --- | --- | --- | --- | --- |
| 1 | French | 1.433 | 1.467 | 1.500 | 1.333 |
| 2 | English | 1.902 | 1.700 | 2.042 | 1.963 |
| 3 | German | 2.665 | 2.833 | 2.458 | 2.704 |

Scorecard: [PNG](../../figures/languages/rankings/median/from/original_glm/language_rankings_overall.png) | [PDF](../../figures/languages/rankings/median/from/original_glm/language_rankings_overall.pdf)

Unranked due to incomplete metric/dataset coverage: Spanish, Japanese, Portuguese, Russian, Chinese.

## Chemical Patents | Few Shot | luna

| Rank | Language | Mixed Mean Rank | Semantic | Lexical | Terminology |
| --- | --- | --- | --- | --- | --- |
| 1 | Spanish | 2.293 | 2.600 | 2.500 | 1.778 |
| 2 | French | 2.715 | 1.200 | 4.500 | 2.444 |
| 3 | German | 2.826 | 4.200 | 1.500 | 2.778 |
| 4 | English | 3.915 | 2.800 | 4.500 | 4.444 |
| 5 | Russian | 4.459 | 4.600 | 4.000 | 4.778 |
| 6 | Chinese | 4.793 | 5.600 | 4.000 | 4.778 |

Scorecard: [PNG](../../figures/languages/rankings/median/from/luna/language_rankings_google_patents_few_shot.png) | [PDF](../../figures/languages/rankings/median/from/luna/language_rankings_google_patents_few_shot.pdf)

Unranked due to incomplete metric/dataset coverage: Japanese.

## Chemical Patents | Zero Shot | luna

| Rank | Language | Mixed Mean Rank | Semantic | Lexical | Terminology |
| --- | --- | --- | --- | --- | --- |
| 1 | Spanish | 2.330 | 2.600 | 2.500 | 1.889 |
| 2 | German | 2.639 | 4.000 | 1.250 | 2.667 |
| 3 | French | 2.985 | 1.400 | 5.000 | 2.556 |
| 4 | English | 3.609 | 2.800 | 4.250 | 3.778 |
| 5 | Russian | 4.348 | 4.600 | 4.000 | 4.444 |
| 6 | Chinese | 5.089 | 5.600 | 4.000 | 5.667 |

Scorecard: [PNG](../../figures/languages/rankings/median/from/luna/language_rankings_google_patents_zero_shot.png) | [PDF](../../figures/languages/rankings/median/from/luna/language_rankings_google_patents_zero_shot.pdf)

Unranked due to incomplete metric/dataset coverage: Japanese.

## JRC Articles | Few Shot | luna

| Rank | Language | Mixed Mean Rank | Semantic | Lexical | Terminology |
| --- | --- | --- | --- | --- | --- |
| 1 | Portuguese | 1.893 | 2.400 | 1.500 | 1.778 |
| 2 | English | 2.585 | 2.200 | 3.000 | 2.556 |
| 3 | French | 2.739 | 2.800 | 1.750 | 3.667 |
| 4 | Spanish | 3.043 | 2.600 | 3.750 | 2.778 |
| 5 | German | 4.741 | 5.000 | 5.000 | 4.222 |

Scorecard: [PNG](../../figures/languages/rankings/median/from/luna/language_rankings_jrc_articles_few_shot.png) | [PDF](../../figures/languages/rankings/median/from/luna/language_rankings_jrc_articles_few_shot.pdf)

## JRC Articles | Zero Shot | luna

| Rank | Language | Mixed Mean Rank | Semantic | Lexical | Terminology |
| --- | --- | --- | --- | --- | --- |
| 1 | Portuguese | 1.972 | 3.000 | 1.250 | 1.667 |
| 2 | French | 2.035 | 2.800 | 1.750 | 1.556 |
| 3 | Spanish | 2.787 | 2.000 | 3.250 | 3.111 |
| 4 | English | 3.272 | 2.400 | 3.750 | 3.667 |
| 5 | German | 4.933 | 4.800 | 5.000 | 5.000 |

Scorecard: [PNG](../../figures/languages/rankings/median/from/luna/language_rankings_jrc_articles_zero_shot.png) | [PDF](../../figures/languages/rankings/median/from/luna/language_rankings_jrc_articles_zero_shot.pdf)

## JRC Definitions | Few Shot | luna

| Rank | Language | Mixed Mean Rank | Semantic | Lexical | Terminology |
| --- | --- | --- | --- | --- | --- |
| 1 | Portuguese | 1.357 | 1.600 | 1.250 | 1.222 |
| 2 | French | 2.585 | 3.200 | 2.000 | 2.556 |
| 3 | Spanish | 2.791 | 3.400 | 2.750 | 2.222 |
| 4 | English | 3.400 | 2.200 | 4.000 | 4.000 |
| 5 | German | 4.867 | 4.600 | 5.000 | 5.000 |

Scorecard: [PNG](../../figures/languages/rankings/median/from/luna/language_rankings_jrc_definitions_few_shot.png) | [PDF](../../figures/languages/rankings/median/from/luna/language_rankings_jrc_definitions_few_shot.pdf)

## JRC Definitions | Zero Shot | luna

| Rank | Language | Mixed Mean Rank | Semantic | Lexical | Terminology |
| --- | --- | --- | --- | --- | --- |
| 1 | Portuguese | 1.478 | 1.600 | 1.500 | 1.333 |
| 2 | French | 1.967 | 2.400 | 1.500 | 2.000 |
| 3 | Spanish | 3.022 | 3.400 | 3.000 | 2.667 |
| 4 | English | 3.533 | 2.600 | 4.000 | 4.000 |
| 5 | German | 5.000 | 5.000 | 5.000 | 5.000 |

Scorecard: [PNG](../../figures/languages/rankings/median/from/luna/language_rankings_jrc_definitions_zero_shot.png) | [PDF](../../figures/languages/rankings/median/from/luna/language_rankings_jrc_definitions_zero_shot.pdf)

## Chemical Patents | Few Shot | original_glm

| Rank | Language | Mixed Mean Rank | Semantic | Lexical | Terminology |
| --- | --- | --- | --- | --- | --- |
| 1 | French | 1.778 | 1.000 | 3.000 | 1.333 |
| 2 | German | 2.463 | 3.000 | 1.500 | 2.889 |
| 3 | English | 2.585 | 2.200 | 3.000 | 2.556 |
| 4 | Chinese | 3.174 | 3.800 | 2.500 | 3.222 |

Scorecard: [PNG](../../figures/languages/rankings/median/from/original_glm/language_rankings_google_patents_few_shot.png) | [PDF](../../figures/languages/rankings/median/from/original_glm/language_rankings_google_patents_few_shot.pdf)

Unranked due to incomplete metric/dataset coverage: Spanish, Japanese, Russian.

## Chemical Patents | Zero Shot | original_glm

| Rank | Language | Mixed Mean Rank | Semantic | Lexical | Terminology |
| --- | --- | --- | --- | --- | --- |
| 1 | French | 2.011 | 1.200 | 3.500 | 1.333 |
| 2 | German | 2.313 | 2.800 | 1.250 | 2.889 |
| 3 | English | 2.502 | 2.200 | 2.750 | 2.556 |
| 4 | Chinese | 3.174 | 3.800 | 2.500 | 3.222 |

Scorecard: [PNG](../../figures/languages/rankings/median/from/original_glm/language_rankings_google_patents_zero_shot.png) | [PDF](../../figures/languages/rankings/median/from/original_glm/language_rankings_google_patents_zero_shot.pdf)

Unranked due to incomplete metric/dataset coverage: Spanish, Japanese, Russian.

## JRC Articles | Few Shot | original_glm

| Rank | Language | Mixed Mean Rank | Semantic | Lexical | Terminology |
| --- | --- | --- | --- | --- | --- |
| 1 | Portuguese | 1.781 | 2.400 | 1.500 | 1.444 |
| 2 | English | 2.400 | 2.200 | 3.000 | 2.000 |
| 3 | French | 2.924 | 2.800 | 1.750 | 4.222 |
| 4 | Spanish | 3.228 | 2.600 | 3.750 | 3.333 |
| 5 | German | 4.667 | 5.000 | 5.000 | 4.000 |

Scorecard: [PNG](../../figures/languages/rankings/median/from/original_glm/language_rankings_jrc_articles_few_shot.png) | [PDF](../../figures/languages/rankings/median/from/original_glm/language_rankings_jrc_articles_few_shot.pdf)

## JRC Articles | Zero Shot | original_glm

| Rank | Language | Mixed Mean Rank | Semantic | Lexical | Terminology |
| --- | --- | --- | --- | --- | --- |
| 1 | Portuguese | 1.898 | 3.000 | 1.250 | 1.444 |
| 2 | French | 2.109 | 2.800 | 1.750 | 1.778 |
| 3 | Spanish | 2.713 | 2.000 | 3.250 | 2.889 |
| 4 | English | 3.457 | 2.400 | 3.750 | 4.222 |
| 5 | German | 4.822 | 4.800 | 5.000 | 4.667 |

Scorecard: [PNG](../../figures/languages/rankings/median/from/original_glm/language_rankings_jrc_articles_zero_shot.png) | [PDF](../../figures/languages/rankings/median/from/original_glm/language_rankings_jrc_articles_zero_shot.pdf)

## JRC Definitions | Few Shot | original_glm

| Rank | Language | Mixed Mean Rank | Semantic | Lexical | Terminology |
| --- | --- | --- | --- | --- | --- |
| 1 | Portuguese | 1.320 | 1.600 | 1.250 | 1.111 |
| 2 | French | 2.622 | 3.200 | 2.000 | 2.667 |
| 3 | Spanish | 2.791 | 3.400 | 2.750 | 2.222 |
| 4 | English | 3.400 | 2.200 | 4.000 | 4.000 |
| 5 | German | 4.867 | 4.600 | 5.000 | 5.000 |

Scorecard: [PNG](../../figures/languages/rankings/median/from/original_glm/language_rankings_jrc_definitions_few_shot.png) | [PDF](../../figures/languages/rankings/median/from/original_glm/language_rankings_jrc_definitions_few_shot.pdf)

## JRC Definitions | Zero Shot | original_glm

| Rank | Language | Mixed Mean Rank | Semantic | Lexical | Terminology |
| --- | --- | --- | --- | --- | --- |
| 1 | Portuguese | 1.404 | 1.600 | 1.500 | 1.111 |
| 2 | French | 2.078 | 2.400 | 1.500 | 2.333 |
| 3 | Spanish | 3.022 | 3.400 | 3.000 | 2.667 |
| 4 | English | 3.496 | 2.600 | 4.000 | 3.889 |
| 5 | German | 5.000 | 5.000 | 5.000 | 5.000 |

Scorecard: [PNG](../../figures/languages/rankings/median/from/original_glm/language_rankings_jrc_definitions_zero_shot.png) | [PDF](../../figures/languages/rankings/median/from/original_glm/language_rankings_jrc_definitions_zero_shot.pdf)

